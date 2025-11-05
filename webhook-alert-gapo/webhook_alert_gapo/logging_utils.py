import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from flask import g, has_request_context


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(g, 'request_id', 'no-request') if has_request_context() else 'no-request'
        return True


class SafeFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = 'no-request'
        return super().format(record)


def setup_logging():
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'

    handlers = []
    if os.getenv('LOG_TO_STDOUT', 'true').lower() == 'true':
        handlers.append(logging.StreamHandler(sys.stdout))
    if os.getenv('LOG_TO_FILE', 'false').lower() == 'true':
        log_file = os.getenv('LOG_FILE_PATH', '/tmp/alert_router.log')
        max_bytes = int(os.getenv('LOG_MAX_BYTES', '10485760'))
        backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        try:
            handlers.append(RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count))
        except Exception as e:
            logging.getLogger(__name__).warning(f"File logging disabled: {e}")
            if not any(isinstance(h, logging.StreamHandler) for h in handlers):
                handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(level=getattr(logging, log_level), handlers=handlers)

    context_filter = ContextFilter()
    root_logger = logging.getLogger()
    root_logger.addFilter(context_filter)
    logging.getLogger(__name__).addFilter(context_filter)
    logging.getLogger('werkzeug').addFilter(context_filter)
    logging.getLogger('werkzeug._internal').addFilter(context_filter)
    logging.getLogger('gunicorn.error').addFilter(context_filter)
    logging.getLogger('gunicorn.access').addFilter(context_filter)
    logging.getLogger('urllib3').addFilter(context_filter)
    logging.getLogger('requests').addFilter(context_filter)

    safe_formatter = SafeFormatter(log_format)
    for h in root_logger.handlers:
        h.setFormatter(safe_formatter)
    for name in ['werkzeug', 'werkzeug._internal', 'gunicorn.error', 'gunicorn.access', 'urllib3', 'requests', __name__]:
        lg = logging.getLogger(name)
        for h in getattr(lg, 'handlers', []):
            h.setFormatter(safe_formatter)

    return logging.getLogger(__name__)