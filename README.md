# Distributed Intrusion Detection System

A containerized, event-driven Security Operations Center (SOC) designed to ingest, process, and analyze network and host data in real-time. The system uses a combination of signature-based rules and streaming Machine Learning (ML) to detect both known attacks and zero-day anomalies.

## System Architecture & Data Flow

The system is built on an event-driven microservices architecture using Kafka as the central nervous system. The data flows through four main layers:

1. **Collection:** Beats agents capture raw traffic and logs from the monitored environment.
2. **Transport:** Events are streamed into Kafka topics (`raw.logs`, `raw.packets`).
3. **Processing & Detection:** The Python engine consumes the raw streams, cleans them, and applies detection logic. Alerts are pushed back to Kafka (`alerts.signatures`, `alerts.anomalies`).
4. **Storage & Visualization:** Elasticsearch indexes the alerts, which are then visualized in Kibana.

---

## Layers and Services

### 1. Collectors (Ingestion Layer)

- **Nginx (Monitored Host):** A mock web server serving as the target for web attack simulations.
- **SSH Server (Monitored Host):** An Ubuntu container exposing port 22, acting as a target for brute-force attacks.
- **MySQL Database (Monitored Host):** A database container acting as a target for data exfiltration and brute-force attacks.
- **DNS Server (Monitored Host):** A Bind9 container acting as a target for DNS tunneling and exfiltration.
- **Filebeat:** Tails and parses Nginx `access.log` and `error.log` files.
- **Packetbeat:** Sniffs raw network traffic (TCP/HTTP flows, MySQL wire protocol, DNS queries, SSH flows) on the Docker bridge network.

### 2. Message Broker (Transport Layer)

- **Kafka (KRaft Mode):** Handles high-throughput, real-time data streaming without the need for Zookeeper. Decouples the ingestion layer from the processing layer, ensuring no data is lost if the detection engine restarts.

### 3. Detection Engine (Processing Layer)

A custom Python service that acts as the brain of the system. It processes events through a strict pipeline:

- **Noise Filter:** Drops irrelevant background noise (e.g., static asset requests, internal Docker DNS checks) to save processing power.
- **Normalizer:** Standardizes different log formats (Filebeat vs. Packetbeat) into a single, unified JSON schema.
- **Enricher:** Adds deep context to the event, such as precise GeoIP location (City, Coordinates, ASN/ISP) and structured Threat Intelligence (categorizing known malicious IPs and assigning confidence scores).
- **Signature Detection:** Uses stateful and stateless rules to catch known attacks (SQLi, XSS, Path Traversal, Brute Force, Compromised Accounts).
- **ML Anomaly Detection:** Uses an online learning model (`river` Half-Space Trees) to track rolling IP statistics (error rates, request counts) and detect unusual behavioral patterns without predefined rules.

### 4. Storage & Presentation (Data Lake Layer)

- **Elasticsearch:** A NoSQL database optimized for search, used to store all generated alerts.
- **Kibana:** The frontend UI used to build dashboards, search through alerts, and monitor the system's health.

### 5. Automated Incident Response

- **Incident Response:** A Python service that listens to Kafka alerts and takes automated actions (e.g., dynamically updating Nginx blocklists or using the Docker API to quarantine compromised containers).

### 6. Attack Simulators

- **Scenario Runner:** A Python framework that orchestrates YAML-based attack scenarios (e.g., warming up the ML model with normal traffic, then launching a distributed brute-force or SQL injection attack).

---

## Expected Output

When the Detection Engine identifies malicious activity, it generates an alert. These alerts are pushed to Kafka and indexed in Elasticsearch.

A typical alert output looks like this (JSON format):

```json
{
  "rule_name": "ML Anomaly Detected",
  "severity": "HIGH",
  "source_ip": "45.133.1.22",
  "destination_ip": "172.20.0.5",
  "description": "Anomalous behavior detected with score 0.99",
  "@timestamp": "2026-05-31T19:12:37.000Z",
  "metadata": {
    "anomaly_score": 0.997,
    "features": {
      "request_count": 10.0,
      "error_rate": 1.0,
      "avg_payload_size": 0.0,
      "variance_score": 1.0
    }
  },
  "event": {
    "event_type": "web_log",
    "http_method": "POST",
    "url_path": "/login",
    "status_code": 401,
    "geoip": {
      "country": "Unknown"
    },
    "threat_intel": {
      "is_known_attacker": true
    }
  }
}
```

### How to Run

1. **Start the environment:** Spin up the infrastructure, collectors, and detection engine.
   ```bash
   ./scripts/bootstrap.sh
   ```
2. **Run attack scenarios:** Use the scenario runner to generate normal traffic (warmup) and simulate attacks.

   ```bash
   cd app/attacks

   # First, warm up the ML model
   python scenario_runner.py scenarios/scenario_0_warmup.yaml

   # Then, run attack scenarios
   python scenario_runner.py scenarios/scenario_1_recon_brute.yaml
   python scenario_runner.py scenarios/scenario_2_brute_xss.yaml
   python scenario_runner.py scenarios/scenario_3_web_exfil.yaml
   python scenario_runner.py scenarios/scenario_4_ssh_compromise.yaml
   python scenario_runner.py scenarios/scenario_5_mysql_exfiltration.yaml
   python scenario_runner.py scenarios/scenario_6_dns_tunneling.yaml
   ```

3. **Stop and clean up:** Bring down the environment and optionally wipe all data volumes (Kafka, Elasticsearch).
   ```bash
   ./scripts/teardown.sh [--wipe]
   ```
