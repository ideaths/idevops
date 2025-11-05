import time
from threading import Thread, Lock
from queue import Queue, Full, Empty
from flask import has_request_context, g


class AlertQueue:
    def __init__(self, app, logger, metrics, config, processor):
        self.queue = Queue(maxsize=config.MAX_QUEUE_SIZE)
        self.workers = []
        self.running = True
        self.lock = Lock()
        self.last_idle_log_time = 0
        self._was_busy = False
        self.app = app
        self.logger = logger
        self.metrics = metrics
        self.config = config
        self.processor = processor

    def start_workers(self, num_workers=4):
        for i in range(num_workers):
            worker = Thread(target=self._worker, daemon=True, name=f'AlertWorker-{i}')
            worker.start()
            self.workers.append(worker)
        self.metrics['active_workers'].set(num_workers)
        self.logger.info(f"Started {num_workers} worker threads")

    def _worker(self):
        while self.running:
            try:
                item = self.queue.get(timeout=1)
                try:
                    if item is None:
                        break
                    self.metrics['queue_size'].set(self.queue.qsize())
                    with self.app.app_context():
                        self.processor(item)
                    self._was_busy = True
                except Exception as e:
                    self.logger.exception(f"Worker thread error: {e}")
                finally:
                    try:
                        self.queue.task_done()
                    except Exception:
                        pass
            except Empty:
                if self._was_busy and self.config.WORKER_IDLE_LOG_INTERVAL > 0:
                    now = time.time()
                    with self.lock:
                        if now - self.last_idle_log_time >= self.config.WORKER_IDLE_LOG_INTERVAL:
                            self.logger.debug("Worker queue idle: no item within timeout")
                            self.last_idle_log_time = now
                            self._was_busy = False
                continue
            except Exception as e:
                self.logger.exception(f"Worker outer loop error: {e}")

    def add(self, item):
        try:
            self.queue.put(item, timeout=self.config.QUEUE_PUT_TIMEOUT)
            self.metrics['queue_size'].set(self.queue.qsize())
            return True
        except Full:
            self.logger.warning("Queue is full; dropping alert")
            return False

    def stop(self):
        self.running = False
        for _ in self.workers:
            self.queue.put(None)
        for w in self.workers:
            try:
                w.join(timeout=2)
            except Exception:
                pass