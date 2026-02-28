/app
├── docker-compose.yaml
├── docker-compose.override.yaml          # optional (dev vs prod)
├── .env                                 # shared env vars
├── README.md
│
├── docs/
│   ├── architecture/
│   │   ├── diagrams/
│   │   │   ├── system_overview.drawio
│   │   │   ├── data_flow.drawio
│   │   │   └── threat_model.drawio
│   │   └── architecture.md
│   │
│   ├── experiments/
│   │   ├── attack_scenarios.md
│   │   ├── evaluation_metrics.md
│   │   └── benchmarking.md
│   │
│   └── research_notes.md
│
├── infrastructure/
│   ├── kafka/
│   │   ├── docker-compose.kafka.yaml
│   │   ├── config/
│   │   │   ├── broker.properties
│   │   │   └── kraft.properties
│   │
│   ├── elastic/
│   │   ├── docker-compose.elastic.yaml
│   │   ├── elasticsearch.yaml
│   │   └── kibana.yaml
│   │
│   └── networking/
│       └── docker-networks.yaml
│
├── collectors/
│   ├── beats/
│   │   ├── filebeat/
│   │   │   ├── Dockerfile
│   │   │   ├── filebeat.yaml
│   │   │   └── modules.d/
│   │   ├── packetbeat/
│   │   │   ├── Dockerfile
│   │   │   └── packetbeat.yaml
│   │   └── README.md
│   │
│   ├── honeypots/
│   │   ├── ssh/
│   │   │   ├── Dockerfile
│   │   │   └── config/
│   │   ├── web/
│   │   └── README.md
│   │
│   └── agents/
│       ├── python/
│       │   ├── agent/
│       │   │   ├── main.py
│       │   │   ├── executor.py
│       │   │   ├── firewall.py
│       │   │   └── config.py
│       │   └── Dockerfile
│       └── README.md
│
├── stream_processing/
│   ├── detection_engine/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── consumer.py
│   │   │   ├── producer.py
│   │   │   ├── enrichment/
│   │   │   │   ├── geoip.py
│   │   │   │   └── asn.py
│   │   │   ├── rules/
│   │   │   │   ├── brute_force.py
│   │   │   │   ├── port_scan.py
│   │   │   │   └── web_attacks.py
│   │   │   ├── ml/
│   │   │   │   ├── features.py
│   │   │   │   ├── isolation_forest.py
│   │   │   │   └── autoencoder.py
│   │   │   └── models/
│   │   │       └── pretrained/
│   │   ├── Dockerfile
│   │   └── config.yaml
│   │
│   └── replay/
│       ├── kafka_to_pcap.py
│       └── README.md
│
├── response/
│   ├── fastapi_service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── kafka_consumer.py
│   │   │   ├── actions/
│   │   │   │   ├── block_ip.py
│   │   │   │   ├── isolate_container.py
│   │   │   └── schemas.py
│   │   ├── Dockerfile
│   │   └── config.yaml
│   │
│   └── README.md
│
├── storage/
│   ├── elastic/
│   │   ├── index_templates/
│   │   │   ├── logs.json
│   │   │   └── alerts.json
│   │   └── ilm_policies/
│   │       └── hot_warm.json
│   │
│   └── README.md
│
├── visualization/
│   ├── kibana/
│   │   ├── dashboards/
│   │   │   ├── attacks.ndjson
│   │   │   ├── network.ndjson
│   │   │   └── response.ndjson
│   │   └── README.md
│
├── attacks/
│   ├── generators/
│   │   ├── http_bruteforce.py
│   │   ├── port_scan.py
│   │   └── credential_stuffing.py
│   │
│   ├── scenarios/
│   │   ├── scenario_1_http_attack.yaml
│   │   └── scenario_2_bruteforce.yaml
│   │
│   └── README.md
│
└── scripts/
    ├── bootstrap.sh
    ├── teardown.sh
    ├── reset_topics.sh
    └── dev.sh