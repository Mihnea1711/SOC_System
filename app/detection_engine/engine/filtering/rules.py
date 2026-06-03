from typing import Dict, Any
from engine.utils.constants import UBUNTU_CONNECTIVITY_DOMAIN, FIREFOX_DETECTPORTAL_DOMAIN

def filter_ubuntu_connectivity(event: Dict[str, Any]) -> bool:
    """
    Filters out background connectivity checks made by Ubuntu to `connectivity-check.ubuntu.com`.
    """
    try:
        # Check if it's a packetbeat HTTP event
        if event.get("type") == "http" or event.get("event", {}).get("dataset") == "http":
            domain = event.get("destination", {}).get("domain", "")
            if domain == UBUNTU_CONNECTIVITY_DOMAIN:
                return True
            
            # Sometimes it's in the url object
            url_domain = event.get("url", {}).get("domain", "")
            if url_domain == UBUNTU_CONNECTIVITY_DOMAIN:
                return True
                
            # Sometimes it's in the server object
            server_domain = event.get("server", {}).get("domain", "")
            if server_domain == UBUNTU_CONNECTIVITY_DOMAIN:
                return True
    except Exception:
        pass
    return False

def filter_firefox_detectportal(event: Dict[str, Any]) -> bool:
    """
    Filters out background captive portal checks made by Firefox to `detectportal.firefox.com`.
    """
    try:
        if event.get("type") == "http" or event.get("event", {}).get("dataset") == "http":
            domain = event.get("destination", {}).get("domain", "")
            if domain == FIREFOX_DETECTPORTAL_DOMAIN:
                return True
                
            url_domain = event.get("url", {}).get("domain", "")
            if url_domain == FIREFOX_DETECTPORTAL_DOMAIN:
                return True
                
            server_domain = event.get("server", {}).get("domain", "")
            if server_domain == FIREFOX_DETECTPORTAL_DOMAIN:
                return True
    except Exception:
        pass
    return False

def filter_static_assets(event: Dict[str, Any]) -> bool:
    """
    Filters out requests for common static web assets (css, js, images).
    This acts as a defense-in-depth layer behind the Filebeat/Packetbeat drop_event processors.
    """
    try:
        # Check Filebeat Nginx logs
        message = event.get("message", "")
        if message:
            # A very simple check for static extensions in the raw log line
            static_extensions = [".css", ".js", ".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg", ".woff", ".woff2"]
            if any(ext in message.lower() for ext in static_extensions):
                return True
                
        # Check Packetbeat HTTP paths
        url_path = event.get("url", {}).get("path", "")
        if url_path:
            static_extensions = [".css", ".js", ".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg", ".woff", ".woff2"]
            if any(url_path.lower().endswith(ext) for ext in static_extensions):
                return True
    except Exception:
        pass
    return False

def filter_nginx_internal_notices(event: Dict[str, Any]) -> bool:
    """
    Filters out Nginx internal startup, shutdown, and worker process notices.
    These are logged to error.log but are not security relevant.
    """
    try:
        message = event.get("message")
        if not isinstance(message, str):
            return False
            
        # Check if it's an Nginx [notice] log
        if "[notice]" in message:
            # Common internal Nginx messages
            internal_patterns = [
                "start worker process",
                "shutting down",
                "exiting",
                "exit",
                "built by gcc",
                "using the \"epoll\" event method",
                "getrlimit(RLIMIT_NOFILE)",
                "signal",
                "OS: Linux",
                "nginx/"
            ]
            if any(pattern in message for pattern in internal_patterns):
                return True
    except Exception:
        pass
    return False

def filter_nginx_not_found_errors(event: Dict[str, Any]) -> bool:
    """
    Filters out Nginx error.log entries for 'No such file or directory' (404s).
    These are redundant because we already capture the 404 event via the Nginx access.log 
    and Packetbeat, which provide more complete information.
    """
    try:
        message = event.get("message")
        if not isinstance(message, str):
            return False
            
        if "[error]" in message and "failed (2: No such file or directory)" in message:
            return True
    except Exception:
        pass
    return False

def filter_packetbeat_unmatched_responses(event: Dict[str, Any]) -> bool:
    """
    Filters out Packetbeat HTTP events that are 'Unmatched response'.
    These events lack the request context (method, url, payload) and only contain
    the response (e.g., 404 Not Found), making them useless for detection.
    """
    try:
        # Check if it's a packetbeat HTTP event
        if event.get("type") == "http" or event.get("event", {}).get("dataset") == "http":
            error_obj = event.get("error", {})
            error_msg = error_obj.get("message")
            
            if not error_msg:
                return False
                
            # error.message can be a string or a list of strings
            if isinstance(error_msg, str):
                if "Unmatched response" in error_msg:
                    return True
            elif isinstance(error_msg, list):
                if any("Unmatched response" in msg for msg in error_msg):
                    return True
                
        # Check if it's a packetbeat DNS event with "No response" error
        if event.get("type") == "dns" or event.get("event", {}).get("dataset") == "dns":
            error_obj = event.get("error", {})
            error_msg = error_obj.get("message")
            
            if not error_msg:
                return False
                
            if isinstance(error_msg, str):
                if "No response to this query" in error_msg or "Another query with the same DNS ID" in error_msg:
                    # We ONLY want to drop these errors if they are noise.
                    return False
            elif isinstance(error_msg, list):
                if any("No response to this query" in msg or "Another query with the same DNS ID" in msg for msg in error_msg):
                    return False
                
    except Exception:
        pass
    return False

def filter_dns_noise(event: Dict[str, Any]) -> bool:
    """
    Filters out background DNS noise like mDNS and local network resolution.
    """
    try:
        if event.get("type") == "dns" or event.get("event", {}).get("dataset") == "dns":
            # Check destination port (5353 is mDNS)
            dest_port = event.get("destination", {}).get("port")
            if dest_port == 5353:
                return True
                
            # Check query name
            query_name = event.get("dns", {}).get("question", {}).get("name", "")
            if not query_name:
                return False
                
            noise_patterns = [
                ".local",
                ".arpa",
                "dns_server",
                "microsoft.com",
                "ubuntu.com",
                "location.services.mozilla.com"
            ]
            
            if any(pattern in query_name for pattern in noise_patterns):
                return True
    except Exception:
        pass
    return False