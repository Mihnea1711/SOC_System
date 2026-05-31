from elasticsearch import Elasticsearch, exceptions
from engine.utils.config import settings
from engine.utils.logger import logger
from datetime import datetime, timezone

class ElasticsearchClient:
    def __init__(self):
        self.hosts = settings.elasticsearch['hosts']
        self.alert_index = settings.elasticsearch.get('alert_index', 'alerts-detection')
        self.client = None

    def connect(self):
        """Initialize the Elasticsearch client."""
        try:
            self.client = Elasticsearch(
                hosts=self.hosts,
                request_timeout=10,
                max_retries=3,
                retry_on_timeout=True
            )
            # Ping the cluster to verify connection
            if self.client.ping():
                info = self.client.info()
                logger.info(f"Successfully connected to Elasticsearch at {self.hosts}. Cluster info: {info.get('cluster_name')}")
            else:
                logger.error(f"Could not ping Elasticsearch at {self.hosts}. Attempting info() to get error details...")
                # This will likely throw an exception with the actual error reason
                self.client.info()
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch client: {e}")
            self.client = None

    def index_document(self, index_name: str, document: dict):
        """
        Index a single document into Elasticsearch.
        
        Args:
            index_name (str): The target index (e.g., 'alerts-detection', 'logs-enriched').
            document (dict): The document payload to store.
        """
        if not self.client:
            self.connect()

        if not self.client:
            logger.warning("Elasticsearch client is not connected. Document not indexed.")
            return False

        try:
            # Ensure the document has a timestamp if it doesn't already
            if "@timestamp" not in document:
                document["@timestamp"] = datetime.now(timezone.utc).isoformat()

            response = self.client.index(index=index_name, document=document)
            
            # logger.debug(f"Successfully indexed document to {index_name}. ID: {response.get('_id')}")
            return True

        except exceptions.ConnectionError as e:
            logger.error(f"Elasticsearch connection error while indexing: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while indexing document to {index_name}: {e}")
        
        return False

    def index_alert(self, alert_payload: dict):
        """Helper to specifically index an alert into the configured alerts index."""
        return self.index_document(self.alert_index, alert_payload)

    def close(self):
        """Cleanly close the Elasticsearch connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("Elasticsearch connection closed cleanly.")
            except Exception as e:
                logger.error(f"Error while closing Elasticsearch client: {e}")
