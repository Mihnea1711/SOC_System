from engine.utils.logger import logger
from engine.utils.config import settings
from engine.state.base import StateStore
from engine.enrichment.enricher import Enricher
from engine.core.rules import RULES

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
        self.enricher = Enricher()
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

        # 1. Enrich the event
        enriched_event = self.enricher.enrich(normalized_event)
        
        # For now, log the enriched event
        logger.info(enriched_event)

        # 2. Run detection rules
        alerts = []
        for rule in RULES:
            try:
                alert = rule(enriched_event, self.state_store)
                if alert:
                    alerts.append(alert)
            except Exception as e:
                logger.exception(f"Error running rule {rule.__name__}")

        # 3. Publish alerts
        for alert in alerts:
            logger.info(f"ALERT GENERATED: {alert['rule_name']} from {source_topic} | IP: {alert.get('source_ip')}")
            
            if self.producer and self.alert_topic:
                self.producer.send_alert(
                    topic=self.alert_topic,
                    payload=alert,
                    key=alert.get("source_ip", "unknown")
                )
            
            # TODO: Store the alert in Elasticsearch for Dashboards
            # if self.elastic:
            #     self.elastic.index_document("alerts", alert)
        