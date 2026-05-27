# SOC Automation Scripts

This directory contains bash scripts designed to automate common administrative tasks for the SOC environment on Linux/macOS systems.

## Available Scripts

### 1. `bootstrap.sh`
**Utility:** Starts the entire SOC environment.
**What it does:**
- Runs a single `docker compose up -d` command including all necessary compose files. Docker Compose natively handles the startup order based on the `depends_on: condition: service_healthy` rules defined in the YAML files.
- Actively polls Docker health checks to provide terminal feedback on when Kafka and Elastic are fully ready.
**Usage:**
```bash
./bootstrap.sh
```

### 2. `teardown.sh`
**Utility:** Safely stops all containers associated with the project.
**What it does:**
- Runs `docker compose down` across all compose files to stop and remove containers and networks.
- **Optional `--wipe` flag:** If you want to start completely fresh, passing `--wipe` will also delete the persistent Docker volumes (destroying all Kafka topics and Elasticsearch indices) and clean up local Python log files.
**Usage:**
```bash
./teardown.sh          # Stop containers, keep data
./teardown.sh --wipe   # Stop containers, DESTROY all data
```
