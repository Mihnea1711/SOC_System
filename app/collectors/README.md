# SOC Data Collectors

This directory contains the configurations for the data ingestion layer of our Distributed Intrusion Detection and Response System. The collectors are responsible for gathering raw telemetry from the monitored environment and shipping it to the central message broker (Kafka) for real-time analysis.

## Architecture & Components

We utilize the **Elastic Beats** family for lightweight, purpose-built data collection. Currently, the system relies on two primary collectors:

### 1. Filebeat (`/beats/filebeat.yml`)
**Purpose:** Log Collection and Forwarding.
**Monitored Targets:** 
- Nginx Web Server (`nginx_server`)
- SSH Server (`ssh_server`)
**Data Flow:**
- Filebeat mounts the `/var/log/nginx/` and `/var/log/ssh/` directories from the host/Docker volumes.
- It continuously tails the `access.log`, `error.log`, and `openssh/current` files.
- **Pre-filtering:** The configuration includes processors to drop noisy, low-value events at the source (e.g., requests for `.css`/`.js` files, or internal Docker health checks).
- **Output:** Ships the filtered JSON logs to the Kafka topic `raw.logs`.

### 2. Packetbeat (`/beats/packetbeat.yml`)
**Purpose:** Real-time Network Packet Analytics.
**Monitored Target:** The `monitored_net` Docker bridge network.
**Data Flow:**
- Packetbeat runs with `network_mode: host` and `cap_add: ['NET_ADMIN', 'NET_RAW']` to sniff traffic across Docker bridge interfaces.
- It decodes network protocols (HTTP, DNS, MySQL, TCP flows) in real-time.
- **Pre-filtering:** The configuration drops internal infrastructure noise (e.g., Docker's internal DNS resolution for `*.local`, or traffic destined for Kafka/Elasticsearch itself).
- **Output:** Ships the decoded network transactions as JSON documents to the Kafka topic `raw.packets`.

## Deployment

The collectors are deployed alongside the monitored services using Docker Compose.

**Location:** `app/collectors/docker-compose.host.yaml`

This compose file defines the entire monitored environment:
1.  `nginx_server`: A vulnerable Nginx web server acting as the target for web attack simulations.
2.  `ssh_server`: A honeypot SSH server to demonstrate TCP-layer brute force detection.
3.  `mysql_server`: A database container acting as a target for data exfiltration detection.
4.  `dns_server`: A Bind9 container acting as a target for DNS tunneling and covert channels.
5.  `filebeat`: The log collector container.
6.  `packetbeat`: The network sniffer container.

### How to Run

To start the entire environment (including collectors and monitored hosts), you should use the main bootstrap script from the root `app/` directory:

```bash
cd app
./scripts/bootstrap.sh
```

*Note: The collectors depend on the Kafka infrastructure being up and running first, as they need to establish a connection to the `raw.logs` and `raw.packets` topics. The bootstrap script handles this ordering automatically.*

## Why Pre-filtering Matters

Both `filebeat.yml` and `packetbeat.yml` utilize the `drop_event` processor. This is a critical architectural decision for a Stream Processing SOC:
By dropping obvious noise (like static asset requests or background OS DNS queries) at the collector level, we save significant network bandwidth, reduce the storage burden on Kafka, and free up CPU cycles in the Python Detection Engine, allowing it to focus entirely on evaluating potentially malicious events.