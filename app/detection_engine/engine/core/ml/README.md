# ML Anomaly Detection Layer

This directory contains the Machine Learning components of the Detection Engine. Its purpose is to identify zero-day attacks, novel evasion techniques (e.g., attackers modifying their payloads or timing to bypass known static signatures), or unusual behavioral patterns that bypass our static, signature-based rules.

## The Model: Half-Space Trees (HST)

We are currently using the **Half-Space Trees** algorithm provided by the `river` Python library.

### How it works
Half-Space Trees is the streaming/online equivalent of the popular **Isolation Forest** algorithm. 
- It builds an ensemble (a "forest") of decision trees.
- It randomly splits the feature space to isolate observations.
- **The core concept:** Anomalies are "few and different." Because they are different, they are easier to isolate. Therefore, anomalous events will have significantly shorter path lengths from the root of the tree to a leaf node. 
- The model outputs an anomaly score between `0.0` (perfectly normal) and `1.0` (highly anomalous).

### Why we chose Half-Space Trees
1. **Online/Streaming Native:** Traditional ML models require "batch" training (gathering a massive CSV of logs, training for hours, deploying, and repeating). HST learns continuously. As every single event flows through Kafka, the model updates its understanding of "normal" in real-time (`learn_one`).
2. **Adapts to Concept Drift:** Network traffic changes over time. HST uses a `window_size` parameter to gradually forget old behavior and adapt to new, legitimate traffic patterns without requiring manual retraining.
3. **Low Overhead:** It requires very little memory and CPU, making it perfect for a lightweight, high-throughput microservice in a Dockerized environment.

## Alternative Options Considered

During the design phase, several other approaches were considered:

1. **Isolation Forest (scikit-learn)**
   * *Why not?* It is a batch-learning model. We would have to store logs in a database, periodically query them, retrain the model, and swap it out. This breaks the real-time, event-driven stream processing architecture we built with Kafka.
2. **Deep Learning / Autoencoders (TensorFlow / PyTorch)**
   * *Why not?* Massive overkill for the 4-dimensional feature vector we are extracting. It would require significant computational overhead (potentially GPUs) and introduces massive complexity for a "mini SOC."
3. **One-Class SVM**
   * *Why not?* Scales very poorly with high-volume streaming data. It becomes computationally expensive as the dataset grows, whereas HST maintains a constant memory and time footprint.
4. **Statistical Thresholding (Z-Score / MAD)**
   * *Why not?* While simpler, basic statistical thresholds struggle with multi-dimensional relationships. For example, a high request count might be normal if the error rate is low, but anomalous if the error rate is high. HST naturally captures these multi-dimensional interactions.

## Feature Engineering

The model does not look at raw logs. The `FeatureExtractor` (`features.py`) maintains a rolling time-window (e.g., 60 seconds) of statistics per IP address and feeds the following numerical vector to the model:
- `request_count`: Volume of traffic.
- `error_rate`: Percentage of 4xx/5xx errors (indicative of scanning, brute-forcing, or exploitation failures).
- `avg_payload_size`: Size of requests (useful for detecting data exfiltration or large payloads like SQLi).
- `url_variance`: Number of unique endpoints accessed (high variance indicates directory brute-forcing or crawling).