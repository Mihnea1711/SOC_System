# SOC Networking Architecture

This directory defines the Docker bridge networks used to isolate and connect the various components of the SOC system.

## Networks Overview

The system uses three distinct Docker bridge networks to enforce logical separation of concerns:

### 1. `monitored_net`
- **Purpose:** Simulates the internal network of the organization being monitored.
- **Subnet:** `172.20.0.0/16`
- **Connected Containers:**
  - `monitored_host` (Vulnerable Nginx)
  - `packetbeat` (Sniffs this network)
  - `filebeat` (Reads logs from `monitored_host`)
- **Security:** Inter-Container Communication (ICC) is explicitly disabled (`com.docker.network.bridge.enable_icc: "false"`) to prevent lateral movement between containers on this network, simulating a segmented environment.

### 2. `pipeline_net`
- **Purpose:** The data ingestion and processing backbone.
- **Subnet:** `172.21.0.0/16`
- **Connected Containers:**
  - `kafka` (Message Broker)
  - `packetbeat` (Ships data here)
  - `filebeat` (Ships data here)
  - `detection_engine` (Consumes from here)
- **Security:** ICC is enabled so collectors can reach Kafka, and the detection engine can consume from it.

### 3. `elastic_net`
- **Purpose:** The storage and visualization backend.
- **Subnet:** `172.22.0.0/16`
- **Connected Containers:**
  - `elasticsearch` (Data Store)
  - `kibana` (Dashboards)
  - `detection_engine` (Ships alerts here)
- **Security:** Isolated network specifically for Elastic Stack components.

## Deployment

These networks are defined in `docker-compose.networks.yaml` and are included at the top level of the main `app/docker-compose.yaml` file. They are created automatically when you run `docker compose up`.