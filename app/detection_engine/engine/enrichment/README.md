# Event Enrichment Layer

This directory contains the logic for enriching normalized events with additional context before they are passed to the detection rules and machine learning models. 

## Purpose

Raw logs and network packets typically only contain IP addresses. To make accurate detection decisions and provide actionable alerts for analysts, we need context. The Enrichment Layer takes a normalized event and appends external intelligence to it.

## Current Enrichments

### 1. GeoIP Lookup
- **Tool:** Uses the `geoip2` Python library and local MaxMind GeoLite2 databases (`GeoLite2-City.mmdb`, `GeoLite2-ASN.mmdb`, and `GeoLite2-Country.mmdb`).
- **Function:** Maps the `source_ip` to physical geographical locations and Autonomous System Numbers (ASNs).
- **Added Data:** Country (`source_country_name`, `source_country_iso`), City (`source_city_name`), Coordinates (`source_latitude`, `source_longitude`), and ISP/Organization (`source_asn`, `source_isp_name`).
- **Use Case:** Helps analysts quickly spot impossible travel, plot attacks on Kibana maps using coordinates, and determine if attacks originate from residential ISPs or hosting providers using ASNs.

### 2. Threat Intelligence (Threat Intel)
- **Tool:** A local structured threat feed (`threat_intel.json`).
- **Function:** Checks if the `source_ip` matches known malicious actors, botnets, or scanners, providing structured context.
- **Added Data:** A boolean flag (`is_threat_intel_match`), the type of threat (`threat_type`), and a confidence score (`threat_confidence`).
- **Use Case:** If an IP is already known to be malicious, detection rules can lower their threshold for alerting based on high confidence scores, and analysts can prioritize the alert.

### 3. Behavioral Enrichment (First Seen)
- **Tool:** The detection engine's `StateStore` (in-memory cache).
- **Function:** Tracks whether the system has ever seen this `source_ip` before.
- **Added Data:** A boolean flag (`is_new_ip`).
- **Use Case:** Attacks frequently originate from newly spun-up infrastructure. Flagging an IP as "new" provides a powerful behavioral indicator for rules and ML models.

## How It Works

The `Enricher` class exposes a single `enrich(event: dict)` method. It safely attempts to look up the IPs. If a lookup fails (e.g., internal IP addresses like `192.168.x.x` or `172.20.x.x` won't have a public GeoIP), it gracefully skips the enrichment, setting values to `None` without crashing the pipeline.

### Example Output
When an event passes through the enricher, it gains new fields at the root level:

```json
{
  "event_type": "web_log",
  "source_ip": "45.133.1.22",
  "status_code": 401,
  "source_country_iso": "RU",
  "source_country_name": "Russia",
  "source_city_name": "Moscow",
  "source_location": {
    "lat": 55.7558,
    "lon": 37.6173
  },
  "source_asn": 12345,
  "source_isp_name": "HostKey",
  "is_threat_intel_match": true,
  "threat_type": "Malware C2",
  "threat_confidence": 90,
  "is_new_ip": true
}
```