import time
from typing import Dict, Any, Optional
from engine.state.local_memory import LocalMemoryStore

class FeatureExtractor:
    """
    Extracts numerical features from raw/normalized events for the ML model.
    Maintains a rolling window of statistics per IP address.
    """
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        # Store a dictionary of stats per IP. 
        # LocalMemoryStore handles the TTL so we only look at recent behavior.
        self.ip_stats = LocalMemoryStore(maxsize=10000)

    def extract(self, event: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Updates the rolling stats for the source IP and returns the current feature vector.
        """
        ip = event.get("source_ip")
        if not ip:
            return None

        # Initialize or get current stats for this IP
        stats = self.ip_stats.get(ip)
        if not stats:
            stats = {
                "request_count": 0,
                "error_count": 0,
                "total_payload_size": 0,
                "unique_paths": set(),
                "unique_payloads": set()
            }

        # Update stats based on the current event
        stats["request_count"] += 1
        
        # Check if it's an error
        # For HTTP (web_log), we check status_code >= 400
        # For Packetbeat events, we check if there's an 'error' field
        status = event.get("status_code")
        if status:
            try:
                status_int = int(status)
                if status_int >= 400:
                    stats["error_count"] += 1
            except ValueError:
                pass
        elif event.get("error"):
            # Packetbeat will sometimes attach an error object like {"message": "unmatched response"}
            # However, for normal HTTP traffic, it shouldn't be counted as an error unless it's a 4xx/5xx
            if event.get("event_type") != "http_request":
                stats["error_count"] += 1
            
        # Payload size and variance
        payload = event.get("payload")
        if payload:
            payload_str = str(payload)
            stats["total_payload_size"] += len(payload_str)
            # Track unique payloads (highly effective for DNS tunneling and SQL injection)
            stats["unique_payloads"].add(payload_str)

        # Unique URLs (Path Variance for HTTP)
        url = event.get("url_path") or ""
        if url:
            stats["unique_paths"].add(url)

        # Save back to cache with TTL
        self.ip_stats.set(ip, stats, ttl_seconds=self.window_seconds)

        # Calculate the final features to be passed to the ML model
        request_count = stats["request_count"]
        error_rate = stats["error_count"] / request_count if request_count > 0 else 0.0
        avg_payload = stats["total_payload_size"] / request_count if request_count > 0 else 0.0
        
        # Combine path variance and payload variance into a single complexity metric
        variance_score = len(stats["unique_paths"]) + len(stats["unique_payloads"])

        return {
            "request_count": float(request_count),
            "error_rate": float(error_rate),
            "avg_payload_size": float(avg_payload),
            "variance_score": float(variance_score)
        }
