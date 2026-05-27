#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "========================================================"
echo "Bootstrapping SOC Environment..."
echo "========================================================"

# Navigate to the app directory
cd "$(dirname "$0")/../"

echo "[1/4] Building and starting all Docker containers..."
# Build images without cache if custom Dockerfiles exist, then start services.
# Docker Compose will handle the startup order based on 'depends_on'
docker compose up -d --build

echo "[2/4] Waiting for Kafka to be healthy..."
while [ "$(docker inspect --format='{{json .State.Health.Status}}' kafka)" != "\"healthy\"" ]; do
    echo -n "."
    sleep 2
done
echo -e "Kafka is ready.\n"

echo "[3/4] Waiting for Elasticsearch to be healthy..."
while [ "$(docker inspect --format='{{json .State.Health.Status}}' elasticsearch)" != "\"healthy\"" ]; do
    echo -n "."
    sleep 5
done
echo -e "Elasticsearch is ready.\n"

echo "[4/4] Waiting for Kibana to be healthy..."
while [ "$(docker inspect --format='{{json .State.Health.Status}}' kibana)" != "\"healthy\"" ]; do
    echo -n "."
    sleep 5
done
echo -e "Kibana is ready.\n"


echo "========================================================"
echo "Environment is fully operational!"
echo "========================================================"
echo "Useful endpoints:"
echo "- Kibana: http://localhost:5601"
echo "- Nginx (Monitored): http://localhost:8080"
echo ""
echo "To view detection engine logs, run:"
echo "docker compose logs -f detection_engine"