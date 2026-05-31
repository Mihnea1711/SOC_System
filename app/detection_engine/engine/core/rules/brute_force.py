import urllib.parse
from typing import Dict, Any, Optional
from engine.state.base import StateStore
from engine.utils.config import settings

# Load thresholds from config, fallback to defaults
BF_CONFIG = getattr(settings, 'rules', {}).get('brute_force', {})
TIME_WINDOW = BF_CONFIG.get('time_window_seconds', 60)
FAILED_THRESHOLD = BF_CONFIG.get('failed_attempts_threshold', 5)
COMPROMISED_THRESHOLD = BF_CONFIG.get('compromised_account_threshold', 3)
SUPPRESSION_TIME = BF_CONFIG.get('suppression_time_seconds', 300)

def detect_brute_force(event: Dict[str, Any], state_store: StateStore) -> Optional[Dict[str, Any]]:
    """
    Stateful rule to detect HTTP Brute Force attacks and Compromised Accounts.
    """
    # 1. Ultra-fast early rejection
    if event.get("event_type") not in ["http_request", "web_log"]:
        return None
        
    http_method = event.get("http_method", "") or ""
    if http_method.upper() != "POST":
        return None
        
    url_path = event.get("url_path", "") or ""
    # We check for both /login (failures) and / (success in our mock)
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

    # State keys
    bf_count_key = f"bf_count:{source_ip}"
    suppress_key = f"bf_suppress:{source_ip}"

    # 3. Handle SUCCESSFUL login (e.g., 200 OK, 301/302 Redirect)
    # This is a critical SOC use case: detecting a successful login AFTER a brute force attempt.
    # In our mock setup, a successful login hits the root path "/" and returns 405 Not Allowed.
    # We will treat 405 as a success indicator for this specific mock scenario.
    if status_code in [200, 301, 302, 405, "200", "301", "302", "405"] and url_path == "/":
        current_count = state_store.get(bf_count_key) or 0
        if current_count >= COMPROMISED_THRESHOLD: # If they had enough failures recently, this success is highly suspicious
            # Clear the count so we don't spam
            state_store.delete(bf_count_key)
            return {
                "rule_name": "Successful Login After Brute Force (Compromised Account)",
                "severity": "CRITICAL",
                "source_ip": source_ip,
                "destination_ip": event.get("destination_ip"),
                "description": f"IP {source_ip} successfully logged in as '{username}' after {current_count} failed attempts.",
                "event": event,
                "metadata": {"username": username, "prior_failures": current_count}
            }
        return None

    # 4. Handle FAILED login (401 Unauthorized, 403 Forbidden, 404 Not Found in our mock)
    # Note: Packetbeat sometimes returns 'status_code': None for unmatched responses,
    # but we still want to count those as failures if they hit the /login endpoint.
    if status_code in [401, 403, 404, "401", "403", "404", None] and "login" in url_path.lower():
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
                "rule_name": "Failed Login Brute Force",
                "severity": "HIGH",
                "source_ip": source_ip,
                "destination_ip": event.get("destination_ip"),
                "description": f"Detected {new_count} failed login attempts within {TIME_WINDOW} seconds. Last attempted user: '{username}'",
                "event": event,
                "metadata": {"last_username": username, "failures": new_count}
            }

    return None
