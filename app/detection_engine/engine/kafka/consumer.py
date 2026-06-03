import json
from confluent_kafka import Consumer, KafkaError, KafkaException
from engine.utils.config import settings
from engine.utils.logger import logger

from engine.filtering.filter_manager import NoiseFilterManager
from engine.filtering.rules import filter_nginx_internal_notices, filter_ubuntu_connectivity, filter_firefox_detectportal, filter_static_assets, filter_nginx_not_found_errors, filter_packetbeat_unmatched_responses, filter_dns_noise
from engine.normalization.normalizer import Normalizer

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

        # Initialize Filtering
        self.filter_manager = NoiseFilterManager()
        self.filter_manager.register_rule(filter_ubuntu_connectivity)
        self.filter_manager.register_rule(filter_firefox_detectportal)
        self.filter_manager.register_rule(filter_static_assets)

        self.filter_manager.register_rule(filter_nginx_internal_notices)
        self.filter_manager.register_rule(filter_nginx_not_found_errors)

        self.filter_manager.register_rule(filter_packetbeat_unmatched_responses)
        self.filter_manager.register_rule(filter_dns_noise)
        
        # Initialize Normalization
        self.normalizer = Normalizer()

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
            # 1. Deserialization
            raw_payload = json.loads(msg.value().decode('utf-8'))
            
            # 2. Noise Filtering
            if self.filter_manager.is_noise(raw_payload):
                # Dropping the event silently to save I/O
                return
                
            # 3. Normalization
            normalized_event = self.normalizer.normalize(raw_payload)
            if not normalized_event:
                # Normalization failed or returned None
                return
                
            # 4. Pass the clean, normalized event to the core processor
            callback(topic, normalized_event)
            
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
