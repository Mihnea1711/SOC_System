from typing import Dict, Any, Optional
from engine.utils.logger import logger

def detect_dns_tunneling(event: Dict[str, Any], state_store: Any = None) -> Optional[Dict[str, Any]]:
    """
    Stateless rule to detect DNS Tunneling (Data Exfiltration).
    Flags unusually long subdomains which are typical of encoded data.
    """
    if event.get("event_type") != "dns_query":
        return None
        
    query = event.get("payload", "")
    if not query:
        return None

    # Check if the query string is unusually long.
    # Typical tunneling looks like: <base64_encoded_data>.attacker.com
    # Legitimate domains rarely have single labels longer than 30-40 characters, 
    # and the total length is usually short.
    
    # Simple heuristic: if the total query length is > 60 chars, it's highly suspicious
    if len(query) > 60:
        return {
            "rule_name": "Suspicious DNS Query (Potential Tunneling)",
            "severity": "HIGH",
            "source_ip": event.get("source_ip"),
            "destination_ip": event.get("destination_ip"),
            "description": f"Detected an unusually long DNS query ({len(query)} chars), indicating potential data exfiltration.",
            "event": event,
            "metadata": {"query": query, "length": len(query)}
        }
        
    return None
