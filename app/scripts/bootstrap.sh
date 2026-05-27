#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "========================================================"
echo "Bootstrapping SOC Environment..."
echo "========================================================"

# Navigate to the app directory
cd "$(dirname "$0")/../"

echo "[1/3] Starting all Docker containers..."
# Start all services defined in the main compose file. 
# Docker Compose will handle the startup order based on 'depends_on'
docker compose up -d

echo "[2/3] Waiting for Kafka to be healthy..."
while [ "$(docker inspect --format='{{json .State.Health.Status}}' kafka)" != "\"healthy\"" ]; do
    echo -n "."
    sleep 2
done
echo -e "\nKafka is ready."

echo "[3/3] Waiting for Elasticsearch to be healthy..."
while [ "$(docker inspect --format='{{json .State.Health.Status}}' elasticsearch)" != "\"healthy\"" ]; do
    echo -n "."
    sleep 5
done
echo -e "\nElasticsearch is ready."

echo "========================================================"
echo "Environment is fully operational!"
echo "========================================================"
echo "Useful endpoints:"
echo "- Kibana: http://localhost:5601"
echo "- Nginx (Monitored): http://localhost:8080"
echo ""
echo "To view detection engine logs, run:"
echo "docker compose logs -f detection_engine"