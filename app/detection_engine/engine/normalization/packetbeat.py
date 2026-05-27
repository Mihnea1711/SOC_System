from typing import Dict, Any
from engine.utils.helpers import create_base_normalized_event

def normalize_packetbeat(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts relevant fields from a Packetbeat JSON event.
    """
    normalized = create_base_normalized_event(raw_event)
    
    # Determine specific event type
    event_dataset = raw_event.get("event", {}).get("dataset", "")
    if event_dataset == "http":
        normalized["event_type"] = "http_request"
    elif event_dataset == "flow":
        normalized["event_type"] = "network_flow"
    else:
        normalized["event_type"] = f"packetbeat_{event_dataset}" if event_dataset else "packetbeat_unknown"

    # IPs and Ports
    normalized["source_ip"] = raw_event.get("source", {}).get("ip")
    normalized["destination_ip"] = raw_event.get("destination", {}).get("ip")
    normalized["destination_port"] = raw_event.get("destination", {}).get("port")

    # HTTP Specifics
    if normalized["event_type"] == "http_request":
        normalized["http_method"] = raw_event.get("http", {}).get("request", {}).get("method")
        
        # URL Path
        normalized["url_path"] = raw_event.get("url", {}).get("path")
        
        # User Agent
        normalized["user_agent"] = raw_event.get("user_agent", {}).get("original")
        
        # Status Code
        normalized["status_code"] = raw_event.get("http", {}).get("response", {}).get("status_code")
        
        # Payload extraction (Query string or Form body)
        query = raw_event.get("url", {}).get("query")
        if query:
            normalized["payload"] = query
        else:
            # Packetbeat sometimes puts POST bodies here if configured to capture them
            # (Note: Requires specific packetbeat.yml config to capture bodies)
            request_body = raw_event.get("http", {}).get("request", {}).get("body", {}).get("content")
            if request_body:
                normalized["payload"] = request_body

    return normalized
