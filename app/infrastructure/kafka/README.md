# Kafka Message Broker

This directory contains the configuration for the Kafka message broker, which acts as the central transport layer for the SOC system.

## Overview

- **Image:** `apache/kafka:latest` (Official Kafka image)
- **Architecture:** Single-node cluster running in **KRaft mode** (no Zookeeper required).

## Service Configuration

- **KAFKA_NODE_ID=1**: Unique ID for this broker.  
- **KAFKA_PROCESS_ROLES=broker,controller**: Enables KRaft mode, allowing this node to act as both the broker and the controller. 
- **KAFKA_LISTENERS**: Ports Kafka will listen on internally:
  - `PLAINTEXT://0.0.0.0:9092` (Internal Broker)
  - `EXTERNAL://0.0.0.0:9094` (Host Access)
  - `CONTROLLER://0.0.0.0:9093` (Internal KRaft Controller)
- **KAFKA_ADVERTISED_LISTENERS**: What other containers (like monitored hosts) will use to reach Kafka (`PLAINTEXT://kafka:9092`).  
- **KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093**: Points to the controller port for this single-node cluster.  
- **KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1**: Replication factor for internal topics (safe for single-node).  
- **KAFKA_NUM_PARTITIONS=3**: Number of partitions per topic by default.  

### Ports Exposed to Host
- `9092` -> Broker (External clients, scripts)
- `9093` -> Controller (Internal KRaft port)
- `9094` -> Host access (Packetbeat, scripts)

### Volumes
- `./data` -> Kafka persistent storage for topics/logs.
- `./docker-entrypoint.sh` -> Custom entrypoint script to start Kafka and create topics.

### Networks
- Attached to `pipeline_net` so collectors and the detection engine can reach it.

--- 

## Custom Entrypoint & Topics

The `docker-entrypoint.sh` script automates the setup process:
1. Starts Kafka.
2. Waits until Kafka is ready.
3. Creates the predefined topics automatically.

### Predefined Topics
| Topic               | Purpose                     |
| ------------------- | --------------------------- |
| `raw.logs`          | Filebeat system / app logs  |
| `raw.packets`       | Packetbeat network events   |
| `alerts.signatures` | Detection engine signatures |
| `alerts.anomalies`  | Anomaly detection alerts    |

- No separate scripts or external configuration are required to create topics.  
- To modify or add topics, update the array inside `docker-entrypoint.sh`.