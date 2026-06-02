from engine.utils.logger import logger
from engine.utils.config import settings
from engine.state.base import StateStore
from engine.enrichment.enricher import Enricher
from engine.core.rules import RULES

from engine.kafka.producer import KafkaProducerService
from engine.elastic.client import ElasticsearchClient
from engine.core.ml.features import FeatureExtractor
from engine.core.ml.model import AnomalyDetector

class DetectionProcessor:
    def __init__(self, 
                 state_store: StateStore = None, 
                 kafka_producer: KafkaProducerService = None, 
                 elastic_client: ElasticsearchClient = None):
        """
        Initialize the processor with state management and output clients.
        
        Args:
            state_store (StateStore): Interface for tracking state (e.g. failed logins).
            kafka_producer (KafkaProducerService): For sending real-time alerts back to Kafka.
            elastic_client (ElasticsearchClient): For storing enriched logs and alerts in Elasticsearch.
        """
        self.state_store = state_store
        self.enricher = Enricher(state_store=self.state_store)
        self.producer = kafka_producer
        self.elastic = elastic_client
        
        # Topics
        self.alert_topic = settings.kafka['topics']['produce_signatures']
        self.anomaly_topic = settings.kafka['topics']['produce_anomalies']
        
        # ML Components
        self.anomaly_threshold = settings.ml['anomaly_threshold']
        self.feature_extractor = FeatureExtractor(window_seconds=settings.ml['window_size_seconds'])
        self.anomaly_detector = AnomalyDetector(warmup_observations=settings.ml['warmup_observations'])

    def process(self, source_topic: str, normalized_event: dict):
        """
        Process a normalized event through the detection rules.
        
        Args:
            source_topic (str): The topic the message came from.
            normalized_event (dict): The clean, flattened dictionary from the Normalizer.
        """
        event_type = normalized_event.get("event_type")

        # 1. Enrich the event
        enriched_event = self.enricher.enrich(normalized_event)
        
        # 2. Run detection rules
        alerts = []
        for rule in RULES:
            try:
                alert = rule(enriched_event, self.state_store)
                if alert:
                    alerts.append(alert)
            except Exception:
                logger.exception(f"Error running rule {rule.__name__}")

        # 3. Publish Signature Alerts
        for alert in alerts:
            # Ensure the alert has the timestamp of the event that triggered it
            if "timestamp" not in alert and "timestamp" in enriched_event:
                alert["@timestamp"] = enriched_event["timestamp"]
                
            logger.info(f"ALERT GENERATED: {alert['rule_name']} from {source_topic} | IP: {alert.get('source_ip')}")
            
            if self.producer and self.alert_topic:
                self.producer.send_alert(
                    topic=self.alert_topic,
                    payload=alert,
                    key=alert.get("source_ip", "unknown")
                )
            
            # Store the alert in Elasticsearch for Dashboards
            if self.elastic:
                self.elastic.index_alert(alert)

        # 4. ML Anomaly Detection
        # We only want to train the ML model on web logs, not raw packets.
        # Packetbeat generates multiple events (TCP flows, HTTP transactions) for a single request,
        # which skews the request_count and error_rate features heavily.
        if event_type == "web_log":
            features = self.feature_extractor.extract(enriched_event)
            if features:
                score = self.anomaly_detector.score_and_train(features)

                # Debug logging to see what the ML model is doing
                # logger.debug(f"[ML] IP: {enriched_event.get('source_ip')} | Score: {score:.3f} | Obs: {self.anomaly_detector.observations} | Feats: {features}")
                
                
                # Only alert if we are past the warmup phase AND the score is high
                if self.anomaly_detector.observations >= self.anomaly_detector.warmup_observations and score > self.anomaly_threshold:
                    anomaly_alert = {
                        "rule_name": "ML Anomaly Detected",
                        "severity": "MEDIUM" if score < 0.95 else "HIGH",
                        "source_ip": enriched_event.get("source_ip"),
                        "destination_ip": enriched_event.get("destination_ip"),
                        "description": f"Anomalous behavior detected with score {score:.2f}",
                        "event": enriched_event,
                        "metadata": {
                            "anomaly_score": score,
                            "features": features
                        },
                        "@timestamp": enriched_event.get("timestamp")
                    }
                    
                    logger.warning(f"ANOMALY GENERATED: Score {score:.2f} from {source_topic} | IP: {anomaly_alert.get('source_ip')}")
                    
                    if self.producer and self.anomaly_topic:
                        self.producer.send_alert(
                            topic=self.anomaly_topic,
                            payload=anomaly_alert,
                            key=anomaly_alert.get("source_ip", "unknown")
                        )
                        
                    if self.elastic:
                        self.elastic.index_alert(anomaly_alert)
        