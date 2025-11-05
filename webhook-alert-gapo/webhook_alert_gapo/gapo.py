import json
import time
from urllib.parse import urlparse
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from flask import has_request_context, g


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
)
def send_to_gapo_with_retry(message: str, chat_config, routing_value: str, config, http_pool, logger, metrics, request_id: str = "unknown"):
    start_time = time.time()
    x_request_id = g.get('request_id', request_id or 'unknown') if has_request_context() else (request_id or 'unknown')
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Request-ID': x_request_id,
        'x-hub-signature': config.GAPO_SIGNATURE,
    }
    payload = {
        "collab_id": chat_config.collab_id,
        "bot_id": chat_config.bot_id,
        "receiver_id": chat_config.receiver_id,
        "body": {"type": "text", "text": message, "is_markdown_text": True},
    }
    try:
        payload_json = json.dumps(payload, ensure_ascii=False)
        payload_size = len(payload_json)
        parsed = urlparse(config.GAPO_API_URL)
        logger.info(
            f"Sending to Gapo: receiver={chat_config.receiver_id} routing={routing_value} "
            f"host={parsed.hostname} scheme={parsed.scheme} path={parsed.path} size={payload_size}"
        )
    except Exception:
        logger.debug("Payload logging failed; continuing")
    response = http_pool.post(config.GAPO_API_URL, json=payload, headers=headers, timeout=chat_config.timeout)
    elapsed = time.time() - start_time
    status_group = 'success' if response.status_code < 400 else 'failed'
    metrics['messages_sent'].labels(routing_label=routing_value, status=status_group).inc()
    logger.info(f"Gapo response: status={response.status_code} elapsed={elapsed:.3f}s routing={routing_value}")
    return response