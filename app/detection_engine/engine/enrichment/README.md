# Event Enrichment Layer

This directory contains the logic for enriching normalized events with additional context before they are passed to the detection rules and machine learning models. 

## Purpose

Raw logs and network packets typically only contain IP addresses. To make accurate detection decisions and provide actionable alerts for analysts, we need context. The Enrichment Layer takes a normalized event and appends external intelligence to it.

## Current Enrichments

### 1. GeoIP Lookup
- **Tool:** Uses the `geoip2` Python library and a local MaxMind GeoLite2-Country database (`GeoLite2-Country.mmdb`).
- **Function:** Maps the `source_ip` to a physical geographical country.
- **Added Data:** Country name (`source_country_name`) and ISO code (`source_country_iso`).
- **Use Case:** Helps analysts quickly spot impossible travel (e.g., login from US, then 5 minutes later from China) or traffic originating from unexpected/sanctioned countries.

### 2. Threat Intelligence (Threat Intel)
- **Tool:** A local threat feed (`threat_intel.txt`).
- **Function:** Checks if the `source_ip` matches known malicious actors, botnets, or scanners.
- **Added Data:** A boolean flag (`is_threat_intel_match`).
- **Use Case:** If an IP is already known to be malicious, detection rules can lower their threshold for alerting, or analysts can prioritize the alert.

## How It Works

The `Enricher` class exposes a single `enrich(event: dict)` method. It safely attempts to look up the IPs. If a lookup fails (e.g., internal IP addresses like `192.168.x.x` or `172.20.x.x` won't have a public GeoIP), it gracefully skips the enrichment or returns "Unknown" without crashing the pipeline.

### Example Output
When an event passes through the enricher, it gains new fields at the root level:

```json
{
  "event_type": "web_log",
  "source_ip": "45.133.1.22",
  "status_code": 401,
  "source_country_iso": "RU",
  "source_country_name": "Russia",
  "is_threat_intel_match": true
}
```