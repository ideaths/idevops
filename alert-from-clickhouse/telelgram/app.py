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

# Alert configuration from environment
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "60"))  # Time between scans (in seconds)
THRESHOLD_MULTIPLIER = Decimal(os.getenv("THRESHOLD_MULTIPLIER", "2"))  # StdDev multiplier for threshold
ALERT_DURATION_THRESHOLD = Decimal(os.getenv("ALERT_DURATION_THRESHOLD", "2")) * Decimal(1e9)  # Minimum duration in nanoseconds

# In-memory dictionary to track active alerts
active_alerts = {}
# Set to track spans that have already been processed for alerts
processed_spans = set()


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


def fetch_trace_flow(client, trace_id):
    """
    Fetch and build the trace flow for a given traceID.
    """
    trace_query = f"""
    SELECT 
        spanID, 
        parentSpanID, 
        name, 
        serviceName, 
        durationNano 
    FROM 
        signoz_traces.distributed_signoz_index_v2
    WHERE 
        traceID = '{trace_id}'
    """
    logger.info(f"Executing trace flow query:\n{trace_query.strip()}")
    try:
        result = client.query(trace_query)
        spans = result.result_rows
        logger.info(f"Retrieved {len(spans)} spans for traceID {trace_id}.")

        span_dict = {row[0]: {"parent": row[1], "name": row[2], "service": row[3], "duration": row[4]} for row in spans}

        flow = []

        def build_flow(span_id, indent=0):
            span = span_dict.get(span_id)
            if not span:
                return
            flow.append(
                f"{'  ' * indent}- {span['service']} | {span['name']} | {Decimal(span['duration']) / Decimal(1e6):.2f} ms"
            )
            for child_id, child in span_dict.items():
                if child["parent"] == span_id:
                    build_flow(child_id, indent + 1)

        root_spans = [span_id for span_id, span in span_dict.items() if not span["parent"]]
        for root_span_id in root_spans:
            build_flow(root_span_id)

        return "\n".join(flow)
    except Exception as e:
        logger.error(f"Error fetching trace flow for traceID {trace_id}: {e}")
        return "Unable to retrieve trace flow."


def format_trace_id(trace_id):
    """
    Ensure traceID is properly formatted as a string.
    Decode bytes if necessary.
    """
    if isinstance(trace_id, bytes):
        return trace_id.decode('utf-8')  # Decode bytes to string
    return trace_id  # Return as-is if already a string


def format_alert_message(alert_type, service_name, operation_name, trace_id, span_id, details, attributes, resolved=False):
    trace_link = ""
    if trace_id and span_id:
        trace_id = format_trace_id(trace_id)  # Ensure traceID is properly formatted
        trace_link = f"[View Trace in SigNoz]({SIGNOZ_BASE_URL}/trace/{trace_id}?spanId={span_id})"

    attributes_text = "\n".join([f"{key}: `{value}`" for key, value in attributes.items()])

    if not resolved:
        return (
            f"*ALERT: {alert_type}*\n"
            f"{details}\n\n"
            f"{trace_link}\n"
            f"⚠️ Please check the service immediately."
        )
    else:
        return (
            f"*RESOLVED: {alert_type}*\n"
            f"{details}\n\n"
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

    new_alerts = {}

    for row in baseline_result.result_rows:
        service_name = row[0]
        operation_name = row[1]
        avg_duration = Decimal(row[2])
        stddev_duration = Decimal(row[3])
        threshold = avg_duration + (THRESHOLD_MULTIPLIER * stddev_duration)

        logger.info(f"Processing service '{service_name}', operation '{operation_name}'. "
                    f"Average duration: {avg_duration}, StdDev: {stddev_duration}, Threshold: {threshold}")

        # Query for spans exceeding the threshold
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
            AND parentSpanID = ''  -- Only root spans
            AND durationNano > {threshold}
            AND durationNano > {ALERT_DURATION_THRESHOLD}  -- Only spans exceeding alert threshold
            AND timestamp >= now() - INTERVAL 15 MINUTE
        """
        logger.info(f"Executing span query:\n{span_query.strip()}")
        try:
            span_result = client.query(span_query)
            logger.info(f"Found {len(span_result.result_rows)} spans exceeding the threshold for operation '{operation_name}'.")
        except Exception as e:
            logger.error(f"Error executing span query: {e}")
            continue

        if not span_result.result_rows:
            logger.info(f"No spans exceeding the threshold for operation '{operation_name}'. Skipping alert.")
            continue  # Skip to the next service/operation if no spans exceed the threshold

        # Process spans exceeding the threshold
        if (service_name, operation_name) not in new_alerts:
            new_alerts[(service_name, operation_name)] = {
                "service_name": service_name,
                "operation_name": operation_name,
                "threshold": threshold / Decimal(1e6),  # Convert to ms
                "spans": []
            }

        for span in span_result.result_rows:
            trace_id = format_trace_id(span[0])
            span_id = span[1]
            if span_id in processed_spans:
                logger.info(f"SpanID {span_id} already processed, skipping.")
                continue  # Skip this span if it's already processed

            duration = Decimal(span[2]) / Decimal(1e6)  # Convert to ms
            timestamp = span[3]
            percent_above = ((duration - threshold / Decimal(1e6)) / (threshold / Decimal(1e6))) * Decimal(100)

            new_alerts[(service_name, operation_name)]["spans"].append({
                "trace_id": trace_id,
                "span_id": span_id,
                "duration": duration,
                "percent_above": percent_above,
                "timestamp": timestamp
            })

    # Send alerts
    for (service_name, operation_name), alert_data in new_alerts.items():
        if not alert_data["spans"]:
            logger.info(f"No spans to alert for operation '{operation_name}'. Skipping alert.")
            continue  # Skip alert if there are no spans exceeding the threshold

        if len(alert_data["spans"]) == 1:  # Single span alert
            span_details = alert_data["spans"][0]
            attributes = fetch_span_attributes(client, span_details["span_id"])
            trace_flow = fetch_trace_flow(client, span_details["trace_id"])

            details = (
                f"Service: `{service_name}`\n"
                f"Operation: `{operation_name}`\n"
                f"Threshold: `{alert_data['threshold']:.2f} ms`\n"
                f"Duration: `{span_details['duration']:.2f} ms` (Above Threshold: `{span_details['percent_above']:.2f}%`)\n"
                f"Timestamp: `{span_details['timestamp']}`\n\n"
                f"*Attributes:*\n"
                + "\n".join([f"- `{key}`: `{value}`" for key, value in attributes.items()]) +
                f"\n\n*Trace Flow:*\n```\n{trace_flow}\n```"
            )
            message = format_alert_message(
                "High Response Time", service_name, operation_name,
                trace_id=span_details["trace_id"], span_id=span_details["span_id"], details=details, attributes=attributes
            )
            send_telegram_alert(message)

            # Mark the span as processed
            processed_spans.add(span_details["span_id"])
        else:  # Multiple span alert
            links = "\n".join([
                f"- [Trace Link]({SIGNOZ_BASE_URL}/trace/{span['trace_id']}?spanId={span['span_id']}) "
                f"(Duration: `{span['duration']:.2f} ms`, Above Threshold: `{span['percent_above']:.2f}%`)"
                for span in alert_data["spans"]
            ])
            details = (
                f"Service: `{service_name}`\n"
                f"Operation: `{operation_name}`\n"
                f"Threshold: `{alert_data['threshold']:.2f} ms`\n\n"
                f"*Affected Spans:*\n{links}"
            )
            message = format_alert_message(
                "High Response Time", service_name, operation_name,
                trace_id=None, span_id=None, details=details, attributes={}
            )
            send_telegram_alert(message)

            # Mark all spans in this alert as processed
            for span in alert_data["spans"]:
                processed_spans.add(span["span_id"])


def monitor_traces():
    client = connect_to_clickhouse()
    while True:
        try:
            check_high_response_time(client)
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    monitor_traces()
