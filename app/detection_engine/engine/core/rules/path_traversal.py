import re
import urllib.parse
from typing import Dict, Any, Optional

# 1. Define raw patterns
_RAW_TRAVERSAL_PATTERNS = {
    "Relative_Paths": [
        r"\.\./\.\./",
        r"\.\.\\\.\.\\",
    ],
    "Encoded_Paths": [
        r"%2e%2e%2f",
        r"%2e%2e/",
        r"\.\.%2f",
        r"%252e%252e%252f", # Double encoded
    ],
    "Sensitive_Linux_Files": [
        r"etc/passwd",
        r"etc/shadow",
        r"etc/hosts",
        r"var/log/",
        r"proc/self/environ",
    ],
    "Sensitive_Windows_Files": [
        r"windows\\system32",
        r"cmd\.exe",
        r"boot\.ini",
    ]
}

# 2. Pre-compile patterns
COMPILED_TRAVERSAL_PATTERNS = {
    category: [re.compile(p, re.IGNORECASE) for p in patterns]
    for category, patterns in _RAW_TRAVERSAL_PATTERNS.items()
}

# 3. Master Regex for fast rejection
_ALL_PATTERNS = [p for patterns in _RAW_TRAVERSAL_PATTERNS.values() for p in patterns]
MASTER_TRAVERSAL_REGEX = re.compile(r"|".join(_ALL_PATTERNS), re.IGNORECASE)

def detect_path_traversal(event: Dict[str, Any], state_store: Any = None) -> Optional[Dict[str, Any]]:
    """
    Stateless rule to detect Path/Directory Traversal attempts.
    Highly optimized using pre-compiled regexes and a master fast-rejection regex.
    """
    # state_store is not used in this stateless rule, but required by the RULES interface
    _ = state_store
    if event.get("event_type") not in ["http_request", "web_log"]:
        return None
        
    url_path = event.get("url_path", "") or ""
    payload = event.get("payload", "") or ""
    
    raw_target = f"{url_path} {payload}"
    decoded_target = urllib.parse.unquote(raw_target)
    
    # ULTRA-FAST PATH
    if not MASTER_TRAVERSAL_REGEX.search(decoded_target):
        return None
        
    # SLOW PATH
    matched_patterns = []
    categories_hit = []
    
    for category, compiled_patterns in COMPILED_TRAVERSAL_PATTERNS.items():
        for compiled_pattern in compiled_patterns:
            if compiled_pattern.search(decoded_target):
                matched_patterns.append(compiled_pattern.pattern)
                if category not in categories_hit:
                    categories_hit.append(category)
    
    if matched_patterns:
        severity = "HIGH"
        if "Sensitive_Linux_Files" in categories_hit or "Sensitive_Windows_Files" in categories_hit:
            severity = "CRITICAL"
            
        return {
            "rule_name": "Path Traversal Detected",
            "severity": severity,
            "source_ip": event.get("source_ip"),
            "destination_ip": event.get("destination_ip"),
            "description": f"Detected Path Traversal. Categories: {', '.join(categories_hit)}",
            "event": event,
            "metadata": {
                "matched_categories": categories_hit,
                "matched_patterns": matched_patterns
            }
        }
            
    return None
