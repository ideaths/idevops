"""
Enhanced Alert Routing System
A production-ready webhook receiver for Prometheus Alertmanager with Gapo chat integration
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import json
import time
import hashlib
import hmac
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from functools import wraps, lru_cache
from threading import Thread, Lock
from queue import Queue, Full, Empty
from dataclasses import dataclass, asdict
from collections import defaultdict
import signal
import sys

from flask import Flask, request, jsonify, g, has_request_context
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from marshmallow import Schema, fields, ValidationError, validates_schema, EXCLUDE
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from werkzeug.middleware.proxy_fix import ProxyFix
import pyotp
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import ipaddress
from urllib.parse import urlparse

# -----------------------------------------------------------------------------
# 1. Enhanced Logging Configuration
# -----------------------------------------------------------------------------
class ContextFilter(logging.Filter):
    """Add request context to log records"""
    def filter(self, record):
        record.request_id = getattr(g, 'request_id', 'no-request') if has_request_context() else 'no-request'
        return True

class SafeFormatter(logging.Formatter):
    """Formatter that guarantees request_id exists on all records"""
    def format(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = 'no-request'
        return super().format(record)

def setup_logging():
    """Configure structured logging with context"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
    
    handlers = []
    if os.getenv('LOG_TO_STDOUT', 'true').lower() == 'true':
        handlers.append(logging.StreamHandler(sys.stdout))
    if os.getenv('LOG_TO_FILE', 'false').lower() == 'true':
        log_file = os.getenv('LOG_FILE_PATH', '/tmp/alert_router.log')
        max_bytes = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
        backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        try:
            handlers.append(RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count))
        except Exception as e:
            logging.getLogger(__name__).warning(f"File logging disabled: {e}")
            if not any(isinstance(h, logging.StreamHandler) for h in handlers):
                handlers.append(logging.StreamHandler(sys.stdout))
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=handlers
    )
    
    # Attach ContextFilter to root and common loggers (werkzeug) so all records have request_id
    context_filter = ContextFilter()
    root_logger = logging.getLogger()
    root_logger.addFilter(context_filter)
    logging.getLogger(__name__).addFilter(context_filter)
    logging.getLogger('werkzeug').addFilter(context_filter)
    logging.getLogger('werkzeug._internal').addFilter(context_filter)
    logging.getLogger('gunicorn.error').addFilter(context_filter)
    logging.getLogger('gunicorn.access').addFilter(context_filter)
    # Also ensure third-party libraries carry request_id
    logging.getLogger('urllib3').addFilter(context_filter)
    logging.getLogger('requests').addFilter(context_filter)

    # Ensure all handlers use SafeFormatter that provides default request_id
    safe_formatter = SafeFormatter(log_format)
    for h in root_logger.handlers:
        h.setFormatter(safe_formatter)
    for name in ['werkzeug', 'werkzeug._internal', 'gunicorn.error', 'gunicorn.access', 'urllib3', 'requests', __name__]:
        lg = logging.getLogger(name)
        for h in getattr(lg, 'handlers', []):
            h.setFormatter(safe_formatter)
    
    return logging.getLogger(__name__)

logger = setup_logging()

# -----------------------------------------------------------------------------
# 2. Configuration Management
# -----------------------------------------------------------------------------
@dataclass
class ChatConfig:
    """Configuration for Gapo chat"""
    collab_id: int
    bot_id: int
    receiver_id: str
    max_retries: int = 3
    timeout: int = 10

class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        # Basic settings
        self.GAPO_API_URL = os.getenv("GAPO_API_URL", "http://10.6.131.11:8082/webhooktest4pt/chatbot/alert-bot")
        self.GAPO_SIGNATURE = os.getenv("GAPO_SIGNATURE", "1")
        self.ALERTMANAGER_ENDPOINT = os.getenv("ALERTMANAGER_ENDPOINT", "/alertmanager")
        self.SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())
        self.WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN", "")
        self.IS_PRODUCTION = os.getenv("IS_PRODUCTION", "false").lower() == "true"
        
        # IP whitelist for webhook endpoint (comma-separated CIDRs or exact IPs)
        self.WEBHOOK_IP_WHITELIST = [ip.strip() for ip in os.getenv("WEBHOOK_IP_WHITELIST", "").split(',') if ip.strip()]
        
        # Rate limiter storage: memory only (no Redis)
        self.LIMITER_STORAGE = os.getenv("LIMITER_STORAGE", "memory://")
        
        # Queue settings
        self.MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "1000"))
        self.WORKER_THREADS = int(os.getenv("WORKER_THREADS", "4"))
        self.QUEUE_PUT_TIMEOUT = int(os.getenv("QUEUE_PUT_TIMEOUT", "2"))
        # Worker idle log throttle interval (seconds); 0 disables idle logging
        self.WORKER_IDLE_LOG_INTERVAL = int(os.getenv("WORKER_IDLE_LOG_INTERVAL", "30"))
        
        # Rate limiting
        self.RATE_LIMIT = os.getenv("RATE_LIMIT", "100 per minute")
        
        # Maximum allowed payload size
        self.MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "1048576"))
        
        # Detailed logging flag for alerts
        self.LOG_ALERT_DETAILS = os.getenv("LOG_ALERT_DETAILS", "false").lower() == "true"
        
        # Routing configuration
        self.ROUTING_LABEL = os.getenv("ROUTING_LABEL", "system")
        self.ALLOWED_VALUES = os.getenv("ALLOWED_VALUES", "efast,ipay").split(',')
        
        # Default chat config
        self.DEFAULT_CHAT_CONFIG = ChatConfig(
            collab_id=int(os.getenv("DEFAULT_COLLAB_ID", "1")),
            bot_id=int(os.getenv("DEFAULT_BOT_ID", "1")),
            receiver_id=os.getenv("DEFAULT_RECEIVER_ID", "1")
        )
        
        # Exclusion lists
        self.EXCLUDED_NAMESPACES = set(os.getenv(
            "EXCLUDED_NAMESPACES",
            "cattle-prometheus,cattle-system,cert-manager,default,kube-logging"
        ).split(','))
        
        self.EXCLUDED_ALERTNAMES = set(os.getenv(
            "EXCLUDED_ALERTNAMES",
            "InfoInhibitor,Watchdog,etcdHighNumberOfFailedGRPCRequests"
        ).split(','))
        
        self.EXCLUDED_JOBS = set(os.getenv("EXCLUDED_JOBS", "kafka,abcd").split(','))
        
        # Load routing configuration
        self.ROUTING_CONFIG = self._load_routing_config()
    
    def _load_routing_config(self) -> Dict[str, ChatConfig]:
        """Load and validate routing configuration"""
        config_str = os.getenv("ROUTING_CONFIG", '{}')
        
        try:
            raw_config = json.loads(config_str)
        except json.JSONDecodeError:
            logger.warning("Invalid ROUTING_CONFIG JSON, using default configuration")
            raw_config = {}
        
        routing_config = {}
        
        # Build config for each allowed value
        for value in self.ALLOWED_VALUES:
            if value in raw_config:
                cfg = raw_config[value]
                collab_id = cfg.get('collab_id', self.DEFAULT_CHAT_CONFIG.collab_id)
                bot_id = cfg.get('bot_id', self.DEFAULT_CHAT_CONFIG.bot_id)
                receiver_id = cfg.get('receiver_id', self.DEFAULT_CHAT_CONFIG.receiver_id)
                try:
                    collab_id = int(collab_id)
                except Exception:
                    collab_id = self.DEFAULT_CHAT_CONFIG.collab_id
                try:
                    bot_id = int(bot_id)
                except Exception:
                    bot_id = self.DEFAULT_CHAT_CONFIG.bot_id
                routing_config[value] = ChatConfig(
                    collab_id=collab_id,
                    bot_id=bot_id,
                    receiver_id=str(receiver_id)
                )
            else:
                # Try to get from individual env vars
                collab_env = os.getenv(f"{value.upper()}_COLLAB_ID", str(self.DEFAULT_CHAT_CONFIG.collab_id))
                bot_env = os.getenv(f"{value.upper()}_BOT_ID", str(self.DEFAULT_CHAT_CONFIG.bot_id))
                receiver_env = os.getenv(f"{value.upper()}_RECEIVER_ID", self.DEFAULT_CHAT_CONFIG.receiver_id)
                
                try:
                    collab_id = int(collab_env)
                except Exception:
                    collab_id = self.DEFAULT_CHAT_CONFIG.collab_id
                try:
                    bot_id = int(bot_env)
                except Exception:
                    bot_id = self.DEFAULT_CHAT_CONFIG.bot_id
                
                routing_config[value] = ChatConfig(
                    collab_id=collab_id,
                    bot_id=bot_id,
                    receiver_id=str(receiver_env)
                )
        
        return routing_config

config = Config()

# -----------------------------------------------------------------------------
# 3. Prometheus Metrics
# -----------------------------------------------------------------------------
metrics = {
    'alerts_received': Counter('alerts_received_total', 'Total alerts received', ['status', 'routing_label']),
    'alerts_filtered': Counter('alerts_filtered_total', 'Total alerts filtered out', ['reason']),
    'messages_sent': Counter('messages_sent_total', 'Total messages sent to Gapo', ['routing_label', 'status']),
    'processing_time': Histogram('alert_processing_duration_seconds', 'Time to process alerts'),
    'queue_size': Gauge('alert_queue_size', 'Current size of alert queue'),
    'active_workers': Gauge('active_worker_threads', 'Number of active worker threads')
}

# -----------------------------------------------------------------------------
# 4. Flask App Setup with Extensions
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# Cache setup
cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 300})

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[config.RATE_LIMIT],
    storage_uri=config.LIMITER_STORAGE
)
# Enforce global rate limit only; remove duplicate per-route limit for clarity

# Set maximum content length for Flask to reject large payloads
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# -----------------------------------------------------------------------------
# 5. Request Validation Schemas
# -----------------------------------------------------------------------------
class AlertSchema(Schema):
    """Schema for validating individual alerts"""
    status = fields.Str(required=True, validate=lambda x: x in ['firing', 'resolved'])
    labels = fields.Dict(required=True)
    annotations = fields.Dict(load_default={})
    startsAt = fields.DateTime(load_default=None)
    endsAt = fields.DateTime(load_default=None)
    generatorURL = fields.Str(load_default="")
    fingerprint = fields.Str(load_default="")

    class Meta:
        unknown = EXCLUDE

class AlertmanagerWebhookSchema(Schema):
    """Schema for validating Alertmanager webhook payload"""
    version = fields.Str(load_default="4")
    groupKey = fields.Str(load_default="")
    status = fields.Str(load_default="firing")
    receiver = fields.Str(load_default="")
    groupLabels = fields.Dict(load_default={})
    commonLabels = fields.Dict(load_default={})
    commonAnnotations = fields.Dict(load_default={})
    externalURL = fields.Str(load_default="")
    alerts = fields.List(fields.Nested(AlertSchema), required=True)
    truncatedAlerts = fields.Boolean(load_default=False)

    class Meta:
        unknown = EXCLUDE

    @validates_schema
    def validate_alerts(self, data, **kwargs):
        if not data.get('alerts'):
            raise ValidationError('Alerts list cannot be empty')

# -----------------------------------------------------------------------------
# 6. Security Decorators
# -----------------------------------------------------------------------------
def require_token(f):
    """Decorator to require authentication token via multiple methods."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not config.WEBHOOK_TOKEN:
            return f(*args, **kwargs)

        # 1. Check Authorization header (preferred)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
        # 2. Check custom header
        elif request.headers.get('X-Auth-Token'):
            token = request.headers.get('X-Auth-Token')
        # 3. Check query parameter (least preferred)
        else:
            token = request.args.get('token')

        if not token:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr} - no token")
            metrics['alerts_filtered'].labels(reason='unauthorized').inc()
            return jsonify({'error': 'Authentication required'}), 401

        if not hmac.compare_digest(token, config.WEBHOOK_TOKEN):
            logger.warning(f"Invalid token from {request.remote_addr}")
            metrics['alerts_filtered'].labels(reason='invalid_token').inc()
            return jsonify({'error': 'Invalid token'}), 403

        return f(*args, **kwargs)
    return decorated_function

def validate_webhook_signature(f):
    """Decorator to validate webhook signature if configured"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature_header = os.getenv('WEBHOOK_SIGNATURE_HEADER')
        signature_secret = os.getenv('WEBHOOK_SIGNATURE_SECRET')
        
        if not signature_header or not signature_secret:
            return f(*args, **kwargs)
        
        provided_signature = request.headers.get(signature_header)
        if not provided_signature:
            return jsonify({'error': 'Missing signature'}), 401
        
        # Calculate expected signature
        payload = request.get_data()
        expected_signature = hmac.new(
            signature_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(provided_signature, expected_signature):
            return jsonify({'error': 'Invalid signature'}), 403
        
        return f(*args, **kwargs)
    return decorated_function








# -----------------------------------------------------------------------------
# 7. Connection Pool for HTTP Requests
# -----------------------------------------------------------------------------


def _ip_in_whitelist(remote_ip: str, whitelist: list[str]) -> bool:
    """Check if remote_ip is within any allowed CIDR or exact IP."""
    if not whitelist:
        return True
    try:
        ip_obj = ipaddress.ip_address(remote_ip)
    except ValueError:
        return False
    for entry in whitelist:
        try:
            if '/' in entry:
                # CIDR
                if ip_obj in ipaddress.ip_network(entry, strict=False):
                    return True
            else:
                # Exact IP
                if ip_obj == ipaddress.ip_address(entry):
                    return True
        except ValueError:
            continue
    return False


def require_admin_mfa(f):
    """Decorator to require MFA for admin endpoints if configured.
    - Enforces TOTP when `ADMIN_MFA_TOTP_SECRET` is set.
    - Skips MFA if request IP is in `ADMIN_IP_WHITELIST` (CIDRs or exact IPs).
    - Accepts code via `X-Admin-MFA` header or `mfa` query param.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        totp_secret = os.getenv("ADMIN_MFA_TOTP_SECRET", "").strip()
        ip_whitelist_env = os.getenv("ADMIN_IP_WHITELIST", "")
        whitelist = [x.strip() for x in ip_whitelist_env.split(",") if x.strip()]

        # If remote IP is whitelisted, bypass MFA
        try:
            remote_ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '').split(',')[0].strip()
            if whitelist and _ip_in_whitelist(remote_ip, whitelist):
                return f(*args, **kwargs)
        except Exception:
            # If whitelist parsing fails, proceed to MFA check
            pass

        # If no secret configured, MFA is disabled
        if not totp_secret:
            return f(*args, **kwargs)

        # Get provided code
        provided_code = request.headers.get("X-Admin-MFA") or request.args.get("mfa")
        if not provided_code:
            return jsonify({"error": "MFA required"}), 401

        try:
            totp = pyotp.TOTP(totp_secret)
            if not totp.verify(provided_code, valid_window=1):
                return jsonify({"error": "Invalid MFA code"}), 401
        except Exception:
            return jsonify({"error": "MFA verification failed"}), 500

        return f(*args, **kwargs)
    return decorated_function





class HTTPConnectionPool:
    """Manage HTTP connection pool with retry logic"""
    
    def __init__(self, max_retries=3, backoff_factor=0.3, pool_size=10):
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
            respect_retry_after_header=True
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=pool_size,
            pool_maxsize=pool_size
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def post(self, url, **kwargs):
        """Make POST request with connection pooling"""
        return self.session.post(url, **kwargs)

http_pool = HTTPConnectionPool()

# -----------------------------------------------------------------------------
# 8. Alert Processing Queue
# -----------------------------------------------------------------------------
class AlertQueue:
    """Thread-safe queue for processing alerts asynchronously"""
    
    def __init__(self, max_size=1000):
        self.queue = Queue(maxsize=max_size)
        self.workers = []
        self.running = True
        self.lock = Lock()
        self.last_idle_log_time = 0
        self._was_busy = False
        
    def start_workers(self, num_workers=4):
        """Start worker threads"""
        for i in range(num_workers):
            worker = Thread(target=self._worker, daemon=True, name=f'AlertWorker-{i}')
            worker.start()
            self.workers.append(worker)
        
        metrics['active_workers'].set(num_workers)
        logger.info(f"Started {num_workers} worker threads")
    
    def _worker(self):
        """Worker thread to process alerts"""
        while self.running:
            try:
                item = self.queue.get(timeout=1)
                try:
                    if item is None:
                        break
                    metrics['queue_size'].set(self.queue.qsize())
                    # Process the alert within Flask application context
                    with app.app_context():
                        self._process_alert_item(item)
                    # Mark that we were busy handling work
                    self._was_busy = True
                except Exception as e:
                    logger.exception(f"Worker thread error: {e}")
                finally:
                    # Always mark task done to avoid queue.join() hanging
                    try:
                        self.queue.task_done()
                    except Exception:
                        pass
            except Empty:
                # Only emit idle log when transitioning from busy to idle
                if self._was_busy and config.WORKER_IDLE_LOG_INTERVAL > 0:
                    now = time.time()
                    with self.lock:
                        if now - self.last_idle_log_time >= config.WORKER_IDLE_LOG_INTERVAL:
                            logger.debug("Worker queue idle: no item within timeout")
                            self.last_idle_log_time = now
                            # Reset busy state after first idle log
                            self._was_busy = False
                continue
            except Exception as e:
                logger.exception(f"Worker outer loop error: {e}")
    
    def _process_alert_item(self, item):
        """Process a single alert item"""
        try:
            # Set up a minimal Flask g context for logging
            if has_request_context():
                # We're already in a request context
                pass
            else:
                # We're in a worker thread, set up minimal context
                g.request_id = item.get('request_id', 'worker-thread')
            
            send_to_gapo_with_retry(
                item['message'],
                item['config'],
                item['routing_value'],
                request_id=item.get('request_id', 'worker-thread')
            )
        except Exception as e:
            logger.error(f"Failed to process alert: {e}")
            metrics['messages_sent'].labels(
                routing_label=item['routing_value'],
                status='failed'
            ).inc()
    
    def add(self, item):
        """Add item to queue"""
        try:
            self.queue.put(item, block=True, timeout=config.QUEUE_PUT_TIMEOUT)
            metrics['queue_size'].set(self.queue.qsize())
            return True
        except Full:
            logger.warning(f"Alert queue is full; put timed out after {config.QUEUE_PUT_TIMEOUT}s")
            metrics['alerts_filtered'].labels(reason='queue_full').inc()
            return False
    
    def stop(self):
        """Stop all workers gracefully"""
        self.running = False
        
        # Add None to queue for each worker to signal shutdown
        for _ in self.workers:
            self.queue.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        logger.info("All worker threads stopped")

alert_queue = AlertQueue(max_size=config.MAX_QUEUE_SIZE)

# -----------------------------------------------------------------------------
# 9. Template Management
# -----------------------------------------------------------------------------
class TemplateManager:
    """Manage Jinja2 templates with caching and fallback"""
    
    def __init__(self, template_dir="./templates"):
        # Prefer TEMPLATE_DIR from environment/ConfigMap mount if provided
        env_template_dir = os.getenv("TEMPLATE_DIR")
        if env_template_dir and os.path.isdir(env_template_dir):
            template_dir = env_template_dir
        else:
            # Support PyInstaller _MEIPASS if present
            meipass = getattr(sys, '_MEIPASS', None)
            if meipass:
                candidate = os.path.join(meipass, 'templates')
                if os.path.isdir(candidate):
                    template_dir = candidate
        
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            cache_size=50
        )
        self.fallback_template = """
🔥 **{{ alert_name }}**
{% if summary %}📝 {{ summary }}{% endif %}
{% if description %}📄 {{ description }}{% endif %}
🏷️ {{ routing_label|title }}: {{ routing_value }}
{% for key, value in labels.items() %}
{% if key != routing_label and key in ['namespace', 'job', 'instance', 'service'] %}
🔖 {{ key|title }}: {{ value }}
{% endif %}
{% endfor %}
"""
    
    @lru_cache(maxsize=10)
    def get_template(self, name='alert_template.html'):
        """Get template with fallback"""
        try:
            return self.env.get_template(name)
        except TemplateNotFound:
            logger.warning(f"Template {name} not found, using fallback")
            return self.env.from_string(self.fallback_template)
    
    def render_alert(self, alert, routing_label, routing_value):
        """Render single alert to string"""
        template = self.get_template()
        
        return template.render(
            alert_name=alert.get('labels', {}).get('alertname', 'Unknown'),
            summary=alert.get('annotations', {}).get('summary', ''),
            description=alert.get('annotations', {}).get('description', ''),
            labels=alert.get('labels', {}),
            routing_label=routing_label,
            routing_value=routing_value
        )

template_manager = TemplateManager()

# -----------------------------------------------------------------------------
# 10. Alert Filtering and Processing
# -----------------------------------------------------------------------------
class AlertFilter:
    """Handle alert filtering logic"""
    
    def __init__(self, config):
        self.config = config
    
    def is_ignored(self, alert: Dict) -> Tuple[bool, str]:
        """
        Check if alert should be ignored
        Returns: (should_ignore, reason)
        """
        labels = alert.get("labels", {})
        namespace = labels.get("namespace", "")
        alertname = labels.get("alertname", "")
        job = labels.get("job", "")
        routing_value = labels.get(self.config.ROUTING_LABEL, "")
        
        # Check routing label
        if routing_value not in self.config.ALLOWED_VALUES:
            return True, "invalid_routing_value"
        
        # Check namespace
        if namespace in self.config.EXCLUDED_NAMESPACES:
            return True, "excluded_namespace"
        
        # Check alertname
        if alertname in self.config.EXCLUDED_ALERTNAMES:
            return True, "excluded_alertname"
        
        # Check job
        if job in self.config.EXCLUDED_JOBS:
            return True, "excluded_job"
        
        return False, ""

alert_filter = AlertFilter(config)

# -----------------------------------------------------------------------------
# 11. Gapo Integration
# -----------------------------------------------------------------------------
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
)
def send_to_gapo_with_retry(message: str, chat_config: ChatConfig, routing_value: str, request_id: str = "unknown"):
    """Send message to Gapo with retry logic"""
    
    start_time = time.time()
    
    # Safely determine request ID without relying on Flask `g` outside request context
    if has_request_context():
        x_request_id = g.get('request_id', request_id or 'unknown')
    else:
        x_request_id = request_id or 'unknown'
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Request-ID': x_request_id,
        'x-hub-signature': config.GAPO_SIGNATURE
    }
    
    payload = {
        "collab_id": chat_config.collab_id,
        "bot_id": chat_config.bot_id,
        "receiver_id": chat_config.receiver_id,
        "body": {
            "type": "text",
            "text": message,
            "is_markdown_text": True
        }
    }
    
    # Outbound logging before sending (enhanced details)
    try:
        payload_json = json.dumps(payload, ensure_ascii=False)
        payload_size = len(payload_json)
        parsed = urlparse(config.GAPO_API_URL)
        logger.info(
            f"Sending to Gapo: receiver={chat_config.receiver_id} routing={routing_value} "
            f"url={config.GAPO_API_URL} size={payload_size}B timeout={chat_config.timeout} "
            f"x_request_id={x_request_id}"
        )
        logger.info(
            f"Gapo request: method=POST scheme={parsed.scheme} host={parsed.hostname}:{parsed.port} path={parsed.path}"
        )
        logger.info(
            f"Gapo headers: Content-Type={headers.get('Content-Type')} Accept={headers.get('Accept')} "
            f"X-Request-ID={headers.get('X-Request-ID')} x-hub-signature={headers.get('x-hub-signature')}"
        )
        logger.info(
            f"Gapo payload: collab_id={payload['collab_id']} bot_id={payload['bot_id']} "
            f"receiver_id={payload['receiver_id']} body.type={payload['body']['type']} "
            f"is_markdown={payload['body'].get('is_markdown_text')} text_len={len(payload['body'].get('text',''))}"
        )
        logger.info(f"Gapo payload_preview={payload_json[:800]}")
    except Exception:
        logger.debug("Failed to assemble outbound log details", exc_info=True)
    
    try:
        response = http_pool.post(
            config.GAPO_API_URL,
            json=payload,
            headers=headers,
            timeout=chat_config.timeout
        )
        
        duration = time.time() - start_time
        
        # Detailed response logging
        try:
            logger.info(
                f"Gapo response: status={response.status_code} reason={getattr(response,'reason','')} "
                f"elapsed={duration:.2f}s url={getattr(response.request,'url','')}"
            )
            logger.info(f"Gapo response_body_preview={(response.text or '')[:800]}")
        except Exception:
            logger.debug("Failed to log Gapo response details", exc_info=True)
        
        if response.status_code == 200:
            logger.info(f"Message sent successfully to receiver {chat_config.receiver_id} in {duration:.2f}s")
            metrics['messages_sent'].labels(routing_label=routing_value, status='success').inc()
        else:
            logger.error(f"Gapo API error: {response.status_code} - {response.text}")
            metrics['messages_sent'].labels(routing_label=routing_value, status='error').inc()
            raise requests.exceptions.RequestException(f"API returned {response.status_code}")
        
    except Exception as e:
        logger.error(f"Failed to send to Gapo: {e}")
        metrics['messages_sent'].labels(routing_label=routing_value, status='failed').inc()
        raise
# -----------------------------------------------------------------------------
# 12. Message Formatting
# -----------------------------------------------------------------------------
def create_message(routing_value: str, firing_alerts: List, resolved_alerts: List) -> str:
    """Create formatted message for Gapo"""
    
    parts = []
    
    # Header
    parts.append(f"🏷️ **{config.ROUTING_LABEL.title()}: {routing_value.upper()}**")
    
    # Summary
    summaries = []
    if firing_alerts:
        summaries.append(f"{len(firing_alerts)} firing")
    if resolved_alerts:
        summaries.append(f"{len(resolved_alerts)} resolved")
    
    if summaries:
        parts.append(f"📊 **Summary**: {', '.join(summaries)}\n")
    
    # Firing alerts
    if firing_alerts:
        parts.append("🚨 **Alerts Firing** 🚨")
        for alert in firing_alerts:
            parts.append(template_manager.render_alert(alert, config.ROUTING_LABEL, routing_value))
        parts.append("")
    
    # Resolved alerts
    if resolved_alerts:
        parts.append("✅ **Alerts Resolved** ✅")
        for alert in resolved_alerts:
            parts.append(template_manager.render_alert(alert, config.ROUTING_LABEL, routing_value))
        parts.append("")
    
    # Timestamp
    parts.append(f"⏰ **Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(parts)

# -----------------------------------------------------------------------------
# 13. Request Helpers
# -----------------------------------------------------------------------------
@app.before_request
def before_request():
    """Set request context before processing"""
    g.request_id = request.headers.get('X-Request-ID', os.urandom(8).hex())
    g.start_time = time.time()
    # Detailed incoming request logging
    try:
        remote_ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '').split(',')[0].strip()
        method = request.method
        path = request.path
        query = request.query_string.decode('utf-8') if request.query_string else ''
        ua = request.headers.get('User-Agent', '')
        content_type = request.headers.get('Content-Type', '')
        content_length = request.content_length or 0
        has_auth = bool(request.headers.get('Authorization') or request.headers.get('X-Auth-Token') or request.args.get('token'))
        body_preview = ''
        alerts_count = None
        if method in ('POST', 'PUT') and (content_type or '').startswith('application/json'):
            body_json = request.get_json(silent=True)
            if isinstance(body_json, dict):
                alerts = body_json.get('alerts')
                alerts_count = len(alerts) if isinstance(alerts, list) else None
                try:
                    body_preview = json.dumps({k: body_json.get(k) for k in ('status','receiver','groupKey','commonLabels')}, ensure_ascii=False)
                except Exception:
                    body_preview = ''
        logger.info(f"Incoming request: ip={remote_ip} method={method} path={path} query=\"{query}\" ua=\"{ua}\" type={content_type} length={content_length} auth={'yes' if has_auth else 'no'} alerts_count={alerts_count} preview={body_preview}")
    except Exception:
        # Log but never block request
        logger.debug("Failed to log request details", exc_info=True)

@app.after_request
def after_request(response):
    """Log request completion and enforce security headers"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        logger.info(f"Request completed in {duration:.3f}s with status {response.status_code}")
        metrics['processing_time'].observe(duration)
    
    # Security headers
    response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '0'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'geolocation=()'
    # HSTS only if behind HTTPS (usually via ingress); user can set IS_PRODUCTION
    if config.IS_PRODUCTION:
        response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
    
    # Basic Content-Security-Policy for API-only server
    response.headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    return response

# -----------------------------------------------------------------------------
# 14. Main Webhook Endpoint
# -----------------------------------------------------------------------------
@app.route(config.ALERTMANAGER_ENDPOINT, methods=['POST'])
@require_token
@validate_webhook_signature
def alertmanager_webhook():
    """Main webhook endpoint for Alertmanager"""
    
    # Enforce IP whitelist if configured
    remote_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    if not _ip_in_whitelist(remote_ip, config.WEBHOOK_IP_WHITELIST):
        logger.warning(f"Blocked IP {remote_ip} not in whitelist")
        metrics['alerts_filtered'].labels(reason='ip_not_whitelisted').inc()
        return jsonify({"error": "IP not allowed"}), 403
    
    try:
        # Validate payload
        schema = AlertmanagerWebhookSchema()
        try:
            data = schema.load(request.json, unknown=EXCLUDE)
        except ValidationError as e:
            logger.warning(f"Invalid payload: {e.messages}")
            return jsonify({"error": "Invalid payload", "details": e.messages}), 400
        
        # Process alerts
        alerts_by_routing = defaultdict(lambda: {'firing': [], 'resolved': []})
        
        for alert in data['alerts']:
            # Optional detailed log per-alert
            if config.LOG_ALERT_DETAILS:
                al = alert
                logger.info(
                    "Alert detail: status=%s name=%s ns=%s svc=%s job=%s instance=%s sev=%s start=%s end=%s labels=%s annotations=%s",
                    al.get('status'),
                    al.get('labels', {}).get('alertname'),
                    al.get('labels', {}).get('namespace'),
                    al.get('labels', {}).get('service'),
                    al.get('labels', {}).get('job'),
                    al.get('labels', {}).get('instance'),
                    al.get('labels', {}).get('severity'),
                    al.get('startsAt'),
                    al.get('endsAt'),
                    json.dumps(al.get('labels', {}), ensure_ascii=False),
                    json.dumps(al.get('annotations', {}), ensure_ascii=False)
                )
            
            # Check if should ignore
            should_ignore, reason = alert_filter.is_ignored(alert)
            
            if should_ignore:
                logger.debug(f"Ignoring alert {alert.get('labels', {}).get('alertname')} - {reason}")
                metrics['alerts_filtered'].labels(reason=reason).inc()
                continue
            
            # Group by routing label and status
            routing_value = alert['labels'].get(config.ROUTING_LABEL, 'unknown')
            status = alert['status']
            
            alerts_by_routing[routing_value][status].append(alert)
            metrics['alerts_received'].labels(status=status, routing_label=routing_value).inc()
        
        # Send messages for each routing value
        messages_queued = 0
        
        for routing_value, alerts_dict in alerts_by_routing.items():
            firing_alerts = alerts_dict['firing']
            resolved_alerts = alerts_dict['resolved']
            
            if not firing_alerts and not resolved_alerts:
                continue
            
            # Get chat configuration
            chat_config = config.ROUTING_CONFIG.get(routing_value, config.DEFAULT_CHAT_CONFIG)
            
            # Create message
            message = create_message(routing_value, firing_alerts, resolved_alerts)
            
            # Queue for async processing
            queued = alert_queue.add({
                'message': message,
                'config': chat_config,
                'routing_value': routing_value,
                'request_id': g.request_id
            })
            
            if queued:
                messages_queued += 1
                logger.info(f"Queued alert for {routing_value}: {len(firing_alerts)} firing, {len(resolved_alerts)} resolved")
        
        return jsonify({
            "status": "success",
            "messages_queued": messages_queued,
            "request_id": g.request_id
        }), 200
        
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return jsonify({"error": "Internal server error", "request_id": g.request_id}), 500

# -----------------------------------------------------------------------------
# 15. Health & Monitoring Endpoints
# -----------------------------------------------------------------------------
@app.route('/health', methods=['GET'])
@cache.cached(timeout=10)
def health_check():
    """Health check endpoint"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "queue_size": alert_queue.queue.qsize(),
        "active_workers": len([w for w in alert_queue.workers if w.is_alive()]),
        "configuration": {
            "routing_label": config.ROUTING_LABEL,
            "configured_values": list(config.ROUTING_CONFIG.keys()),
            "allowed_values": list(config.ALLOWED_VALUES)
        }
    }
    
    # Check if any workers are dead
    if health_status['active_workers'] < config.WORKER_THREADS:
        health_status['status'] = 'degraded'
        health_status['warning'] = 'Some worker threads are not running'
    
    # Check queue size
    if alert_queue.queue.qsize() > config.MAX_QUEUE_SIZE * 0.8:
        health_status['status'] = 'degraded'
        health_status['warning'] = 'Queue is nearly full'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@app.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """Expose metrics for Prometheus"""
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/config', methods=['GET'])
@require_token
@require_admin_mfa
def get_config():
    """Get current configuration (secured)"""
    
    return jsonify({
        "routing_label": config.ROUTING_LABEL,
        "routing_config": {
            k: asdict(v) for k, v in config.ROUTING_CONFIG.items()
        },
        "allowed_values": list(config.ALLOWED_VALUES),
        "excluded_namespaces": list(config.EXCLUDED_NAMESPACES),
        "excluded_alertnames": list(config.EXCLUDED_ALERTNAMES),
        "excluded_jobs": list(config.EXCLUDED_JOBS),
        "queue_status": {
            "size": alert_queue.queue.qsize(),
            "max_size": config.MAX_QUEUE_SIZE,
            "workers": config.WORKER_THREADS
        }
    }), 200

@app.route('/reload', methods=['POST'])
@require_token
@require_admin_mfa
def reload_config():
    """Reload configuration without restart"""
    
    try:
        # Reload configuration
        global config
        config = Config()
        
        # Update components
        alert_filter.config = config
        
        logger.info("Configuration reloaded successfully")
        return jsonify({"status": "success", "message": "Configuration reloaded"}), 200
        
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------------------------
# 16. Graceful Shutdown
# -----------------------------------------------------------------------------
def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {sig}, shutting down gracefully...")
    
    # Stop accepting new requests
    alert_queue.stop()
    
    # Wait for queue to be processed
    alert_queue.queue.join()
    
    logger.info("Shutdown complete")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# -----------------------------------------------------------------------------
# 17. Application Startup
# -----------------------------------------------------------------------------
_initialized = False

def initialize_app():
    """Initialize application components"""
    global _initialized
    if _initialized:
        logger.debug("initialize_app() already executed; skipping re-initialization")
        return

    logger.info("=" * 50)
    logger.info("Starting Enhanced Alert Routing System")
    logger.info(f"Routing by label: {config.ROUTING_LABEL}")
    logger.info(f"Configured values: {list(config.ROUTING_CONFIG.keys())}")
    logger.info(f"Worker threads: {config.WORKER_THREADS}")
    logger.info(f"Queue size: {config.MAX_QUEUE_SIZE}")
    logger.info("=" * 50)
    
    # Start worker threads
    alert_queue.start_workers(config.WORKER_THREADS)
    _initialized = True
    
    # Test Gapo connectivity (optional)
    if os.getenv('TEST_GAPO_ON_STARTUP', 'false').lower() == 'true':
        try:
            test_payload = {
                "collab_id": config.DEFAULT_CHAT_CONFIG.collab_id,
                "bot_id": config.DEFAULT_CHAT_CONFIG.bot_id,
                "receiver_id": config.DEFAULT_CHAT_CONFIG.receiver_id,
                "body": {"type": "text", "text": "startup test", "is_markdown_text": True}
            }
            headers = {"Content-Type": "application/json", "x-hub-signature": config.GAPO_SIGNATURE}
            response = http_pool.post(config.GAPO_API_URL, json=test_payload, headers=headers, timeout=5)
            logger.info(f"Gapo API test: {response.status_code}")
        except Exception as e:
            logger.warning(f"Gapo API test failed: {e}")

# -----------------------------------------------------------------------------
# 18. Main Entry Point
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    # Initialize application
    initialize_app()
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'false').lower() == 'true',
        threaded=True
    )