# Detection Engine

The Detection Engine is the core Python microservice of the SOC. It acts as a real-time stream processing application, consuming raw logs and network packets from Kafka, analyzing them, and outputting security alerts.

## Pipeline Architecture

Every event that enters the engine goes through a strict, sequential pipeline managed by the `DetectionProcessor` (`app/detection_engine/engine/core/processor.py`).

### 1. Ingestion (Kafka Consumer)
The engine connects to the Kafka broker and subscribes to the `raw.logs` (Filebeat) and `raw.packets` (Packetbeat) topics.

### 2. Noise Filtering (`engine/filtering/`)
Before any heavy processing occurs, events are passed through the `NoiseFilterManager`. This layer drops irrelevant background noise (e.g., internal Docker DNS queries, static asset requests like `.css` or `.js`, and OS-level connectivity checks). This significantly reduces the load on the rest of the pipeline.

### 3. Normalization (`engine/normalization/`)
Raw events from different sources have completely different JSON schemas. The Normalizer converts these disparate formats into a single, unified dictionary schema. 
- It extracts the `source_ip`, `destination_ip`, `event_type`, and the core `payload` (e.g., the HTTP URL, the SQL query, or the DNS query string).

### 4. Enrichment (`engine/enrichment/`)
The engine adds critical context to the normalized event:
- **GeoIP:** Uses MaxMind databases to append City, Country, Coordinates, and ASN (ISP) data based on the `source_ip`.
- **Threat Intelligence:** Checks the IP against a structured database of known malicious actors, appending threat categories and confidence scores.

### 5. Signature Detection (`engine/core/rules/`)
The enriched event is evaluated against a suite of detection rules.
- **Stateless Rules:** Evaluate a single event in isolation (e.g., "Does this SQL query contain `UNION SELECT`?", "Is this DNS query longer than 60 characters?").
- **Stateful Rules:** Track behavior over time using an in-memory `StateStore` (e.g., "Has this IP failed to login via SSH 5 times in the last minute?").

### 6. Machine Learning Anomaly Detection (`engine/ml/`)
Events are passed to the `AnomalyDetector`, which uses the `river` library for online, streaming machine learning.
- It extracts numerical features (e.g., request counts, error rates, payload sizes) over rolling time windows.
- It uses a `HalfSpaceTrees` algorithm to score the event. If the anomaly score exceeds a dynamic threshold, an ML alert is generated.

### 7. Alert Generation (Kafka Producer)
If any rule or the ML model flags the event, an Alert JSON object is created and pushed to the `alerts.signatures` or `alerts.anomalies` Kafka topics, where it is eventually picked up by Logstash/Elasticsearch for visualization in Kibana.