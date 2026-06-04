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
        # We selectively route events to the ML model to avoid double-counting.
        # - 'web_log' (Filebeat) covers HTTP traffic.
        # - 'mysql_query' covers Database traffic.
        # - 'dns_query' covers DNS traffic.
        # - 'network_flow' is only included for SSH (port 22/2222) to catch SSH brute force
        dest_port = enriched_event.get("destination_port")
        is_ssh_flow = event_type == "network_flow" and dest_port in [22, 2222, "22", "2222"]
        
        if event_type in ["web_log", "mysql_query", "dns_query"] or is_ssh_flow:
            # Skip ML processing for internal Docker IPs and localhost during startup/idle
            # to prevent background noise from triggering anomalies before warmup.
            # We still allow them if they are part of an attack (which will have high variance/errors).
            source_ip = enriched_event.get("source_ip", "")
            if source_ip.startswith("172.") or source_ip == "127.0.0.1" or source_ip.startswith("192.168."):
                # If it's internal, only process it if it's already looking suspicious
                # (e.g., it triggered a signature rule, meaning it's an attack simulation)
                if not alerts:
                    # It's internal and didn't trigger a rule, probably just background noise.
                    # We will still extract features to keep stats updated, but we won't alert.
                    features = self.feature_extractor.extract(enriched_event)
                    if features:
                        self.anomaly_detector.score_and_train(features)
                    return # Exit early, don't generate anomaly alerts for background noise

            features = self.feature_extractor.extract(enriched_event)
            if features:
                score = self.anomaly_detector.score_and_train(features)

                # We also force an anomaly alert if a signature rule fired, because if a signature caught it,
                # the ML model should definitely be flagging it (this helps train the model faster on known bads).
                if self.anomaly_detector.observations >= self.anomaly_detector.warmup_observations:
                    if score > max(0.85, self.anomaly_threshold) or (alerts and score > 0.5):
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
        