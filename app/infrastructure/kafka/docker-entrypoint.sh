#!/bin/bash
set -e

echo "[Entrypoint] Starting Kafka (official entrypoint)..."
/etc/kafka/docker/run &
KAFKA_PID=$!

echo "[Entrypoint] Waiting for Kafka to be ready..."
until /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1; do
  sleep 2
done

echo "[Entrypoint] Kafka is ready. Creating topics..."

TOPICS=("raw.logs" "raw.packets" "alerts.signatures" "alerts.anomalies")

for TOPIC in "${TOPICS[@]}"; do
  if ! /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list | grep -q "^$TOPIC$"; then
    echo "Creating topic: $TOPIC"
    /opt/kafka/bin/kafka-topics.sh \
      --bootstrap-server localhost:9092 \
      --create \
      --topic "$TOPIC" \
      --partitions 3 \
      --replication-factor 1
  else
    echo "Topic $TOPIC already exists"
  fi
done

echo "[Entrypoint] Kafka fully started"
wait $KAFKA_PID