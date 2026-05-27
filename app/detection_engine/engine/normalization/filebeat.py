import re
from typing import Dict, Any
from engine.utils.helpers import create_base_normalized_event
from engine.utils.constants import FILEBEAT_LOG_ACCESS, FILEBEAT_LOG_ERROR

# Regex to parse standard Nginx combined access log format
# Example: 172.20.0.1 - - [27/May/2026:00:39:36 +0000] "POST /login HTTP/1.1" 404 153 "-" "Hydra/0.1 (Brute Force Tool)" "-"
NGINX_ACCESS_REGEX = re.compile(
    r'(?P<ip>\S+)\s+\S+\s+\S+\s+\[.*?\]\s+"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+(?P<status>\d+)\s+\S+\s+".*?"\s+"(?P<user_agent>.*?)"'
)

def normalize_filebeat(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts relevant fields from a Filebeat JSON event (specifically Nginx logs).
    """
    normalized = create_base_normalized_event(raw_event)
    normalized["event_type"] = "web_log"
    
    message = raw_event.get("message", "")
    if not message:
        return normalized

    # Check if it's an access log or error log based on file path
    log_path = raw_event.get("log", {}).get("file", {}).get("path", "")
    
    if FILEBEAT_LOG_ACCESS in log_path:
        # Parse access log
        match = NGINX_ACCESS_REGEX.search(message)
        if match:
            data = match.groupdict()
            normalized["source_ip"] = data.get("ip")
            normalized["http_method"] = data.get("method")
            normalized["url_path"] = data.get("path")
            
            status = data.get("status")
            if status and status.isdigit():
                normalized["status_code"] = int(status)
                
            normalized["user_agent"] = data.get("user_agent")
            
            # We assume Nginx is running on 80 or 8080. 
            # Filebeat doesn't natively know the destination port from standard access logs unless configured.
            normalized["destination_port"] = 8080 
            
    elif FILEBEAT_LOG_ERROR in log_path:
        # Error logs are less structured, but we can try to extract IP if present
        # Example: ... client: 172.20.0.1, server: localhost, request: "POST /login HTTP/1.1" ...
        ip_match = re.search(r'client:\s+(?P<ip>\d+\.\d+\.\d+\.\d+)', message)
        if ip_match:
            normalized["source_ip"] = ip_match.group("ip")
            
        request_match = re.search(r'request:\s+"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"', message)
        if request_match:
            normalized["http_method"] = request_match.group("method")
            normalized["url_path"] = request_match.group("path")

    return normalized