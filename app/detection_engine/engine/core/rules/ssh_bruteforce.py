from typing import Dict, Any, Optional
from engine.state.base import StateStore

# Thresholds for SSH Brute Force
TIME_WINDOW = 60
FAILED_THRESHOLD = 10
SUPPRESSION_TIME = 300

def detect_ssh_brute_force(event: Dict[str, Any], state_store: StateStore) -> Optional[Dict[str, Any]]:
    """
    Stateful rule to detect SSH Brute Force attacks based on network flows.
    Since SSH is encrypted, we rely on the volume of TCP connections to port 22/2222.
    """
    # 1. Early rejection
    if event.get("event_type") != "network_flow":
        return None
        
    destination_port = event.get("destination_port")
    if destination_port not in [22, 2222]:
        return None
        
    source_ip = event.get("source_ip")
    if not source_ip or not state_store:
        return None

    # State keys
    # Note: We use "ssh_bf_count" here, which is different from "bf_count:SSH" used in brute_force.py.
    # This rule tracks raw TCP connections (network_flow), while brute_force.py tracks actual failed logins (ssh_log).
    ssh_count_key = f"ssh_flow_bf_count:{source_ip}"
    suppress_key = f"ssh_flow_bf_suppress:{source_ip}"

    # 2. Count the flow
    try:
        new_count = state_store.increment(ssh_count_key, amount=1, ttl_seconds=TIME_WINDOW)
    except NotImplementedError:
        current_count = state_store.get(ssh_count_key) or 0
        new_count = current_count + 1
        state_store.set(ssh_count_key, new_count, ttl_seconds=TIME_WINDOW)
    
    # 3. Threshold Check
    if new_count >= FAILED_THRESHOLD:
        # Alert Suppression
        if state_store.get(suppress_key):
            return None
            
        # Set suppression
        state_store.set(suppress_key, True, ttl_seconds=SUPPRESSION_TIME)
        
        return {
            "rule_name": "SSH Brute Force Detected",
            "severity": "HIGH",
            "source_ip": source_ip,
            "destination_ip": event.get("destination_ip"),
            "description": f"Detected {new_count} rapid SSH connections to port {destination_port} within {TIME_WINDOW} seconds.",
            "event": event,
            "metadata": {"connection_count": new_count, "target_port": destination_port}
        }

    return None
