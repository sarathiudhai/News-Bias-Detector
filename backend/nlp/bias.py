"""
Political Bias Classifier using valurank/distilroberta-mbfc-bias.

Singleton pattern — model loaded once at startup.
Sentences processed in batches of 16 for efficiency.
Labels mapped to Left / Center / Right with 0-100 confidence scores.
"""

import logging
from transformers import pipeline

logger = logging.getLogger(__name__)

# Label mapping from model output → simplified Left/Center/Right
LABEL_MAP = {
    "left": "Left",
    "leftcenter": "Left",
    "leastbiased": "Center",
    "rightcenter": "Right",
    "right": "Right",
    "extremeright": "Right",
    "unknown": "Center",
}

# Directional weight for aggregation: negative = left, positive = right, 0 = center
DIRECTION_WEIGHT = {
    "left": -1.0,
    "leftcenter": -0.5,
    "leastbiased": 0.0,
    "rightcenter": 0.5,
    "right": 1.0,
    "extremeright": 1.0,
    "unknown": 0.0,
}


class BiasClassifier:
    """Singleton political bias classifier."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        logger.info("Loading political bias model: valurank/distilroberta-mbfc-bias")
        self._pipe = pipeline(
            "text-classification",
            model="valurank/distilroberta-mbfc-bias",
            top_k=None,  # Return all label scores
            truncation=True,
            max_length=512,
        )
        self._initialized = True
        logger.info("Political bias model loaded successfully.")

    def classify_sentences(self, sentences: list[str]) -> list[dict]:
        """
        Classify a list of sentences for political bias.

        Args:
            sentences: List of sentence strings.

        Returns:
            List of dicts: {"label": str, "score": int, "uncertain": bool, "raw_label": str}
        """
        results = []
        batch_size = 16

        for i in range(0, len(sentences), batch_size):
            batch = sentences[i : i + batch_size]
            batch_outputs = self._pipe(batch)

            for output in batch_outputs:
                # output is a list of {"label": ..., "score": ...} sorted by score desc
                top = max(output, key=lambda x: x["score"])
                raw_label = top["label"].lower()
                confidence = int(top["score"] * 100)

                results.append(
                    {
                        "label": LABEL_MAP.get(raw_label, "Center"),
                        "score": confidence,
                        "uncertain": confidence < 50,
                        "raw_label": raw_label,
                    }
                )

        return results

    def aggregate_bias(self, sentence_results: list[dict]) -> dict:
        """
        Compute article-level bias from sentence-level results.
        Uses directional weighted average to determine overall leaning.

        Returns:
            {"label": str, "score": int}
        """
        if not sentence_results:
            return {"label": "Center", "score": 0}

        total_weight = 0.0
        total_confidence = 0.0
        direction_sum = 0.0

        for r in sentence_results:
            weight = r["score"] / 100.0
            direction = DIRECTION_WEIGHT.get(r["raw_label"], 0.0)
            direction_sum += direction * weight
            total_weight += abs(weight)
            total_confidence += r["score"]

        avg_confidence = int(total_confidence / len(sentence_results))

        if total_weight > 0:
            avg_direction = direction_sum / total_weight
        else:
            avg_direction = 0.0

        # Determine label from average direction
        if avg_direction < -0.25:
            label = "Left"
        elif avg_direction > 0.25:
            label = "Right"
        else:
            label = "Center"

        # Score represents how strongly biased (0 = perfectly neutral, 100 = extremely biased)
        bias_intensity = min(100, int(abs(avg_direction) * 100))

        return {"label": label, "score": max(bias_intensity, avg_confidence // 2)}
