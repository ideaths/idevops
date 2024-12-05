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
THRESHOLD_MULTIPLIER = Decimal(os.getenv("THRESHOLD_MULTIPLIER", "2"))  # StdDev multiplier for threshold
HIGH_LATENCY_RATIO_THRESHOLD = Decimal(os.getenv("HIGH_LATENCY_RATIO_THRESHOLD", "1"))  # High latency ratio threshold in percentage

# Allowed service names for alerts
ALLOWED_SERVICES = os.getenv("ALLOWED_SERVICES", "efast-mobile,efast-uiux-web").split(",")


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


def check_high_response_time(client):
    logger.info("Checking for high response time...")

    # Add service name filtering in SQL query
    allowed_services_filter = " OR ".join([f"serviceName = '{service}'" for service in ALLOWED_SERVICES])

    # Baseline query to calculate thresholds
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

    for row in baseline_result.result_rows:
        service_name = row[0]
        operation_name = row[1]
        http_target = row[2] or 'N/A'  # Handle null values
        avg_duration = Decimal(row[3])
        stddev_duration = Decimal(row[4])
        threshold = avg_duration + (THRESHOLD_MULTIPLIER * stddev_duration)

        logger.info(f"Processing service '{service_name}', operation '{operation_name}', http.target '{http_target}'. "
                    f"Average duration: {avg_duration}, StdDev: {stddev_duration}, Threshold: {threshold}")

        # Query to count total spans and spans exceeding threshold in the last 15 minutes
        span_count_query = f"""
        SELECT
            COUNTIf(durationNano > {threshold}) AS high_latency_count,
            COUNT(*) AS total_count
        FROM
            signoz_traces.distributed_signoz_index_v2
        WHERE
            serviceName = '{service_name}'
            AND name = '{operation_name}'
            AND splitByString('?', stringTagMap['http.target'])[1] = '{http_target}'
            AND timestamp >= now() - INTERVAL 15 MINUTE
        """
        logger.info(f"Executing span count query:\n{span_count_query.strip()}")
        try:
            span_count_result = client.query(span_count_query)
            if span_count_result.result_rows:
                high_latency_count = span_count_result.result_rows[0][0]
                total_count = span_count_result.result_rows[0][1]

                # Calculate the percentage of spans with high latency
                if total_count > 0:
                    high_latency_ratio = (Decimal(high_latency_count) / Decimal(total_count)) * 100
                    logger.info(f"High latency ratio: {high_latency_ratio:.2f}% for service '{service_name}', operation '{operation_name}', http.target '{http_target}'.")

                    # Trigger alert if high latency spans exceed the threshold ratio
                    if high_latency_ratio > HIGH_LATENCY_RATIO_THRESHOLD:
                        message = (
                            f"*ALERT: High Response Time Ratio*\n"
                            f"Service: `{service_name}`\n"
                            f"Operation: `{operation_name}`\n"
                            f"http.target: `{http_target}`\n"
                            f"Threshold: `{threshold / Decimal(1e6):.2f} ms`\n"
                            f"*High Latency Spans: `{high_latency_count}`*\n"
                            f"*Total Spans: `{total_count}`*\n"
                            f"*Ratio: `{high_latency_ratio:.2f}%`*\n\n"
                            f"====[Service Dashboard]====\n"
                            f"{SIGNOZ_BASE_URL}/services/{service_name}?relativeTime=3h\n"
                        )
                        send_workchat_alert(message)
                else:
                    logger.info(f"No spans found for service '{service_name}', operation '{operation_name}', http.target '{http_target}'. Skipping alert.")
        except Exception as e:
            logger.error(f"Error executing span count query: {e}")


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




# export WORKCHAT_API_URL="http://10.0.72.130:8081/v1/messageSupport"
# export THREAD_ID="61555923755026"
# export USER_LIST="ducdt1"
# export PRIORITY="1"
# export CLICKHOUSE_HOST="localhost"
# export CLICKHOUSE_PORT="8123"
# export CLICKHOUSE_DATABASE="signoz_traces"
# export SIGNOZ_BASE_URL="https://awx.idevops.io.vn"
# export SCAN_INTERVAL=300
# export THRESHOLD_MULTIPLIER=2
# export HIGH_LATENCY_RATIO_THRESHOLD=1
# export ALLOWED_SERVICES="efast-mobile,efast-uiux-web"
