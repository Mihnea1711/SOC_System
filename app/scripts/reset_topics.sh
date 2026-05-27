#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "========================================================"
echo "Resetting Kafka Topics..."
echo "========================================================"

cd "$(dirname "$0")/../"

# Check if Kafka container is running
if [ "$(docker inspect -f '{{.State.Running}}' kafka 2>/dev/null)" != "true" ]; then
    echo "Error: Kafka container is not running. Please start the environment first."
    exit 1
fi

echo "Deleting existing topics..."
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic raw.packets" || true
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic raw.logs" || true
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic raw.metrics" || true
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic raw.audit" || true
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic alerts.signatures" || true
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic alerts.anomalies" || true

echo "Recreating topics..."
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic raw.packets --partitions 3 --replication-factor 1"
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic raw.logs --partitions 3 --replication-factor 1"
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic raw.metrics --partitions 3 --replication-factor 1"
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic raw.audit --partitions 3 --replication-factor 1"
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic alerts.signatures --partitions 3 --replication-factor 1"
docker exec kafka sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic alerts.anomalies --partitions 3 --replication-factor 1"

echo "========================================================"
echo "Topics reset successfully."
echo "========================================================"
