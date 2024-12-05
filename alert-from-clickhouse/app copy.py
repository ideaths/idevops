import os
import requests
import time
from decimal import Decimal
import clickhouse_connect
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Telegram configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ClickHouse configuration
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_PORT", "8123")
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "signoz_traces")

# SigNoz base URL for trace links
SIGNOZ_BASE_URL = os.getenv("SIGNOZ_BASE_URL", "https://awx.idevops.io.vn")


def connect_to_clickhouse():
    try:
        client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            database=CLICKHOUSE_DATABASE
        )
        logger.info(f"Connected to ClickHouse database '{CLICKHOUSE_DATABASE}' at {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to ClickHouse: {e}")
        raise


def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logger.info("Telegram alert sent successfully!")
        else:
            logger.warning(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")


def fetch_span_attributes(client, span_id):
    attributes_query = f"""
    SELECT 
        stringTagMap
    FROM 
        signoz_traces.distributed_signoz_index_v2
    WHERE 
        spanID = '{span_id}'
    """
    logger.info(f"Executing attributes query:\n{attributes_query.strip()}")
    try:
        result = client.query(attributes_query)
        if result.result_rows:
            string_tag_map = result.result_rows[0][0]
            return string_tag_map
        else:
            logger.warning(f"No attributes found for spanID {span_id}.")
            return {}
    except Exception as e:
        logger.error(f"Error fetching attributes for spanID {span_id}: {e}")
        return {}


def format_alert_message(alert_type, service_name, operation_name, trace_id, span_id, details, attributes, resolved=False):
    attributes_text = "\n".join([f"{key}: `{value}`" for key, value in attributes.items()])
    trace_link = f"{SIGNOZ_BASE_URL}/trace/{trace_id}?spanId={span_id}"

    if not resolved:
        return (
            f"*ALERT: {alert_type}*\n"
            f"Service: `{service_name}`\n"
            f"Operation: `{operation_name}`\n"
            f"{details}\n\n"
            f"*Attributes:*\n{attributes_text}\n\n"
            f"[View Trace in SigNoz]({trace_link})\n"
            f"⚠️ Please check the service immediately."
        )
    else:
        return (
            f"*RESOLVED: {alert_type}*\n"
            f"Service: `{service_name}`\n"
            f"Operation: `{operation_name}`\n"
            f"{details}\n\n"
            f"*Attributes:*\n{attributes_text}\n\n"
            f"[View Trace in SigNoz]({trace_link})\n"
            f"✅ Issue has been resolved."
        )


def check_high_response_time(client):
    logger.info("Checking for high response time...")
    baseline_query = """
    SELECT 
        serviceName, 
        name AS operation_name, 
        AVG(durationNano) AS avg_duration, 
        stddevPop(durationNano) AS stddev_duration
    FROM 
        signoz_traces.distributed_signoz_index_v2
    WHERE 
        timestamp >= now() - INTERVAL 4 HOUR
    GROUP BY 
        serviceName, operation_name
    """
    logger.info(f"Executing baseline query:\n{baseline_query.strip()}")
    try:
        baseline_result = client.query(baseline_query)
        logger.info("Baseline query executed successfully.")
    except Exception as e:
        logger.error(f"Error executing baseline query: {e}")
        return

    for row in baseline_result.result_rows:
        service_name = row[0]
        operation_name = row[1]
        avg_duration = Decimal(row[2])
        stddev_duration = Decimal(row[3])
        threshold = avg_duration + 2 * stddev_duration

        logger.info(f"Processing service '{service_name}', operation '{operation_name}'. "
                    f"Average duration: {avg_duration}, StdDev: {stddev_duration}, Threshold: {threshold}")

        span_query = f"""
        SELECT 
            traceID, 
            spanID, 
            durationNano, 
            timestamp 
        FROM 
            signoz_traces.distributed_signoz_index_v2
        WHERE 
            serviceName = '{service_name}' 
            AND name = '{operation_name}'
            AND durationNano > {threshold}
            AND timestamp >= now() - INTERVAL 15 MINUTE
        """
        logger.info(f"Executing span query:\n{span_query.strip()}")
        try:
            span_result = client.query(span_query)
            logger.info(f"Found {len(span_result.result_rows)} spans exceeding the threshold for operation '{operation_name}'.")
        except Exception as e:
            logger.error(f"Error executing span query: {e}")
            continue

        for span in span_result.result_rows:
            trace_id = span[0]
            span_id = span[1]
            duration_ms = Decimal(span[2]) / Decimal(1e6)
            timestamp = span[3]
            threshold_ms = threshold / Decimal(1e6)

            percent_above_threshold = ((duration_ms - threshold_ms) / threshold_ms) * 100

            if percent_above_threshold <= 50:
                logger.info(f"Span {span_id} exceeded threshold but not by more than 50%. Skipping alert.")
                continue

            details = (
                f"Trace ID: `{trace_id}`\n"
                f"Span ID: `{span_id}`\n"
                f"Duration: `{duration_ms:.2f} ms`\n"
                f"Threshold: `{threshold_ms:.2f} ms`\n"
                f"Above Threshold: `{percent_above_threshold:.2f}%`\n"
                f"Timestamp: `{timestamp}`"
            )
            logger.info(f"Span exceeding threshold by more than 50%:\n{details}")

            attributes = fetch_span_attributes(client, span_id)

            message = format_alert_message(
                "High Response Time", service_name, operation_name, trace_id, span_id, details, attributes
            )
            send_telegram_alert(message)


def monitor_traces():
    client = connect_to_clickhouse()
    while True:
        try:
            check_high_response_time(client)
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
        time.sleep(300)


if __name__ == "__main__":
    monitor_traces()
