import re
from typing import Dict, Any
from engine.utils.helpers import create_base_normalized_event
from engine.utils.constants import FILEBEAT_LOG_ACCESS, FILEBEAT_LOG_ERROR, FILEBEAT_LOG_SSH

# Regex to parse standard Nginx combined access log format
# Example: 172.20.0.1 - - [27/May/2026:00:39:36 +0000] "POST /login HTTP/1.1" 404 153 "-" "Hydra/0.1 (Brute Force Tool)" "-"
NGINX_ACCESS_REGEX = re.compile(
    r'(?P<ip>\S+)\s+\S+\s+\S+\s+\[.*?\]\s+"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+(?P<status>\d+)\s+\S+\s+".*?"\s+"(?P<user_agent>.*?)"'
)

# Regex to parse SSH logs from linuxserver/openssh-server
# Example: 2026-06-02 14:26:48.070801293  Failed password for admin from 172.20.0.1 port 57920 ssh2
# Example: 2026-06-02 14:26:48.174289513  Connection closed by authenticating user admin 172.20.0.1 port 57920 [preauth]
# Example: 2026-06-02 14:26:48.070801293  Accepted password for admin from 172.20.0.1 port 57920 ssh2
SSH_LOG_REGEX = re.compile(
    r'(?P<status>Failed|Accepted)\s+password\s+for\s+(?:invalid user\s+)?(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)'
)

def normalize_filebeat(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts relevant fields from a Filebeat JSON event (Nginx logs, SSH logs).
    """
    normalized = create_base_normalized_event(raw_event)
    
    message = raw_event.get("message", "")
    if not message:
        return normalized

    # Check if it's an access log or error log based on file path
    log_path = raw_event.get("log", {}).get("file", {}).get("path", "")
    
    if FILEBEAT_LOG_ACCESS in log_path:
        normalized["event_type"] = "web_log"
        normalized["destination_ip"] = "nginx_server"

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
            normalized["destination_port"] = 8080 
            
    elif FILEBEAT_LOG_ERROR in log_path:
        normalized["event_type"] = "web_log"
        normalized["destination_ip"] = "nginx_server"

        # Error logs are less structured, but we can try to extract IP if present
        ip_match = re.search(r'client:\s+(?P<ip>\d+\.\d+\.\d+\.\d+)', message)
        if ip_match:
            normalized["source_ip"] = ip_match.group("ip")
            
        request_match = re.search(r'request:\s+"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"', message)
        if request_match:
            normalized["http_method"] = request_match.group("method")
            normalized["url_path"] = request_match.group("path")

    elif FILEBEAT_LOG_SSH in log_path:
        normalized["event_type"] = "ssh_log"
        normalized["destination_port"] = 2222
        normalized["destination_ip"] = "ssh_server"

        match = SSH_LOG_REGEX.search(message)
        if match:
            data = match.groupdict()
            normalized["source_ip"] = data.get("ip")
            # We map "Failed" to 401 and "Accepted" to 200 so we can reuse logic easily, 
            # or we can just pass the string. Let's use status_code for consistency.
            normalized["status_code"] = 200 if data.get("status") == "Accepted" else 401
            # We put the username in the payload so the rules can extract it
            normalized["payload"] = f"username={data.get('user')}"

    return normalized