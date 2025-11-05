import os
import signal
from collections import defaultdict
from dataclasses import asdict
from flask import Flask, request, jsonify, g
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from prometheus_client import Counter, Histogram, Gauge, generate_latest

from .logging_utils import setup_logging
from .config import Config, ChatConfig
from .http_pool import HTTPConnectionPool
from .templates_manager import TemplateManager
from .filters import AlertFilter
from .gapo import send_to_gapo_with_retry
from .message import create_message
from .queue import AlertQueue
from .security import require_token, validate_webhook_signature, require_admin_mfa, _ip_in_whitelist
from .schemas import AlertmanagerWebhookSchema
from .healthcheck import HealthChecker


def create_app() -> Flask:
    logger = setup_logging()
    cfg = Config()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = cfg.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = cfg.MAX_CONTENT_LENGTH
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 300})
    limiter = Limiter(app=app, key_func=get_remote_address, default_limits=[cfg.RATE_LIMIT], storage_uri=cfg.LIMITER_STORAGE)

    metrics = {
        'alerts_received': Counter('alerts_received_total', 'Total alerts received', ['status', 'routing_label']),
        'alerts_filtered': Counter('alerts_filtered_total', 'Total alerts filtered out', ['reason']),
        'messages_sent': Counter('messages_sent_total', 'Total messages sent to Gapo', ['routing_label', 'status']),
        'processing_time': Histogram('alert_processing_duration_seconds', 'Time to process alerts'),
        'queue_size': Gauge('alert_queue_size', 'Current size of alert queue'),
        'active_workers': Gauge('active_worker_threads', 'Number of active worker threads'),
    }

    http_pool = HTTPConnectionPool()
    template_manager = TemplateManager()
    alert_filter = AlertFilter(cfg)
    health_checker = HealthChecker(cfg, http_pool, logger, metrics, None)

    def process_alert_item(item):
        try:
            if not g.get('request_id'):
                g.request_id = item.get('request_id', 'worker-thread')
            send_to_gapo_with_retry(
                item['message'], item['config'], item['routing_value'], cfg, http_pool, logger, metrics, request_id=item.get('request_id', 'worker-thread')
            )
        except Exception as e:
            logger.error(f"Failed to process alert: {e}")
            metrics['messages_sent'].labels(routing_label=item['routing_value'], status='failed').inc()

    alert_queue = AlertQueue(app, logger, metrics, cfg, process_alert_item)
    # inject alert_queue into health_checker now that it's created
    health_checker.alert_queue = alert_queue

    @app.before_request
    def assign_request_id():
        g.request_id = request.headers.get('X-Request-ID') or os.urandom(8).hex()

    @app.route(cfg.ALERTMANAGER_ENDPOINT, methods=['POST'])
    @require_token(cfg, logger, metrics)
    @validate_webhook_signature()
    def alertmanager_webhook():
        remote_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        if not _ip_in_whitelist(remote_ip, cfg.WEBHOOK_IP_WHITELIST):
            logger.warning(f"Blocked IP {remote_ip} not in whitelist")
            metrics['alerts_filtered'].labels(reason='ip_not_whitelisted').inc()
            return jsonify({"error": "IP not allowed"}), 403
        try:
            schema = AlertmanagerWebhookSchema()
            try:
                data = schema.load(request.get_json(force=True, silent=True) or {}, unknown=None)
            except Exception as e:
                return jsonify({"error": "Invalid payload", "details": str(e)}), 400
            alerts = data['alerts']
            alerts_by_routing = defaultdict(lambda: {'firing': [], 'resolved': []})
            for alert in alerts:
                if cfg.LOG_ALERT_DETAILS:
                    al = alert
                    logger.info(
                        "Alert detail: status=%s name=%s ns=%s svc=%s job=%s instance=%s sev=%s start=%s end=%s",
                        al.get('status'), al.get('labels', {}).get('alertname'), al.get('labels', {}).get('namespace'),
                        al.get('labels', {}).get('service'), al.get('labels', {}).get('job'), al.get('labels', {}).get('instance'),
                        al.get('labels', {}).get('severity'), al.get('startsAt'), al.get('endsAt'),
                    )
                should_ignore, reason = alert_filter.is_ignored(alert)
                if should_ignore:
                    logger.debug(f"Ignoring alert {alert.get('labels', {}).get('alertname')} - {reason}")
                    metrics['alerts_filtered'].labels(reason=reason).inc()
                    continue
                routing_value = alert.get('labels', {}).get(cfg.ROUTING_LABEL, 'unknown')
                status = alert.get('status', 'firing')
                alerts_by_routing[routing_value][status].append(alert)
                metrics['alerts_received'].labels(status=status, routing_label=routing_value).inc()
            messages_queued = 0
            for routing_value, alerts_dict in alerts_by_routing.items():
                firing_alerts = alerts_dict['firing']
                resolved_alerts = alerts_dict['resolved']
                if not firing_alerts and not resolved_alerts:
                    continue
                chat_config = cfg.ROUTING_CONFIG.get(routing_value, cfg.DEFAULT_CHAT_CONFIG)
                message = create_message(cfg, template_manager, routing_value, firing_alerts, resolved_alerts)
                queued = alert_queue.add({
                    'message': message,
                    'config': chat_config,
                    'routing_value': routing_value,
                    'request_id': g.request_id,
                })
                if queued:
                    messages_queued += 1
                    logger.info(f"Queued alert for {routing_value}: {len(firing_alerts)} firing, {len(resolved_alerts)} resolved")
            return jsonify({"status": "success", "messages_queued": messages_queued, "request_id": g.request_id}), 200
        except Exception as e:
            logger.exception(f"Error processing webhook: {e}")
            return jsonify({"error": "Internal server error", "request_id": g.request_id}), 500

    @app.route('/health', methods=['GET'])
    @cache.cached(timeout=10)
    def health_check():
        health_status = {
            "status": "healthy",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "queue_size": alert_queue.queue.qsize(),
            "active_workers": len([w for w in alert_queue.workers if w.is_alive()]),
            "configuration": {
                "routing_label": cfg.ROUTING_LABEL,
                "configured_values": list(cfg.ROUTING_CONFIG.keys()),
                "allowed_values": list(cfg.ALLOWED_VALUES),
            },
            "healthchecks": {
                "urls": cfg.HEALTHCHECK_URLS,
                "interval": cfg.HEALTHCHECK_INTERVAL,
                "status": health_checker.status,
            },
        }
        if health_status['active_workers'] < cfg.WORKER_THREADS:
            health_status['status'] = 'degraded'
            health_status['warning'] = 'Some worker threads are not running'
        if alert_queue.queue.qsize() > cfg.MAX_QUEUE_SIZE * 0.8:
            health_status['status'] = 'degraded'
            health_status['warning'] = 'Queue is nearly full'
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code

    @app.route('/metrics', methods=['GET'])
    def prometheus_metrics():
        return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

    @app.route('/config', methods=['GET'])
    @require_token(cfg, logger, metrics)
    @require_admin_mfa()
    def get_config():
        return jsonify({
            "routing_label": cfg.ROUTING_LABEL,
            "routing_config": {k: asdict(v) for k, v in cfg.ROUTING_CONFIG.items()},
            "allowed_values": list(cfg.ALLOWED_VALUES),
            "excluded_namespaces": list(cfg.EXCLUDED_NAMESPACES),
            "excluded_alertnames": list(cfg.EXCLUDED_ALERTNAMES),
            "excluded_jobs": list(cfg.EXCLUDED_JOBS),
            "queue_status": {
                "size": alert_queue.queue.qsize(),
                "max_size": cfg.MAX_QUEUE_SIZE,
                "workers": cfg.WORKER_THREADS,
            },
        }), 200

    @app.route('/reload', methods=['POST'])
    @require_token(cfg, logger, metrics)
    @require_admin_mfa()
    def reload_config():
        try:
            nonlocal cfg, alert_filter
            cfg = Config()
            alert_filter.config = cfg
            logger.info("Configuration reloaded successfully")
            return jsonify({"status": "success", "message": "Configuration reloaded"}), 200
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return jsonify({"error": str(e)}), 500

    def signal_handler(signum, frame):
        alert_queue.stop()
        try:
            health_checker.stop()
        except Exception:
            pass
        try:
            os._exit(0)
        except Exception:
            pass

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app.extensions['alert_ctx'] = {
        'config': cfg,
        'logger': logger,
        'metrics': metrics,
        'http_pool': http_pool,
        'template_manager': template_manager,
        'alert_filter': alert_filter,
        'alert_queue': alert_queue,
        'health_checker': health_checker,
    }
    return app


_initialized = False
_last_app = None

def initialize_app(app=None):
    global _initialized, _last_app
    if _initialized:
        return
    app = app or _last_app or create_app()
    ctx = app.extensions['alert_ctx']
    logger = ctx['logger']
    cfg = ctx['config']
    ctx['alert_queue'].start_workers(cfg.WORKER_THREADS)
    try:
        ctx['health_checker'].start()
    except Exception as e:
        logger.warning(f"HealthChecker failed to start: {e}")
    _initialized = True
    if os.getenv('TEST_GAPO_ON_STARTUP', 'false').lower() == 'true':
        try:
            test_payload = {
                "collab_id": cfg.DEFAULT_CHAT_CONFIG.collab_id,
                "bot_id": cfg.DEFAULT_CHAT_CONFIG.bot_id,
                "receiver_id": cfg.DEFAULT_CHAT_CONFIG.receiver_id,
                "body": {"type": "text", "text": "startup test", "is_markdown_text": True},
            }
            headers = {"Content-Type": "application/json", "x-hub-signature": cfg.GAPO_SIGNATURE}
            ctx['http_pool'].post(cfg.GAPO_API_URL, json=test_payload, headers=headers, timeout=5)
        except Exception as e:
            logger.warning(f"Gapo API test failed: {e}")