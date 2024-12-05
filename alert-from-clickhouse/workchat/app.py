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

# Workchat configuration
WORKCHAT_API_URL = os.getenv("WORKCHAT_API_URL", "http://10.0.72.130:8081/v1/messageSupport")
THREAD_ID = os.getenv("THREAD_ID", "61555923755026")
USER_LIST = os.getenv("USER_LIST", "ducdt1")
PRIORITY = os.getenv("PRIORITY", "1")

# ClickHouse configuration
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_PORT", "8123")
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "signoz_traces")

# SigNoz base URL for trace links
SIGNOZ_BASE_URL = os.getenv("SIGNOZ_BASE_URL", "https://awx.idevops.io.vn")

# Alert configuration from environment
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "300"))  # Time between scans (in seconds)
THRESHOLD_MULTIPLIER = Decimal(os.getenv("THRESHOLD_MULTIPLIER", "3"))  # StdDev multiplier for threshold
ALERT_DURATION_THRESHOLD = Decimal(os.getenv("ALERT_DURATION_THRESHOLD", "3")) * Decimal(1e9)  # Minimum duration in nanoseconds

# Allowed service names for alerts
ALLOWED_SERVICES = os.getenv("ALLOWED_SERVICES", "efast-mobile,efast-uiux-web").split(",")

# In-memory dictionary to track active alerts
active_alerts = {}
processed_spans = set()  # Set to track spans that have already been processed for alerts

# Maximum threshold in milliseconds (loaded from environment)
MAX_THRESHOLD_MS = int(os.getenv("MAX_THRESHOLD_MS", "10000"))  # 10 seconds default

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


def send_workchat_alert(message):
    url = WORKCHAT_API_URL
    payload = {
        "threadId": THREAD_ID,
        "userList": USER_LIST,
        "content": message,
        "priority": PRIORITY
    }
    headers = {
        'Content-Type': 'application/json',
        'charset': 'UTF-8',
        'Accept': 'application/json'
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info("Workchat alert sent successfully!")
        else:
            logger.warning(f"Failed to send Workchat alert: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Workchat alert: {e}")


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


def format_trace_id(trace_id):
    if isinstance(trace_id, bytes):
        return trace_id.decode('utf-8')  # Decode bytes to string
    return trace_id  # Return as-is if already a string


def format_alert_message(alert_type, service_name, operation_name, trace_id, span_id, details, attributes, duration, percent_above, http_target, multiple=False):
    # Generate the service dashboard link
    service_dashboard_link = f"{SIGNOZ_BASE_URL}/services/{service_name}?relativeTime=3h"

    # Generate the trace link
    trace_link = f"{SIGNOZ_BASE_URL}/trace/{trace_id}?spanId={span_id}" if trace_id and span_id else ""

    # Fetch Kubernetes attributes
    deployment_name = attributes.get("k8s.deployment.name", "N/A")
    namespace_name = attributes.get("k8s.namespace.name", "N/A")

    # Format the alert message
    if not multiple:  # Single trace alert
        return (
            f"*ALERT: {alert_type}*\n"
            f"K8s Deployment: `{deployment_name}`\n"
            f"K8s Namespace: `{namespace_name}`\n"
            f"Service: `{service_name}`\n"
            f"Operation: `{operation_name}`\n"
            f"http.target: `{http_target}`\n"
            f"Threshold: `{details['threshold']:.2f} ms`\n"
            f"*Duration: `{duration:.2f} ms`*\n"
            f"*Above Threshold: `{percent_above:.2f}%`*\n\n"
            f"====[Service Dashboard]====\n"
            f"{service_dashboard_link}\n\n"
            f"=======[Link Trace]=======\n"
            f"{trace_link}"
        )
    else:  # Multi-trace alert
        return (
            f"*ALERT: {alert_type}*\n"
            f"Service: `{service_name}`\n"
            f"Operation: `{operation_name}`\n"
            f"http.target: `{http_target}`\n"
            f"K8s Deployment: `{deployment_name}`\n"
            f"K8s Namespace: `{namespace_name}`\n"
            f"Threshold: `{details['threshold']:.2f} ms`\n\n"
            f"====[Service Dashboard]====\n"
            f"{service_dashboard_link}\n\n"
            f"=======[Link Trace]=======\n"
            f"{trace_link}"
        )


def check_high_response_time(client):
    logger.info("Checking for high response time...")

    # Add service name filtering in SQL query
    allowed_services_filter = " OR ".join([f"serviceName = '{service}'" for service in ALLOWED_SERVICES])

    baseline_query = f"""
    SELECT
        serviceName,
        name AS operation_name,
        splitByString('?', stringTagMap['http.target'])[1] AS http_target,
        AVG(durationNano) AS avg_duration,
        stddevPop(durationNano) AS stddev_duration
    FROM
        signoz_traces.distributed_signoz_index_v2
    WHERE
        ({allowed_services_filter})  -- Filter for allowed services
        AND timestamp >= now() - INTERVAL 4 HOUR
    GROUP BY
        serviceName, operation_name, http_target
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
        http_target = row[2] or 'N/A'  # Handle null values
        avg_duration = Decimal(row[3])
        stddev_duration = Decimal(row[4])
        threshold = avg_duration + (THRESHOLD_MULTIPLIER * stddev_duration)

        # Kiểm tra nếu ngưỡng vượt quá 10 giây (MAX_THRESHOLD_MS từ env)
        threshold_ms = threshold / Decimal(1e6)  # Convert nanoseconds to milliseconds
        if threshold_ms > MAX_THRESHOLD_MS:
            logger.info(f"Skipping alert for service '{service_name}', operation '{operation_name}' due to threshold > {MAX_THRESHOLD_MS} ms.")
            continue  # Bỏ qua cảnh báo nếu ngưỡng lớn hơn giá trị MAX_THRESHOLD_MS từ env

        logger.info(f"Processing service '{service_name}', operation '{operation_name}', http.target '{http_target}'. "
                    f"Average duration: {avg_duration}, StdDev: {stddev_duration}, Threshold: {threshold_ms} ms")

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
            AND splitByString('?', stringTagMap['http.target'])[1] = '{http_target}'
            AND parentSpanID = ''  -- Only root spans
            AND durationNano > {threshold}
            AND durationNano > {ALERT_DURATION_THRESHOLD}  -- Only spans exceeding alert threshold
            AND timestamp >= now() - INTERVAL 15 MINUTE
        """
        logger.info(f"Executing span query:\n{span_query.strip()}")
        try:
            span_result = client.query(span_query)
            logger.info(f"Found {len(span_result.result_rows)} spans exceeding the threshold for operation '{operation_name}' and http.target '{http_target}'.")
        except Exception as e:
            logger.error(f"Error executing span query: {e}")
            continue

        if not span_result.result_rows:
            logger.info(f"No spans exceeding the threshold for operation '{operation_name}' and http.target '{http_target}'. Skipping alert.")
            continue  # Skip to the next service/operation if no spans exceed the threshold

        affected_spans = []
        k8s_deployment_names = set()
        k8s_namespace_names = set()

        for span in span_result.result_rows:
            trace_id = format_trace_id(span[0])
            span_id = span[1]
            duration = Decimal(span[2]) / Decimal(1e6)  # Convert to ms
            timestamp = span[3]
            percent_above = ((duration - threshold_ms) / threshold_ms) * Decimal(100)

            # Chỉ thêm span vào danh sách nếu vượt 80% threshold
            if percent_above >= Decimal(80):
                attributes = fetch_span_attributes(client, span_id)
                k8s_deployment_name = attributes.get("k8s.deployment.name", "N/A")
                k8s_namespace_name = attributes.get("k8s.namespace.name", "N/A")

                if k8s_deployment_name != "N/A":
                    k8s_deployment_names.add(k8s_deployment_name)
                if k8s_namespace_name != "N/A":
                    k8s_namespace_names.add(k8s_namespace_name)

                affected_spans.append({
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "duration": duration,
                    "percent_above": percent_above,
                    "timestamp": timestamp
                })

        if not affected_spans:
            logger.info(f"No spans exceeding the 80% threshold for service '{service_name}' and operation '{operation_name}'. Skipping alert.")
            continue  # Skip this service/operation if no affected spans

        deployment_name = ", ".join(k8s_deployment_names) if k8s_deployment_names else "N/A"
        namespace_name = ", ".join(k8s_namespace_names) if k8s_namespace_names else "N/A"

        if len(affected_spans) > 1:
            links = "\n".join([ 
                f"[Trace {i+1}]({SIGNOZ_BASE_URL}/trace/{s['trace_id']}?spanId={s['span_id']}) "
                f"(Duration: `{s['duration']:.2f} ms`, Above Threshold: `{s['percent_above']:.2f}%`)"
                for i, s in enumerate(affected_spans)
            ])
            details = {
                "threshold": threshold_ms
            }
            message = format_alert_message(
                alert_type="High Response Time (Multi-Trace)",
                service_name=service_name,
                operation_name=operation_name,
                trace_id=None,
                span_id=None,
                details=details,
                attributes={"k8s.deployment.name": deployment_name, "k8s.namespace.name": namespace_name},
                duration=None,
                percent_above=None,
                http_target=http_target,
                multiple=True
            ) + f"\n{links}"
            send_workchat_alert(message)
        else:
            span_details = affected_spans[0]  # Safe to access since we checked non-empty list
            details = {
                "threshold": threshold_ms
            }
            message = format_alert_message(
                alert_type="High Response Time",
                service_name=service_name,
                operation_name=operation_name,
                trace_id=span_details["trace_id"],
                span_id=span_details["span_id"],
                details=details,
                attributes={"k8s.deployment.name": deployment_name, "k8s.namespace.name": namespace_name},
                duration=span_details["duration"],
                percent_above=span_details["percent_above"],
                http_target=http_target
            )
            send_workchat_alert(message)


def main():
    client = connect_to_clickhouse()
    
    while True:
        check_high_response_time(client)
        logger.info(f"Waiting {SCAN_INTERVAL} seconds before next scan.")
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
