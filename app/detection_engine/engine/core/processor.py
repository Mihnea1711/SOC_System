from engine.utils.logger import logger
from engine.utils.config import settings

class DetectionProcessor:
    def __init__(self, kafka_producer, elastic_client):
        """
        Initialize the processor with the output clients.
        
        Args:
            kafka_producer (KafkaProducerService): For sending real-time alerts back to Kafka.
            elastic_client (ElasticsearchClient): For storing enriched logs and alerts in Elasticsearch.
        """
        self.producer = kafka_producer
        self.elastic = elastic_client
        self.alert_topic = settings.kafka['topics']['produce_signatures']

    def process(self, source_topic: str, payload: dict):
        """
        Dummy method to process an incoming log/packet.
        This is where enrichment, rules, and ML logic will go in the future.
        
        Args:
            source_topic (str): The topic the message came from (e.g., 'raw.logs').
            payload (dict): The parsed JSON payload of the message.
        """
        logger.info("im here and waiting")
        logger.info(payload)
        
        # # 1. TODO: Enrichment (GeoIP, ASN, etc.)
        # enriched_payload = payload.copy()
        # enriched_payload["tags"] = enriched_payload.get("tags", []) + ["enriched-dummy"]
        
        # # Store the enriched log in Elasticsearch
        # # E.g., 'logs-enriched' index
        # self.elastic.index_document("logs-enriched", enriched_payload)

        # # 2. TODO: Detection (Rules / ML)
        # # Dummy detection logic: if the log contains "failed password", generate an alert
        # message = str(enriched_payload.get("message", "")).lower()
        # if "failed password" in message or "error" in message:
            
        #     # Create a dummy alert
        #     alert = {
        #         "alert_type": "DUMMY_SIGNATURE_ALERT",
        #         "severity": "high",
        #         "description": "Detected a suspicious keyword in the logs.",
        #         "source_log": enriched_payload,
        #         "action_required": "block_ip",
        #         # Dummy IP for now
        #         "source_ip": "192.168.1.100" 
        #     }
            
        #     logger.info(f"ALERT GENERATED: {alert['alert_type']} from {source_topic}")
            
        #     # 3. Output to Kafka for Real-Time Mitigation
        #     self.producer.send_alert(
        #         topic=self.alert_topic,
        #         payload=alert,
        #         key=alert["source_ip"]
        #     )
            
        #     # 4. Output to Elasticsearch for Dashboards
        #     self.elastic.index_alert(alert)
