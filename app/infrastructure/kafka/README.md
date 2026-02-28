# Broker Image Configs

- Image: bitnami/kafka:latest -> latest Kafka image from Bitnami, supports KRaft mode.
- KAFKA_BROKER_ID=1 -> unique ID for this broker.
- KAFKA_LISTENERS -> the port Kafka will listen on internally (inside the container).
- KAFKA_ADVERTISED_LISTENERS -> what other containers (like your monitored hosts) will use to reach Kafka.
- kafka:9092 -> Docker container name + port on the network
- KAFKA_PROCESS_ROLES=broker,controller -> enables KRaft mode (no Zookeeper).
- KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093 -> points to the controller port for this single-node cluster.
- KAFKA_NUM_PARTITIONS=3 -> number of partitions per topic by default.
- KAFKA_AUTO_CREATE_TOPICS_ENABLE=false -> we will explicitly create topics with a script.
- ports -> exposes Kafka to the host if you want to interact from outside Docker.
```
    9092 -> broker
    9093 -> controller (internal KRaft port)
```
- volumes ->
    ./config -> for any Kafka property overrides (broker.properties, kraft.properties)
    ./topics -> scripts to create topics on startup
- networks -> attached to pipeline_net so monitored hosts can reach Kafka.
- restart: always -> ensures broker comes back after a crash.

# config/broker.properties & config/kraft.properties are optional
- These files are optional, mainly for fine-tuning Kafka. Since Bitnami images already have sensible defaults, you could start without touching them.

# topics/create-topics.sh
- cub kafka-ready -> waits until Kafka broker is up (Bitnami utility).
```
| Topic               | Purpose                     |
| ------------------- | --------------------------- |
| `raw.logs`          | Filebeat system / app logs  |
| `raw.packets`       | Packetbeat network events   |
| `alerts.signatures` | Detection engine signatures |
| `alerts.anomalies`  | Anomaly detection alerts    |
```

# how to run
```bash
cd infrastructure/kafka
docker compose -f docker-compose.kafka.yaml up -d
```
- After a few seconds, Kafka will be listening on pipeline_net:kafka:9092.
- check topics
```bash
docker exec -it kafka kafka-topics.sh --bootstrap-server kafka:9092 --list
```