import os
import time
import logging
import mysql.connector
import requests
from datetime import datetime
from decimal import Decimal

# Load environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "otel_traces")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "<YOUR_TELEGRAM_BOT_TOKEN>")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "<YOUR_CHAT_ID>")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Connect to MySQL
def connect_to_mysql():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        logger.info("Connected to MySQL database.")
        return conn
    except mysql.connector.Error as e:
        logger.error(f"MySQL connection failed: {e}")
        raise

# Ensure alerts table exists
def setup_alerts_table():
    """
    Create the 'alerts' table if it does not exist.
    """
    conn = connect_to_mysql()
    cursor = conn.cursor()
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS alerts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            service_name VARCHAR(255) NOT NULL,
            span_name VARCHAR(255) NOT NULL,
            trace_id CHAR(32),
            span_id CHAR(16),
            alert_time DATETIME(3) NOT NULL,
            resolved_time DATETIME(3),
            status ENUM('active', 'resolved') NOT NULL DEFAULT 'active',
            UNIQUE KEY unique_alert (service_name, span_name, trace_id, span_id)
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
        logger.info("Table 'alerts' ensured.")
    except mysql.connector.Error as e:
        logger.error(f"MySQL Error (create alerts table): {e}")
    finally:
        cursor.close()
        conn.close()

# Send Telegram alert
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logger.info("Telegram alert sent successfully.")
        else:
            logger.error(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")

# Monitor spans response times grouped by service_name and span_name
def monitor_spans_response_times():
    setup_alerts_table()  # Ensure the alerts table exists before processing
    conn = connect_to_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get baseline (avg and stddev) from last 4 hours
        query_baseline = """
        SELECT s.name AS span_name, t.service_name,
               AVG(s.duration) / 1000 AS avg_duration_ms,
               STDDEV(s.duration) / 1000 AS stddev_duration_ms
        FROM spans s
        INNER JOIN traces t ON s.trace_id = t.trace_id
        WHERE s.start_time > NOW() - INTERVAL 4 HOUR
        GROUP BY s.name, t.service_name
        """
        cursor.execute(query_baseline)
        baseline_data = cursor.fetchall()

        for baseline in baseline_data:
            span_name = baseline['span_name']
            service_name = baseline['service_name']
            avg_baseline = Decimal(baseline['avg_duration_ms'])  # Ensure Decimal type
            stddev_baseline = Decimal(baseline['stddev_duration_ms'])  # Ensure Decimal type
            threshold = avg_baseline + 2 * stddev_baseline  # Perform calculations as Decimal

            # Get all durations in the last 15 minutes for the same service_name and span_name
            query_recent = """
            SELECT s.span_id, s.trace_id, s.start_time, s.duration / 1000 AS duration_ms
            FROM spans s
            INNER JOIN traces t ON s.trace_id = t.trace_id
            WHERE s.start_time > NOW() - INTERVAL 15 MINUTE
              AND s.name = %s AND t.service_name = %s
            """
            cursor.execute(query_recent, (span_name, service_name))
            recent_data = cursor.fetchall()

            for record in recent_data:
                span_id = record['span_id']
                trace_id = record['trace_id']
                duration_ms = Decimal(record['duration_ms'])  # Ensure Decimal type
                start_time = record['start_time']

                # Get span attributes
                query_attributes = """
                SELECT key_name, value_text
                FROM span_attributes
                WHERE span_id = %s
                """
                cursor.execute(query_attributes, (span_id,))
                attributes = cursor.fetchall()
                attribute_details = "\n".join(
                    f"{attr['key_name']}: `{attr['value_text']}`" for attr in attributes
                )

                # Calculate percentage above baseline
                percent_above_baseline = ((duration_ms - avg_baseline) / avg_baseline * 100) if avg_baseline > 0 else Decimal(0)

                if duration_ms > threshold:
                    # Check if alert already active for this span
                    query_active_alert = """
                    SELECT * FROM alerts
                    WHERE service_name = %s AND span_name = %s AND trace_id = %s AND span_id = %s AND status = 'active'
                    """
                    cursor.execute(query_active_alert, (service_name, span_name, trace_id, span_id))
                    active_alert = cursor.fetchone()

                    if not active_alert:
                        # Insert a new active alert for this span
                        insert_alert = """
                        INSERT INTO alerts (service_name, span_name, trace_id, span_id, alert_time, status)
                        VALUES (%s, %s, %s, %s, NOW(3), 'active')
                        """
                        cursor.execute(insert_alert, (service_name, span_name, trace_id, span_id))
                        conn.commit()

                        # Send alert
                        alert_message = (
                            f"*ALERT: High Span Response Time Detected*\n"
                            f"Service: `{service_name}`\n"
                            f"Span Name: `{span_name}`\n"
                            f"Trace ID: `{trace_id}`\n"
                            f"Span ID: `{span_id}`\n"
                            f"Start Time: `{start_time}`\n"
                            f"Duration: `{duration_ms:.3f} ms`\n"
                            f"Threshold: `{threshold:.3f} ms`\n"
                            f"Above Baseline: `{percent_above_baseline:.2f}%`\n\n"
                            f"*Attributes:*\n{attribute_details}"
                        )
                        send_telegram_alert(alert_message)
                else:
                    # Resolve alert if active for this span
                    query_resolve_alert = """
                    SELECT * FROM alerts
                    WHERE service_name = %s AND span_name = %s AND trace_id = %s AND span_id = %s AND status = 'active'
                    """
                    cursor.execute(query_resolve_alert, (service_name, span_name, trace_id, span_id))
                    active_alert = cursor.fetchone()

                    if active_alert:
                        # Mark the alert as resolved
                        resolve_alert = """
                        UPDATE alerts
                        SET status = 'resolved', resolved_time = NOW(3)
                        WHERE id = %s
                        """
                        cursor.execute(resolve_alert, (active_alert['id'],))
                        conn.commit()

                        # Send resolve notification with attributes and percentage above baseline
                        resolve_message = (
                            f"*RESOLVED: Span Response Time Back to Normal*\n"
                            f"Service: `{service_name}`\n"
                            f"Span Name: `{span_name}`\n"
                            f"Trace ID: `{trace_id}`\n"
                            f"Span ID: `{span_id}`\n"
                            f"Resolved Time: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}`\n"
                            f"Above Baseline: `{percent_above_baseline:.2f}%`\n\n"
                            f"*Attributes:*\n{attribute_details}"
                        )
                        send_telegram_alert(resolve_message)

    except mysql.connector.Error as e:
        logger.error(f"MySQL Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    while True:
        try:
            logger.info("Monitoring spans response times grouped by service_name...")
            monitor_spans_response_times()
            time.sleep(300)  # Check every 5 minutes
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(60)  # Retry after 1 minute if error occurs
