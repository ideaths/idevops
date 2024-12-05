import os
import logging
import mysql.connector
from datetime import datetime, timedelta

# Load environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "otel_traces")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
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

# Cleanup old data
def cleanup_old_data():
    conn = connect_to_mysql()
    cursor = conn.cursor()
    try:
        # Get the timestamp 7 days ago
        threshold_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Deleting data older than: {threshold_date}")

        # Define cleanup queries for each table
        cleanup_queries = {
            "spans": "DELETE FROM spans WHERE start_time < %s",
            "traces": "DELETE FROM traces WHERE start_time < %s",
            "alerts": "DELETE FROM alerts WHERE alert_time < %s",
            "span_attributes": """
                DELETE sa FROM span_attributes sa
                JOIN spans s ON sa.span_id = s.span_id
                WHERE s.start_time < %s
            """
        }

        # Execute cleanup for each table
        for table, query in cleanup_queries.items():
            cursor.execute(query, (threshold_date,))
            affected_rows = cursor.rowcount
            logger.info(f"Deleted {affected_rows} rows from table '{table}'.")

        # Commit the changes
        conn.commit()
        logger.info("Cleanup completed successfully.")

    except mysql.connector.Error as e:
        logger.error(f"MySQL Error during cleanup: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    try:
        logger.info("Starting cleanup process...")
        cleanup_old_data()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")