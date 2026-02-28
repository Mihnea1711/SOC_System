# Elasticsearch & Kibana Infrastructure

## 1. Elasticsearch

Elasticsearch serves as the storage and indexing layer for enriched logs and alerts.

### Service Configs

- **Image:** `docker.elastic.co/elasticsearch/elasticsearch:9.3.1`  
- **Container Name / Hostname:** `elasticsearch`  
- **Environment Variables:**
```
    discovery.type=single-node # Single-node cluster
    xpack.security.enabled=false # Disable built-in security for simplicity
```
- **Ports:** `9200:9200` -> access Elasticsearch from host or other containers
- **Volumes:**
```
    ./elasticsearch.yaml -> optional configuration overrides
    ./elasticsearch/data -> persistent data storage
```
- **Network:** `elastic_net` -> isolated network for Elastic/Kibana
- **Restart Policy:** `unless-stopped`


## Config Options from `elasticsearch.yaml`

- **cluster.name**: elastic-cluster             # Logical name of the cluster
- **node.name**: elasticsearch                  # Node name inside the cluster
- **network.host**: 0.0.0.0                     # Listen on all interfaces
- **http.port**: 9200                           # Port for HTTP API
- **path.data**: /usr/share/elasticsearch/data  # Path for persistent storage
- **path.logs**: /usr/share/elasticsearch/logs  # Path for logs
- **discovery.type**: single-node               # Single-node cluster
- **bootstrap.memory_lock**: true               # Locks memory for performance

## How To Test
```bash
    curl http://localhost:9200/_cluster/health?pretty
    curl http://localhost:9200/_cat/indices?v
```

# Kibana

This document describes the setup of the Kibana service, which provides visualization and dashboards for Elasticsearch data.

---

## Service Configs

- **Image:** `docker.elastic.co/kibana/kibana:9.3.1`  
- **Container Name / Hostname:** `kibana`  
- **Depends On:** `elasticsearch` (must be running first)  
- **Ports:** `5601:5601` -> access Kibana from host or other containers  
- **Volumes:**
```
    ./kibana.yaml -> optional configuration overrides
    ./kibana/data -> persistent storage
```
- **Network:** `elastic_net` -> isolated network for Elastic/Kibana  
- **Restart Policy:** `unless-stopped`

## Config Options from kibana.yaml

- **server.name**: kibana                       # Name of the Kibana server
- **server.host**: 0.0.0.0                      # Listen on all interfaces
- **server.port**: 5601                         # Port for Kibana UI
- **elasticsearch.hosts**:                      # Elasticsearch backend(s)
```
    http://elasticsearch:9200
```
- **monitoring.ui.container.elasticsearch.enabled**: true  # Enable monitoring of Elasticsearch in UI

## How To Test
```
    http://localhost:5601
```