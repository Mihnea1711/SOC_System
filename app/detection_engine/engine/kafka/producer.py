import json
from confluent_kafka import Producer
from engine.utils.config import settings
from engine.utils.logger import logger

class KafkaProducerService:
    def __init__(self):
        self.bootstrap_servers = settings.kafka['bootstrap_servers']
        self.conf = {
            'bootstrap.servers': self.bootstrap_servers,
            # optional configurations (acks, compression, retries)
            'client.id': 'detection-engine-producer',
            'acks': 'all' # Ensures the leader and all replicas acknowledge the write
        }
        self.producer = None

    def connect(self):
        """Initialize the Kafka Producer."""
        try:
            self.producer = Producer(self.conf)
            logger.info(f"Successfully connected Kafka producer to {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka Producer: {e}")
            raise

    def send_alert(self, topic: str, payload: dict, key: str = None):
        """
        Produce a message (an alert or an enriched log) to a specific topic.
        
        Args:
            topic (str): The destination Kafka topic.
            payload (dict): The message content, usually an alert dictionary.
            key (str, optional): An optional partition key (e.g., an IP address or alert type).
        """
        if not self.producer:
            self.connect()

        try:
            # Convert dictionary to JSON string
            json_payload = json.dumps(payload).encode('utf-8')
            
            # Key must also be bytes if provided
            byte_key = key.encode('utf-8') if key else None

            # Produce message asynchronously
            self.producer.produce(
                topic=topic,
                key=byte_key,
                value=json_payload,
                callback=self._delivery_report
            )
            
            # Polls for callback events (success/failure)
            self.producer.poll(0)
            
        except TypeError as e:
            logger.error(f"Failed to serialize payload to JSON: {e}. Payload: {payload}")
        except BufferError as e:
            logger.error(f"Kafka producer local queue is full: {e}. Consider calling flush().")
        except Exception as e:
            logger.error(f"Unexpected error producing message to topic {topic}: {e}")

    def flush_queue(self, timeout=10.0):
        """
        Block until all pending messages are sent.
        Useful when gracefully shutting down the application.
        """
        if self.producer:
            logger.info("Flushing Kafka producer queue...")
            remaining = self.producer.flush(timeout)
            if remaining > 0:
                logger.warning(f"Producer flush timed out. {remaining} messages still in queue.")
            else:
                logger.info("Kafka producer queue flushed successfully.")

    def _delivery_report(self, err, msg):
        """Called once for each message produced to indicate delivery result."""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
