import os
import time
import logging
from confluent_kafka import Consumer, KafkaError, KafkaException
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from datetime import datetime
import mysql.connector

# Load environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "default_topic")
GROUP_ID = os.getenv("GROUP_ID", "default_group")

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

# Convert milliseconds to DATETIME(3)
def convert_milliseconds_to_datetime(milliseconds):
    timestamp = milliseconds / 1000.0  # Convert to seconds
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Precision to 3 digits

# Connect to MySQL with retry logic
def connect_to_mysql(with_database=True, retries=60, delay=10):
    for attempt in range(retries):
        try:
            if with_database:
                conn = mysql.connector.connect(
                    host=MYSQL_HOST,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD,
                    database=MYSQL_DATABASE
                )
            else:
                conn = mysql.connector.connect(
                    host=MYSQL_HOST,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD
                )
            logger.info(f"MySQL connection established successfully on attempt {attempt + 1}.")
            return conn
        except mysql.connector.Error as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} - MySQL connection failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
    logger.error("MySQL connection failed after multiple attempts.")
    raise Exception("MySQL connection failed after multiple attempts.")

# Create database and tables
def setup_database():
    logger.info("Setting up database...")
    db_conn = connect_to_mysql(with_database=False)
    cursor = db_conn.cursor()

    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        logger.info(f"Database '{MYSQL_DATABASE}' ensured.")
    except mysql.connector.Error as e:
        logger.error(f"MySQL Error (create database): {e}")
    finally:
        cursor.close()
        db_conn.close()

    db_conn = connect_to_mysql(with_database=True)
    cursor = db_conn.cursor()

    CREATE_TRACES_TABLE = """
    CREATE TABLE IF NOT EXISTS traces (
        trace_id CHAR(32) PRIMARY KEY,
        service_name VARCHAR(255) NOT NULL,
        start_time DATETIME(3) NOT NULL,
        end_time DATETIME(3) NOT NULL,
        duration BIGINT GENERATED ALWAYS AS (TIMESTAMPDIFF(MICROSECOND, start_time, end_time)) STORED,
        INDEX idx_service_name (service_name),
        INDEX idx_start_time (start_time)
    );
    """

    CREATE_SPANS_TABLE = """
    CREATE TABLE IF NOT EXISTS spans (
        span_id CHAR(16) PRIMARY KEY,
        trace_id CHAR(32) NOT NULL,
        parent_span_id CHAR(16),
        name VARCHAR(255) NOT NULL,
        start_time DATETIME(3) NOT NULL,
        end_time DATETIME(3) NOT NULL,
        duration BIGINT GENERATED ALWAYS AS (TIMESTAMPDIFF(MICROSECOND, start_time, end_time)) STORED,
        FOREIGN KEY (trace_id) REFERENCES traces(trace_id) ON DELETE CASCADE,
        INDEX idx_trace_id (trace_id),
        INDEX idx_start_time (start_time),
        INDEX idx_name (name)
    );
    """

    CREATE_SPAN_ATTRIBUTES_TABLE = """
    CREATE TABLE IF NOT EXISTS span_attributes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        span_id CHAR(16) NOT NULL,
        key_name VARCHAR(255) NOT NULL,
        value_text TEXT,
        INDEX idx_span_id (span_id),
        FOREIGN KEY (span_id) REFERENCES spans(span_id) ON DELETE CASCADE
    );
    """

    try:
        cursor.execute(CREATE_TRACES_TABLE)
        logger.info("Table 'traces' ensured.")
        cursor.execute(CREATE_SPANS_TABLE)
        logger.info("Table 'spans' ensured.")
        cursor.execute(CREATE_SPAN_ATTRIBUTES_TABLE)
        logger.info("Table 'span_attributes' ensured.")
    except mysql.connector.Error as e:
        logger.error(f"MySQL Error (create tables): {e}")
    finally:
        cursor.close()
        db_conn.close()

# Insert trace, span, and attributes into MySQL
def insert_span_and_attributes(span_id, trace_id, parent_span_id, name, start_time, end_time, attributes):
    db_conn = connect_to_mysql()
    cursor = db_conn.cursor()
    try:
        # Check if trace exists, insert if not
        cursor.execute("SELECT COUNT(*) FROM traces WHERE trace_id = %s", (trace_id,))
        trace_exists = cursor.fetchone()[0]

        if not trace_exists:
            sql_trace = """
            INSERT INTO traces (trace_id, service_name, start_time, end_time)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE start_time=VALUES(start_time), end_time=VALUES(end_time)
            """
            cursor.execute(sql_trace, (trace_id, "unknown-service", start_time, end_time))
            logger.info(f"Trace inserted: {trace_id}")

        # Insert span
        sql_span = """
        INSERT INTO spans (span_id, trace_id, parent_span_id, name, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE start_time=VALUES(start_time), end_time=VALUES(end_time)
        """
        cursor.execute(sql_span, (span_id, trace_id, parent_span_id, name, start_time, end_time))

        # Insert attributes
        for key, value in attributes.items():
            sql_attr = """
            INSERT INTO span_attributes (span_id, key_name, value_text)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE value_text=VALUES(value_text)
            """
            cursor.execute(sql_attr, (span_id, key, value))

        # Commit transaction
        db_conn.commit()
        logger.info(f"Span and attributes inserted/updated for span: {span_id}")
    except mysql.connector.Error as e:
        db_conn.rollback()
        logger.error(f"MySQL Error (insert_span_and_attributes): {e}")
    finally:
        cursor.close()
        db_conn.close()

# Kafka Consumer Functions
def create_kafka_consumer():
    while True:
        try:
            logger.info("Initializing Kafka consumer...")
            consumer = Consumer({
                'bootstrap.servers': KAFKA_BROKER,
                'group.id': GROUP_ID,
                'auto.offset.reset': 'earliest'
            })
            consumer.subscribe([KAFKA_TOPIC])
            logger.info(f"Subscribed to topic: {KAFKA_TOPIC}")
            return consumer
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def consume_kafka_messages():
    consumer = create_kafka_consumer()

    try:
        while True:
            try:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().fatal():
                        logger.error(f"Fatal Kafka error: {msg.error()}. Reinitializing consumer...")
                        time.sleep(5)
                        consumer = create_kafka_consumer()
                        continue

                    logger.warning(f"Kafka non-fatal error: {msg.error()}")
                    continue

                logger.info("Message received from Kafka.")
                request = ExportTraceServiceRequest()
                request.ParseFromString(msg.value())

                for resource_span in request.resource_spans:
                    service_name = "unknown-service"
                    for span in resource_span.scope_spans[0].spans:
                        trace_id = span.trace_id.hex()
                        span_id = span.span_id.hex()
                        parent_span_id = span.parent_span_id.hex() if span.parent_span_id else None

                        start_time = convert_milliseconds_to_datetime(span.start_time_unix_nano // 1_000_000)
                        end_time = convert_milliseconds_to_datetime(span.end_time_unix_nano // 1_000_000)

                        attributes = {attr.key: attr.value.string_value for attr in span.attributes}

                        logger.info(f"Processing trace_id: {trace_id}, span_id: {span_id}, start_time: {start_time}, end_time: {end_time}")
                        insert_span_and_attributes(
                            span_id=span_id,
                            trace_id=trace_id,
                            parent_span_id=parent_span_id,
                            name=span.name,
                            start_time=start_time,
                            end_time=end_time,
                            attributes=attributes
                        )

            except KafkaException as e:
                logger.error(f"KafkaException encountered: {e}. Reinitializing consumer...")
                time.sleep(5)
                consumer = create_kafka_consumer()

            except Exception as e:
                logger.error(f"Unexpected error: {e}. Reinitializing consumer...")
                time.sleep(5)
                consumer = create_kafka_consumer()

    except KeyboardInterrupt:
        logger.info("Kafka consumer stopped by user.")
    finally:
        consumer.close()

if __name__ == "__main__":
    setup_database()
    consume_kafka_messages()