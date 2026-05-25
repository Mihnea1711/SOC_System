import json
from confluent_kafka import Consumer, KafkaError, KafkaException
from engine.utils.config import settings
from engine.utils.logger import logger

class KafkaConsumerService:
    def __init__(self):
        self.bootstrap_servers = settings.kafka['bootstrap_servers']
        self.group_id = settings.kafka['group_id']
        self.topics = settings.kafka['topics']['consume']
        
        self.conf = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest',
        }
        
        self.consumer = None
        self._running = False

    def connect(self):
        """Initialize the Kafka Consumer and subscribe to topics."""
        try:
            self.consumer = Consumer(self.conf)
            self.consumer.subscribe(self.topics)
            logger.info(f"Successfully connected Kafka consumer to {self.bootstrap_servers}")
            logger.info(f"Subscribed to topics: {self.topics}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka Consumer: {e}")
            raise

    def consume_loop(self, message_handler_callback):
        """
        Continuously polls for new messages.
        Passes parsed messages to the provided callback function.
        """
        if not self.consumer:
            self.connect()

        self._running = True
        logger.info("Starting Kafka consume loop...")
        
        try:
            while self._running:
                # Poll for messages with a timeout (e.g., 1.0 second)
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event (not an actual error)
                        logger.debug(f"{msg.topic()} [{msg.partition()}] reached end at offset {msg.offset()}")
                    elif msg.error():
                        raise KafkaException(msg.error())
                else:
                    self._process_message(msg, message_handler_callback)

        except KeyboardInterrupt:
            logger.info("Consume loop interrupted by user (KeyboardInterrupt).")
        except Exception as e:
            logger.error(f"Error during consume loop: {e}", exc_info=True)
        finally:
            self.close()

    def _process_message(self, msg, callback):
        """Internal helper to parse the message and pass it to the callback."""
        topic = msg.topic()
        try:
            # Most logs (from Beats) will be JSON formatted
            payload = json.loads(msg.value().decode('utf-8'))
            logger.info(f"Received message from topic: {topic}")
            
            # Pass the parsed payload and the source topic to the core processor
            callback(topic, payload)
            
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode JSON from topic {topic}. Raw payload: {msg.value()}")
        except Exception as e:
            logger.error(f"Error processing message from topic {topic}: {e}")

    def close(self):
        """Cleanly close the consumer connection."""
        self._running = False
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("Kafka consumer connection closed cleanly.")
            except Exception as e:
                logger.error(f"Error while closing Kafka consumer: {e}")
