import time
import sys
import threading
from engine.utils.logger import logger
from engine.utils.config import settings

from engine.kafka.consumer import KafkaConsumerService
from engine.kafka.producer import KafkaProducerService
from engine.elastic.client import ElasticsearchClient
from engine.core.processor import DetectionProcessor

# Global variables for graceful shutdown
consumer_service = None
producer_service = None
elastic_service = None

def signal_handler(signum, frame):
    """
    Handle termination signals (SIGINT, SIGTERM) to gracefully 
    shut down the Kafka clients and Elasticsearch connection.
    """
    logger.info("Termination signal received. Initiating graceful shutdown...")
    if consumer_service:
        consumer_service.close()
    if producer_service:
        producer_service.flush_queue()
    if elastic_service:
        elastic_service.close()
    
    logger.info("Graceful shutdown complete. Exiting.")
    sys.exit(0)

def main():
    global consumer_service, producer_service, elastic_service

    env = settings.app.get('environment', 'dev')
    logger.info(f"Starting Detection Engine ('{env}' mode)")

    # Initialize Clients
    consumer_service = KafkaConsumerService()
    producer_service = KafkaProducerService()
    elastic_service = ElasticsearchClient()

    try:
        # Try to connect producer and elastic search first
        producer_service.connect()
        elastic_service.connect()
        
        # Initialize the Core Processor
        processor = DetectionProcessor(
            kafka_producer=producer_service,
            elastic_client=elastic_service
        )

        # Start the Consumer Loop
        # The consume_loop blocks, so we run it in the main thread.
        # It takes processor.process as the callback.
        logger.info("Starting up the main consumer loop.")
        consumer_service.consume_loop(message_handler_callback=processor.process)
        
    except Exception as e:
        logger.critical(f"A critical error occurred during startup: {e}", exc_info=True)
    finally:
        # If we reach here, ensure everything is closed.
        if consumer_service:
            consumer_service.close()
        if producer_service:
            producer_service.flush_queue()
        if elastic_service:
            elastic_service.close()

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    main()
