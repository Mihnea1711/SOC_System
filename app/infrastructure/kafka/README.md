# Broker Image Configs

- **Image:** `apache/kafka:latest` -> official Kafka image, supports KRaft mode (no Zookeeper required).  
- **KAFKA_NODE_ID=1** -> unique ID for this broker.  
- **KAFKA_LISTENERS** -> ports Kafka will listen on internally
- **KAFKA_PROCESS_ROLES=broker,controller** -> enables KRaft mode (single-node cluster). 
- **KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092** -> what other containers (like monitored hosts) will use to reach Kafka.  
- **KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER** -> which listener acts as controller.  
- **KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093** -> points to the controller port for this single-node cluster.  
- **KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1** -> replication factor for internal topics.  
- **KAFKA_NUM_PARTITIONS=3** -> number of partitions per topic by default.  

- **PORTS** -> exposes Kafka to the host if you want to interact from outside Docker.
```
    9092 -> broker
    9093 -> controller (internal KRaft port)
```
- **VOLUMES** ->
```
    ./data -> Kafka persistent storage for topics/logs
    ./docker-entrypoint.sh -> custom entrypoint script to start Kafka and create topics
```
- **NETWORKS** -> attached to pipeline_net so monitored hosts can reach Kafka.
- **RESTART**: `unless-stopped` -> ensures broker comes back after a crash.

--- 

# Custom Entrypoint

- **docker-entrypoint.sh** -> single script that:
  1. Starts Kafka.
  2. Waits until Kafka is ready.
  3. Creates the predefined topics automatically.

## Topics
| Topic               | Purpose                     |
| ------------------- | --------------------------- |
| `raw.logs`          | Filebeat system / app logs  |
| `raw.packets`       | Packetbeat network events   |
| `alerts.signatures` | Detection engine signatures |
| `alerts.anomalies`  | Anomaly detection alerts    |

- No separate scripts or external configuration are required to create topics.  
- To modify topics, update the array inside `docker-entrypoint.sh`.