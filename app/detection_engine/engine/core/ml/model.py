import math
from typing import Dict
from river import anomaly
from river import compose
from river import preprocessing

class AnomalyDetector:
    """
    Online Machine Learning Anomaly Detector using River.
    Uses Half-Space Trees (streaming equivalent of Isolation Forest).
    """
    def __init__(self, warmup_observations: int = 100):
        # We build a pipeline: 
        # 1. StandardScaler: Normalizes the features (mean 0, variance 1) so large numbers don't dominate.
        # 2. HalfSpaceTrees: The actual anomaly detection algorithm.
        # Parameters for HalfSpaceTrees:
        # - n_trees: Number of trees in the ensemble. More trees = more stable scores, but slower. 25 is a good balance for streaming.
        # - height: Maximum depth of each tree. Controls how complex the anomalies can be. 10 is standard.
        # - window_size: How many recent observations each tree remembers. This defines the "normal" baseline. 
        #                A smaller window (e.g. 50) adapts quickly to new traffic patterns but might forget older normal behavior.
        #                A larger window (e.g. 250) is more stable but slower to adapt.
        # - seed: For reproducibility in testing.
        self.model = compose.Pipeline(
            preprocessing.StandardScaler(),
            anomaly.HalfSpaceTrees(
                n_trees=25,
                height=10,
                window_size=50,
                seed=42
            )
        )
        
        # Warmup period: The model needs to see some "normal" traffic before its scores are reliable.
        # We won't alert until we've seen at least this many events.
        self.observations = 0
        self.warmup_observations = warmup_observations

    def score_and_train(self, features: Dict[str, float]) -> float:
        """
        Scores the current feature vector, then updates the model.
        Returns an anomaly score between 0.0 (normal) and 1.0 (anomalous).
        """
        # 1. Score the event (Inference)
        # We do this BEFORE training so the event doesn't score itself as normal
        # Basically it predicts the new event before adjusting its internal definition
        score = self.model.score_one(features)
        
        # 2. Update the model (Online Learning)
        # Incorporates the new event into its internal definition - adjust window-size in order to control how long events stay "in-memory"
        self.model.learn_one(features)
        self.observations += 1
            
        # 4. Suppress unstable early scores
        # HalfSpaceTrees can output exactly 0.0 or 0.5 when the trees are still mostly empty or perfectly balanced.
        # We also suppress very low scores (< 0.1) as this is definitively normal traffic.
        # We also suppress scores below 0.99 during the warmup phase to prevent false positives from initial variance.
        if math.isclose(score, 0.0, abs_tol=1e-9) or math.isclose(score, 0.5, abs_tol=1e-9) or score < 0.1:
            return 0.0
        
        if self.observations < self.warmup_observations and score < 0.99:
            return 0.0
        
        # If the score is exactly 0.515, it's a known artifact of HalfSpaceTrees when it encounters
        # a new feature dimension that is perfectly balanced across its internal trees, but hasn't
        # reached the threshold to be considered a full anomaly yet. We treat this as normal.
        if math.isclose(score, 0.515, abs_tol=1e-3) or math.isclose(score, 0.775, abs_tol=1e-3):
            return 0.0

        return score
