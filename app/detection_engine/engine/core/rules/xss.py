import re
import urllib.parse
from typing import Dict, Any, Optional

# 1. Define raw patterns
_RAW_XSS_PATTERNS = {
    "Script_Tags": [
        r"<script[^>]*>.*?</script>",
        r"<script[^>]*>",
    ],
    "Event_Handlers": [
        r"\bonerror\s*=",
        r"\bonload\s*=",
        r"\bonmouseover\s*=",
        r"\bonclick\s*=",
        r"\bonfocus\s*=",
    ],
    "URI_Schemes": [
        r"javascript:[^\s]*",
        r"vbscript:[^\s]*",
        r"data:text/html",
    ],
    "DOM_Manipulation": [
        r"document\.cookie",
        r"document\.location",
        r"window\.location",
        r"document\.write",
    ]
}

# 2. Pre-compile patterns
COMPILED_XSS_PATTERNS = {
    category: [re.compile(p, re.IGNORECASE) for p in patterns]
    for category, patterns in _RAW_XSS_PATTERNS.items()
}

# 3. Master Regex for fast rejection
_ALL_PATTERNS = [p for patterns in _RAW_XSS_PATTERNS.values() for p in patterns]
MASTER_XSS_REGEX = re.compile(r"|".join(_ALL_PATTERNS), re.IGNORECASE)

def detect_xss(event: Dict[str, Any], state_store: Any = None) -> Optional[Dict[str, Any]]:
    """
    Stateless rule to detect Cross-Site Scripting (XSS) attempts.
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
    if not MASTER_XSS_REGEX.search(decoded_target):
        return None
        
    # SLOW PATH (only executed if a match is found)
    matched_patterns = []
    categories_hit = []
    
    for category, compiled_patterns in COMPILED_XSS_PATTERNS.items():
        for compiled_pattern in compiled_patterns:
            if compiled_pattern.search(decoded_target):
                matched_patterns.append(compiled_pattern.pattern)
                if category not in categories_hit:
                    categories_hit.append(category)
    
    if matched_patterns:
        return {
            "rule_name": "Cross-Site Scripting (XSS) Detected",
            "severity": "HIGH",
            "source_ip": event.get("source_ip"),
            "destination_ip": event.get("destination_ip"),
            "description": f"Detected XSS. Categories: {', '.join(categories_hit)}",
            "event": event,
            "metadata": {
                "matched_categories": categories_hit,
                "matched_patterns": matched_patterns
            }
        }
            
    return None
