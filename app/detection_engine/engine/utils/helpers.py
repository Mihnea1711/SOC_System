from typing import Dict, Any
from datetime import datetime, timezone

def create_base_normalized_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper to create the guaranteed schema with default None values.
    This ensures all detection rules can safely access these keys without KeyErrors.
    """
    return {
        "timestamp": raw_event.get("@timestamp", datetime.now(timezone.utc).isoformat()),
        "source_ip": None,
        "destination_ip": None,
        "destination_port": None,
        "event_type": "unknown",
        "http_method": None,
        "url_path": None,
        "user_agent": None,
        "status_code": None,
        "payload": None,
        "raw_event": raw_event
    }
