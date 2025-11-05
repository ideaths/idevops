import threading
import time
from typing import Dict, List


class HealthChecker:
    def __init__(self, cfg, http_pool, logger, metrics, alert_queue):
        self.cfg = cfg
        self.http_pool = http_pool
        self.logger = logger
        self.metrics = metrics
        self.alert_queue = alert_queue
        self._thread = None
        self._stop = threading.Event()
        self.status: Dict[str, Dict] = {}

    def _check_once(self):
        urls: List[str] = self.cfg.HEALTHCHECK_URLS
        if not urls:
            return
        for url in urls:
            start = time.time()
            try:
                resp = self.http_pool.get(url, timeout=self.cfg.HEALTHCHECK_TIMEOUT)
                code = resp.status_code
                ok = self.cfg.HEALTHCHECK_MIN_OK <= code <= self.cfg.HEALTHCHECK_MAX_OK
                self.status[url] = {
                    'status_code': code,
                    'ok': ok,
                    'elapsed': time.time() - start,
                    'checked_at': time.time(),
                }
                if not ok:
                    routing = self.cfg.HEALTHCHECK_ROUTING
                    chat_cfg = self.cfg.ROUTING_CONFIG.get(routing, self.cfg.DEFAULT_CHAT_CONFIG)
                    msg = f"Healthcheck FAILED: {url} returned {code} at {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    self.alert_queue.add({
                        'message': msg,
                        'config': chat_cfg,
                        'routing_value': routing,
                        'request_id': f"healthcheck-{int(time.time())}",
                    })
            except Exception as e:
                self.status[url] = {
                    'status_code': None,
                    'ok': False,
                    'error': str(e),
                    'elapsed': time.time() - start,
                    'checked_at': time.time(),
                }
                routing = self.cfg.HEALTHCHECK_ROUTING
                chat_cfg = self.cfg.ROUTING_CONFIG.get(routing, self.cfg.DEFAULT_CHAT_CONFIG)
                msg = f"Healthcheck ERROR: {url} exception {e} at {time.strftime('%Y-%m-%d %H:%M:%S')}"
                self.alert_queue.add({
                    'message': msg,
                    'config': chat_cfg,
                    'routing_value': routing,
                    'request_id': f"healthcheck-{int(time.time())}",
                })

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name='HealthChecker', daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        interval = max(10, int(self.cfg.HEALTHCHECK_INTERVAL))
        self.logger.info(f"HealthChecker started, interval={interval}s, urls={self.cfg.HEALTHCHECK_URLS}")
        while not self._stop.is_set():
            try:
                self._check_once()
            except Exception as e:
                self.logger.error(f"HealthChecker loop error: {e}")
            self._stop.wait(interval)
        self.logger.info("HealthChecker stopped")