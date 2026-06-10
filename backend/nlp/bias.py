"""
Political Bias Classifier using valurank/distilroberta-mbfc-bias
via the HuggingFace Serverless Inference API.

Singleton pattern — API client initialized once at startup.
Sentences processed in batches for efficiency.
Labels mapped to Left / Center / Right with 0-100 confidence scores.
"""

import os
import time
import logging
import requests as http_requests

logger = logging.getLogger(__name__)

HF_MODEL = "valurank/distilroberta-mbfc-bias"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

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
    """Singleton political bias classifier using HuggingFace Inference API."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._token = os.environ.get("HF_API_TOKEN", "")
        self._headers = {}
        if self._token:
            self._headers["Authorization"] = f"Bearer {self._token}"
            logger.info("HuggingFace API token loaded.")
        else:
            logger.warning(
                "HF_API_TOKEN not set. Using HF Inference API without auth "
                "(lower rate limits). Set HF_API_TOKEN env var for better reliability."
            )
        self._initialized = True
        logger.info(f"BiasClassifier initialized (remote model: {HF_MODEL})")

    def _call_hf_api(self, texts: list[str], retries: int = 3) -> list:
        """
        Call HuggingFace Inference API with retry logic for cold starts.

        Args:
            texts: List of strings to classify.
            retries: Number of retry attempts for model loading.

        Returns:
            List of classification results (one per text).
        """
        payload = {"inputs": texts, "parameters": {"top_k": None}}

        for attempt in range(retries):
            try:
                response = http_requests.post(
                    HF_API_URL,
                    headers=self._headers,
                    json=payload,
                    timeout=60,
                )

                if response.status_code == 200:
                    return response.json()

                # Model is loading (cold start) — wait and retry
                if response.status_code == 503:
                    data = response.json()
                    wait_time = data.get("estimated_time", 20)
                    logger.info(
                        f"Model loading on HuggingFace (attempt {attempt + 1}/{retries}). "
                        f"Waiting {wait_time:.0f}s..."
                    )
                    time.sleep(min(wait_time, 30))
                    continue

                # Rate limited
                if response.status_code == 429:
                    logger.warning("HuggingFace rate limit hit. Waiting 10s...")
                    time.sleep(10)
                    continue

                # Other errors
                logger.error(
                    f"HF API error {response.status_code}: {response.text}"
                )
                response.raise_for_status()

            except http_requests.exceptions.Timeout:
                logger.warning(f"HF API timeout (attempt {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    time.sleep(5)
                    continue
                raise

        raise RuntimeError(
            f"HuggingFace API failed after {retries} attempts. "
            "The model may be unavailable. Try again shortly."
        )

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

            try:
                batch_outputs = self._call_hf_api(batch)
            except Exception as e:
                # If API fails, return Center/uncertain for this batch
                logger.error(f"Bias API call failed: {e}. Defaulting to Center.")
                for _ in batch:
                    results.append(
                        {
                            "label": "Center",
                            "score": 0,
                            "uncertain": True,
                            "raw_label": "unknown",
                        }
                    )
                continue

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
