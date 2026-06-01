# Event Enrichment Layer

This directory contains the logic for enriching normalized events with additional context before they are passed to the detection rules and machine learning models. 

## Purpose

Raw logs and network packets typically only contain IP addresses. To make accurate detection decisions and provide actionable alerts for analysts, we need context. The Enrichment Layer takes a normalized event and appends external intelligence to it.

## Current Enrichments

### 1. GeoIP Lookup
- **Tool:** Uses the `geoip2` Python library and a local MaxMind GeoLite2-City database (`GeoLite2-City.mmdb`).
- **Function:** Maps the `source_ip` and `destination_ip` to physical geographical locations.
- **Added Data:** Country name, ISO code, city name, and latitude/longitude coordinates.
- **Use Case:** Helps analysts quickly spot impossible travel (e.g., login from US, then 5 minutes later from China) or traffic originating from unexpected/sanctioned countries.

### 2. Threat Intelligence (Threat Intel)
- **Tool:** A local threat feed (`ti_ips.txt`).
- **Function:** Checks if the `source_ip` or `destination_ip` matches known malicious actors, botnets, or scanners.
- **Added Data:** A boolean flag (`is_known_attacker`) and the matched IP.
- **Use Case:** If an IP is already known to be malicious, detection rules can lower their threshold for alerting, or analysts can prioritize the alert.

## How It Works

The `Enricher` class exposes a single `enrich(event: dict)` method. It safely attempts to look up the IPs. If a lookup fails (e.g., internal IP addresses like `192.168.x.x` or `172.20.x.x` won't have a public GeoIP), it gracefully skips the enrichment or returns "Unknown" without crashing the pipeline.

### Example Output
When an event passes through the enricher, it gains new nested dictionaries:

```json
{
  "event_type": "web_log",
  "source_ip": "45.133.1.22",
  "status_code": 401,
  "geoip": {
    "country": "Russia",
    "iso_code": "RU",
    "city": "Moscow",
    "location": {"lat": 55.7558, "lon": 37.6173}
  },
  "threat_intel": {
    "is_known_attacker": true,
    "matched_ip": "45.133.1.22"
  }
}
```