from typing import Dict, Any
from engine.utils.helpers import create_base_normalized_event
from engine.utils.logger import logger

def normalize_packetbeat(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts relevant fields from a Packetbeat JSON event.
    """
    normalized = create_base_normalized_event(raw_event)
    
    # Determine specific event type
    event_dataset = raw_event.get("event", {}).get("dataset", "")
    network_protocol = raw_event.get("network", {}).get("protocol", "")
    if event_dataset == "http":
        normalized["event_type"] = "http_request"
    elif event_dataset == "flow":
        normalized["event_type"] = "network_flow"
    elif event_dataset == "mysql" or network_protocol == "mysql":
        normalized["event_type"] = "mysql_query"
    elif event_dataset == "dns" or network_protocol == "dns":
        normalized["event_type"] = "dns_query"
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

    # MySQL Specifics
    elif normalized["event_type"] == "mysql_query":
        # Packetbeat extracts the raw SQL query string
        # Sometimes it's under mysql.query, sometimes under mysql.query.text depending on the beat version
        query = raw_event.get("query")
        if not query:
            query = raw_event.get("mysql", {}).get("query")
            
        if isinstance(query, dict):
            normalized["payload"] = query.get("text")
        else:
            normalized["payload"] = query

        # Also try to extract from 'method' which sometimes holds the query type
        if not normalized["payload"]:
            normalized["payload"] = raw_event.get("method")

    # DNS Specifics
    elif normalized["event_type"] == "dns_query":
        # Extract the queried domain name
        # Packetbeat 8.x/9.x usually puts it in dns.question.name
        normalized["payload"] = raw_event.get("dns", {}).get("question", {}).get("name")
        
        # Fallback for older beats or different configurations
        if not normalized["payload"]:
            # Sometimes it's a list if multiple questions are asked
            questions = raw_event.get("dns", {}).get("questions", [])
            if questions and len(questions) > 0:
                normalized["payload"] = questions[0].get("name")
                
        if not normalized["payload"]:
            normalized["payload"] = raw_event.get("query")
            
    return normalized
