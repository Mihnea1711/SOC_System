from typing import Dict, Any, Optional
import re
from engine.utils.logger import logger

# Common suspicious SQL keywords used in data exfiltration or reconnaissance
SUSPICIOUS_KEYWORDS = [
    r"mysqldump",
    r"INTO OUTFILE",
    r"INTO DUMPFILE",
    r"LOAD DATA INFILE",
    r"UNION SELECT",
    r"INFORMATION_SCHEMA",
    r"xp_cmdshell"
]

# Compile regexes for performance
SUSPICIOUS_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_KEYWORDS]

def detect_mysql_exfiltration(event: Dict[str, Any], state_store: Any = None) -> Optional[Dict[str, Any]]:
    """
    Stateless rule to detect suspicious MySQL queries that indicate 
    data exfiltration or lateral movement.
    """
    if event.get("event_type") != "mysql_query":
        return None
        
    query = event.get("payload", "")
    if not query:
        return None

    # 1. Check for massive SELECT * queries (simple heuristic)
    # A query like "SELECT * FROM users" without a LIMIT is highly suspicious in production.
    if re.search(r"SELECT\s+\*\s+FROM\s+[`'\"]?[a-zA-Z0-9_]+[`'\"]?(?!\s+WHERE|\s+LIMIT)", query, re.IGNORECASE):
        return {
            "rule_name": "Suspicious MySQL Query (Unbounded SELECT)",
            "severity": "MEDIUM",
            "source_ip": event.get("source_ip"),
            "destination_ip": event.get("destination_ip"),
            "description": "Detected an unbounded SELECT * query, potential data exfiltration attempt.",
            "event": event,
            "metadata": {"query": query}
        }

    # 2. Check for explicitly malicious keywords
    matched_patterns = []
    for regex in SUSPICIOUS_REGEXES:
        if regex.search(query):
            matched_patterns.append(regex.pattern)

    if matched_patterns:
        return {
            "rule_name": "Malicious MySQL Query (Data Exfiltration)",
            "severity": "HIGH",
            "source_ip": event.get("source_ip"),
            "destination_ip": event.get("destination_ip"),
            "description": f"Detected suspicious SQL keywords: {', '.join(matched_patterns)}",
            "event": event,
            "metadata": {"query": query, "matched_patterns": matched_patterns}
        }

    return None
