from typing import Dict, Any, Optional
from engine.utils.logger import logger
from engine.utils.constants import BEAT_TYPE_PACKETBEAT, BEAT_TYPE_FILEBEAT

from .packetbeat import normalize_packetbeat
from .filebeat import normalize_filebeat

class Normalizer:
    """
    Responsible for converting raw, nested JSON dictionaries from various Beats
    into a standardized, flat dictionary schema for the detection engine.
    
    The output dictionary is guaranteed to have the following keys (though values may be None):
    - timestamp (str)
    - source_ip (str)
    - destination_ip (str)
    - destination_port (int)
    - event_type (str): e.g., 'network_flow', 'http_request', 'web_log'
    - http_method (str)
    - url_path (str)
    - user_agent (str)
    - status_code (int)
    - payload (str): e.g., form data, query string
    - raw_event (dict): The original un-normalized event for reference/evidence
    """
    
    def __init__(self):
        logger.info("Normalizer initialized.")

    def normalize(self, raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Routes the raw event to the appropriate specific normalizer based on the beat type.
        
        Args:
            raw_event: The raw JSON dictionary from Kafka.
            
        Returns:
            A standardized dictionary, or None if the event could not be normalized 
            (e.g., unrecognized beat type or malformed data).
        """
        try:
            # Determine the source of the event
            beat_type = raw_event.get("@metadata", {}).get("beat")
            
            if not beat_type:
                # Try fallback if @metadata is missing
                agent_type = raw_event.get("agent", {}).get("type")
                if agent_type:
                    beat_type = agent_type
            
            if beat_type == BEAT_TYPE_PACKETBEAT:
                return normalize_packetbeat(raw_event)
            elif beat_type == BEAT_TYPE_FILEBEAT:
                return normalize_filebeat(raw_event)
            else:
                logger.warning(f"Unknown beat type encountered: {beat_type}. Skipping normalization.")
                return None
                
        except Exception as e:
            logger.error(f"Error during normalization: {e}", exc_info=True)
            return None

