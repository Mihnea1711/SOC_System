# Detection Rules

This directory contains the signature-based detection rules for the SOC System's detection engine. These rules are applied to normalized and enriched events to identify known attack patterns and suspicious behaviors.

## Rule Types

The detection engine supports two main types of rules:

### 1. Stateless Rules
Stateless rules evaluate a single event in isolation. They do not require any historical context or memory of previous events. These are typically used for signature matching (e.g., finding specific keywords or regex patterns in a payload).

*   **`sqli.py` (SQL Injection)**
    *   **Description**: Detects common SQL injection attempts by scanning the `url_path` and `payload` fields for known malicious patterns (e.g., `UNION SELECT`, `OR 1=1`, `--`).
    *   **Type**: Stateless
    *   **Target Events**: `http_request`, `web_log`

*   **`xss.py` (Cross-Site Scripting)**
    *   **Description**: Detects XSS attempts by scanning for common script injection vectors (e.g., `<script>`, `onerror=`, `javascript:`).
    *   **Type**: Stateless
    *   **Target Events**: `http_request`, `web_log`

*   **`path_traversal.py` (Path/Directory Traversal)**
    *   **Description**: Detects attempts to access unauthorized files or directories using traversal sequences (e.g., `../../`, `%2e%2e%2f`, `/etc/passwd`).
    *   **Type**: Stateless
    *   **Target Events**: `http_request`, `web_log`

### 2. Stateful Rules
Stateful rules require context over time. They track behavior across multiple events, typically using the `StateStore` (e.g., an in-memory cache or Redis) to maintain counts, timestamps, or sequences of actions.

*   **`brute_force.py` (HTTP Brute Force & Compromised Account)**
    *   **Description**: Detects brute-force login attempts and successful logins following a brute force attack. It tracks the number of failed login requests (e.g., status codes 401, 403, 404 on `/login` endpoints) originating from a specific source IP address. It also parses the payload to extract the targeted username for better context.
    *   **Thresholds**: 
        *   Triggers a `HIGH` alert if 5 failures occur within a 60-second window.
        *   Triggers a `CRITICAL` alert ("Compromised Account") if a successful login (200, 301, 302, or 405 in our mock environment) occurs from an IP that recently had 3 or more failures.
    *   **Suppression**: Includes a 5-minute alert suppression mechanism for the failed login alerts to prevent flooding.
    *   **Type**: Stateful
    *   **Target Events**: `http_request`, `web_log`

## Adding a New Rule

To add a new detection rule:

1.  Create a new Python file in this directory (e.g., `my_new_rule.py`).
2.  Define a function that takes an `event` (dict) and a `state_store` (StateStore instance) as arguments.
3.  The function should return an alert dictionary if the rule triggers, or `None` if it does not.
4.  Import your new rule in `__init__.py` and add it to the `RULES` list.

**Example Rule Signature:**
```python
from typing import Dict, Any, Optional
from engine.state.base import StateStore

def detect_something_bad(event: Dict[str, Any], state_store: StateStore) -> Optional[Dict[str, Any]]:
    # ... logic ...
    if bad_thing_happened:
        return {
            "rule_name": "My Custom Rule",
            "severity": "MEDIUM",
            "source_ip": event.get("source_ip"),
            "description": "Explanation of what was detected.",
            "event": event
        }
    return None
```
