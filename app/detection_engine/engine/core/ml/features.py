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
                "unique_urls": set()
            }

        # Update stats based on the current event
        stats["request_count"] += 1
        
        # Check if it's an error (4xx or 5xx)
        status = event.get("status_code")
        if status:
            try:
                status_int = int(status)
                if status_int >= 400:
                    stats["error_count"] += 1
            except ValueError:
                pass # Ignore non-integer status codes
        else:
            # Packetbeat sometimes returns None for unmatched/failed connections
            stats["error_count"] += 1
            
        # Payload size
        payload = event.get("payload") or ""
        stats["total_payload_size"] += len(payload)

        # Unique URLs (Path Variance)
        url = event.get("url_path") or ""
        if url:
            stats["unique_urls"].add(url)

        # Save back to cache with TTL
        self.ip_stats.set(ip, stats, ttl_seconds=self.window_seconds)

        # Calculate the final features to be passed to the ML model
        request_count = stats["request_count"]
        error_rate = stats["error_count"] / request_count if request_count > 0 else 0.0
        avg_payload = stats["total_payload_size"] / request_count if request_count > 0 else 0.0
        url_variance = len(stats["unique_urls"])

        return {
            "request_count": float(request_count),
            "error_rate": float(error_rate),
            "avg_payload_size": float(avg_payload),
            "url_variance": float(url_variance)
        }
