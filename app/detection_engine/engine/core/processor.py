from engine.utils.logger import logger
from engine.utils.config import settings
from engine.state.base import StateStore

class DetectionProcessor:
    def __init__(self, state_store: StateStore, kafka_producer=None, elastic_client=None):
        """
        Initialize the processor with state management and output clients.
        
        Args:
            state_store (StateStore): Interface for tracking state (e.g. failed logins).
            kafka_producer (KafkaProducerService): For sending real-time alerts back to Kafka.
            elastic_client (ElasticsearchClient): For storing enriched logs and alerts in Elasticsearch.
        """
        self.state_store = state_store
        self.producer = kafka_producer
        self.elastic = elastic_client
        self.alert_topic = settings.kafka['topics']['produce_signatures']

    def process(self, source_topic: str, normalized_event: dict):
        """
        Process a normalized event through the detection rules.
        
        Args:
            source_topic (str): The topic the message came from.
            normalized_event (dict): The clean, flattened dictionary from the Normalizer.
        """
        # For now, just log the clean, normalized event to verify our pipeline works
        # logger.info(f"Processed Normalized Event [{normalized_event['event_type']}]: "
        #             f"Src: {normalized_event['source_ip']} -> "
        #             f"Dst: {normalized_event['destination_ip']}:{normalized_event['destination_port']} | "
        #             f"Method: {normalized_event['http_method']} | "
        #             f"Path: {normalized_event['url_path']}")
        logger.info(normalized_event)
        # TODO: Route `normalized_event` to static and stateful rules here.
        # TODO: Detection (Rules / ML)
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

        #     # 1. Output to Kafka for Real-Time Mitigation
        #     self.producer.send_alert(
        #         topic=self.alert_topic,
        #         payload=alert,
        #         key=alert["source_ip"]
        #     )

        #      # 2. TODO: Enrichment (GeoIP, ASN, etc.)
        #      enriched_payload = payload.copy()
        #      enriched_payload["tags"] = enriched_payload.get("tags", []) + ["enriched-dummy"]

        #      # 3 Store the enriched log in Elasticsearch for Dashboards
        #      # E.g., 'logs-enriched' index
        #      self.elastic.index_document("logs-enriched", enriched_payload)
            
        #      # 4. Output to Kafka for Real-Time Mitigation
        #      self.producer.send_alert(
        #         topic=self.alert_topic,
        #         payload=alert,
        #         key=alert["source_ip"]
        #      )    
        