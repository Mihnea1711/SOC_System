import re
import urllib.parse
from typing import Dict, Any, Optional

# 1. Define raw patterns
_RAW_SQLI_PATTERNS = {
    "Tautology": [
        r"\b(or|and)\b\s+\d+=\d+",                  
        r"\b(or|and)\b\s+['\"][^'\"]+['\"]=['\"][^'\"]+['\"]", 
        r"\b(or|and)\b\s+true\b"                    
    ],
    "Union_Based": [
        r"union\s+(all\s+)?select",                 
    ],
    "Error_Based": [
        r"extractvalue\s*\(",                       
        r"updatexml\s*\(",                          
    ],
    "Blind_Time_Based": [
        r"waitfor\s+delay\s+['\"][^'\"]+['\"]",     
        r"pg_sleep\s*\(",                           
        r"\bsleep\s*\(",                            
    ],
    "System_Commands": [
        r"xp_cmdshell",                             
        r"exec\s+master\.\.xp_cmdshell",
    ],
    "Information_Schema": [
        r"information_schema\.tables",              
        r"information_schema\.columns",
    ],
    "Inline_Comments": [
        r"/\*.*\*/",                                
        r"--\s*$",                                      
        r";\s*--"
    ],
    "Dangerous_Keywords": [
        r";\s*drop\s+table",
        r";\s*truncate\s+table",
        r";\s*alter\s+table",
    ]
}

# 2. Pre-compile patterns at module load time for maximum performance
COMPILED_SQLI_PATTERNS = {
    category: [re.compile(p, re.IGNORECASE) for p in patterns]
    for category, patterns in _RAW_SQLI_PATTERNS.items()
}

# 3. Create a single MASTER regex for ultra-fast early rejection
# This combines all patterns into one: (pattern1|pattern2|pattern3)
_ALL_PATTERNS = [p for patterns in _RAW_SQLI_PATTERNS.values() for p in patterns]
MASTER_SQLI_REGEX = re.compile(r"|".join(_ALL_PATTERNS), re.IGNORECASE)

def detect_sqli(event: Dict[str, Any], state_store: Any = None) -> Optional[Dict[str, Any]]:
    """
    Stateless rule to detect SQL Injection attempts in URL or payload.
    Highly optimized using pre-compiled regexes and a master fast-rejection regex.
    """
    if event.get("event_type") not in ["http_request", "web_log"]:
        return None
        
    url_path = event.get("url_path", "") or ""
    payload = event.get("payload", "") or ""
    
    # Combine and normalize
    raw_target = f"{url_path} {payload}"
    
    # URL Decode
    decoded_target = urllib.parse.unquote(raw_target)
    
    # ULTRA-FAST PATH: Check the master regex first.
    # If this fails (which it will for 99.9% of normal traffic), we return immediately.
    if not MASTER_SQLI_REGEX.search(decoded_target):
        return None
        
    # SLOW PATH: We only reach here if the master regex found a match.
    # Now we iterate through the compiled categories to find exactly what triggered it.
    matched_patterns = []
    categories_hit = []
    
    for category, compiled_patterns in COMPILED_SQLI_PATTERNS.items():
        for compiled_pattern in compiled_patterns:
            if compiled_pattern.search(decoded_target):
                matched_patterns.append(compiled_pattern.pattern)
                if category not in categories_hit:
                    categories_hit.append(category)
    
    if matched_patterns:
        # Dynamic severity
        severity = "HIGH"
        if "System_Commands" in categories_hit or "Dangerous_Keywords" in categories_hit:
            severity = "CRITICAL"
            
        return {
            "rule_name": "SQL Injection Detected",
            "severity": severity,
            "source_ip": event.get("source_ip"),
            "destination_ip": event.get("destination_ip"),
            "description": f"Detected SQLi. Categories: {', '.join(categories_hit)}",
            "event": event,
            "metadata": {
                "matched_categories": categories_hit,
                "matched_patterns": matched_patterns
            }
        }
        
    return None
