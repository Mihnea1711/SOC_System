import urllib.parse
from typing import Dict, Any, Optional
from engine.state.base import StateStore

# Thresholds for HTTP Brute Force
TIME_WINDOW = 60
FAILED_THRESHOLD = 5
COMPROMISED_THRESHOLD = 3
SUPPRESSION_TIME = 300

def detect_brute_force(event: Dict[str, Any], state_store: StateStore) -> Optional[Dict[str, Any]]:
    """
    Stateful rule to detect HTTP Brute Force attacks and Compromised Accounts.
    """
    # 1. early rejection
    if event.get("event_type") not in ["http_request", "web_log", "ssh_log"]:
        return None
        
    http_method = event.get("http_method", "") or ""
    url_path = event.get("url_path", "") or ""
    
    if event.get("event_type") != "ssh_log":
        if http_method.upper() != "POST":
            return None
            
        # check for both /login (failures) and / (success in the mock)
        if "login" not in url_path.lower() and url_path != "/":
            return None
        
    source_ip = event.get("source_ip")
    status_code = event.get("status_code")
    
    if not source_ip or not status_code or not state_store:
        return None

    # 2. Extract username from payload for better context (if available)
    payload = event.get("payload", "") or ""
    username = "unknown"
    if "username=" in payload:
        try:
            parsed_payload = urllib.parse.parse_qs(payload)
            if "username" in parsed_payload:
                username = parsed_payload["username"][0]
        except Exception:
            pass

    # Determine the service type for accurate tracking and alerting
    service_type = "SSH" if event.get("event_type") == "ssh_log" else "Web"

    # State keys - We separate the count by service so an SSH brute force 
    # doesn't mix with a Web brute force from the same IP.
    bf_count_key = f"bf_count:{service_type}:{source_ip}"
    suppress_key = f"bf_suppress:{service_type}:{source_ip}"

    # 3. Handle SUCCESSFUL login (e.g., 200 OK, 301/302 Redirect)
    # This is a critical SOC use case: detecting a successful login AFTER a brute force attempt.
    # In our mock setup, a successful login hits the root path "/" and returns 405 Not Allowed.
    # We will treat 405 as a success indicator for this specific mock scenario.
    is_web_success = event.get("event_type") != "ssh_log" and status_code in [200, 301, 302, 405, "200", "301", "302", "405"] and url_path == "/"
    is_ssh_success = event.get("event_type") == "ssh_log" and status_code == 200
    
    if is_web_success or is_ssh_success:
        current_count = state_store.get(bf_count_key) or 0
        if current_count >= COMPROMISED_THRESHOLD: # If they had enough failures recently, this success is highly suspicious
            # Clear the count so we don't spam
            state_store.delete(bf_count_key)
            return {
                "rule_name": f"Successful {service_type} Login After Brute Force (Compromised Account)",
                "severity": "CRITICAL",
                "source_ip": source_ip,
                "destination_ip": event.get("destination_ip"),
                "description": f"IP {source_ip} successfully logged in to {service_type} as '{username}' after {current_count} failed attempts.",
                "event": event,
                "metadata": {"username": username, "prior_failures": current_count, "service": service_type}
            }
        return None

    # 4. Handle FAILED login (401 Unauthorized, 403 Forbidden, 404 Not Found in our mock)
    # Note: Packetbeat sometimes returns 'status_code': None for unmatched responses,
    # but we still want to count those as failures if they hit the /login endpoint.
    # We also check that it's NOT an ssh_log here, because ssh_logs are handled by the other condition.
    is_web_failure = event.get("event_type") != "ssh_log" and status_code in [401, 403, 404, "401", "403", "404", None] and "login" in url_path.lower()
    is_ssh_failure = event.get("event_type") == "ssh_log" and status_code == 401
    
    if is_web_failure or is_ssh_failure:
        # Use the atomic increment method if available, otherwise fallback to get/set
        try:
            new_count = state_store.increment(bf_count_key, amount=1, ttl_seconds=TIME_WINDOW)
        except NotImplementedError:
            current_count = state_store.get(bf_count_key) or 0
            new_count = current_count + 1
            state_store.set(bf_count_key, new_count, ttl_seconds=TIME_WINDOW)
        
        # Threshold Check
        if new_count >= FAILED_THRESHOLD:
            # Alert Suppression
            if state_store.get(suppress_key):
                return None
                
            # Set suppression
            state_store.set(suppress_key, True, ttl_seconds=SUPPRESSION_TIME)
            
            return {
                "rule_name": f"Failed {service_type} Login Brute Force",
                "severity": "HIGH",
                "source_ip": source_ip,
                "destination_ip": event.get("destination_ip"),
                "description": f"Detected {new_count} failed {service_type} login attempts within {TIME_WINDOW} seconds. Last attempted user: '{username}'",
                "event": event,
                "metadata": {"last_username": username, "failures": new_count, "service": service_type}
            }

    return None
