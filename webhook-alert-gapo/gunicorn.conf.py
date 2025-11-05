import os

# Read settings from environment with defaults
workers = int(os.getenv('GUNICORN_WORKERS', '2'))
threads = int(os.getenv('GUNICORN_THREADS', '4'))
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:5000')
timeout = int(os.getenv('GUNICORN_TIMEOUT', '60'))
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'gthread')
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
accesslog = '-'  # stdout
errorlog = '-'   # stdout

# Preload app to share memory between workers
preload_app = True

# Hook: post worker init

def post_worker_init(worker):
    # Optionally, initialize app components per worker, if needed
    try:
        from webhook_alert_gapo import initialize_app
        initialize_app()
    except Exception as e:
        # Gunicorn will log the exception; avoid crash
        worker.log.warning(f"post_worker_init failed: {e}")