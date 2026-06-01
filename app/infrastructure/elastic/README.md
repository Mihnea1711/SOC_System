# Elasticsearch & Kibana Infrastructure

This directory contains the configuration for the storage and visualization layer of the SOC system.

## 1. Elasticsearch

Elasticsearch serves as the NoSQL storage and indexing layer for enriched logs and generated alerts.

### Service Configuration

- **Image:** `docker.elastic.co/elasticsearch/elasticsearch:9.3.1`  
- **Architecture:** Single-node cluster (`discovery.type=single-node`).
- **Security:** Built-in security (xpack) is disabled (`xpack.security.enabled=false`) for local development simplicity.
- **Ports:** `9200:9200` (Access Elasticsearch from host or other containers).
- **Networks:** Attached to `elastic_net` (isolated network for Elastic/Kibana).

### Volumes
- `./elasticsearch.yaml` -> Optional configuration overrides.
- `./elasticsearch/data` -> Persistent data storage (survives container restarts).

### Config Options (`elasticsearch.yaml`)
- **cluster.name**: `elastic-cluster` (Logical name of the cluster)
- **node.name**: `elasticsearch` (Node name inside the cluster)
- **network.host**: `0.0.0.0` (Listen on all interfaces)
- **bootstrap.memory_lock**: `true` (Locks memory for performance)

### How To Test
```bash
curl http://localhost:9200/_cluster/health?pretty
curl http://localhost:9200/_cat/indices?v
```

---

## 2. Kibana

Kibana provides the frontend UI, visualizations, and dashboards for the data stored in Elasticsearch.

### Service Configuration

- **Image:** `docker.elastic.co/kibana/kibana:9.3.1`  
- **Dependencies:** Waits for `elasticsearch` to be running first.
- **Ports:** `5601:5601` (Access Kibana UI from the host browser).
- **Networks:** Attached to `elastic_net`.

### Volumes
- `./kibana.yaml` -> Configuration overrides.
- `./kibana/data` -> Persistent storage for Kibana settings/dashboards.

### Config Options (`kibana.yaml`)
- **server.host**: `0.0.0.0` (Listen on all interfaces)
- **elasticsearch.hosts**: `["http://elasticsearch:9200"]` (Points to the Elasticsearch backend)
- **monitoring.ui.container.elasticsearch.enabled**: `true` (Enable monitoring of Elasticsearch in UI)

### How To Test
Open your browser and navigate to:
```
http://localhost:5601
```