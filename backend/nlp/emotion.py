"""
Emotional Language Detector.

Uses cardiffnlp/twitter-roberta-base-sentiment for sentence-level sentiment.
Uses a curated emotion lexicon (derived from NRC categories) to flag charged words.
Singleton pattern — model loaded once at startup.
"""

import logging
import re
from transformers import pipeline

logger = logging.getLogger(__name__)

# Curated emotion lexicon — words strongly associated with emotional charge
# Organized by NRC emotion categories
EMOTION_LEXICON = {
    "anger": {"anger", "rage", "fury", "outrage", "wrath", "hostile", "furious",
              "enraged", "infuriated", "livid", "irate", "wrathful", "seething",
              "aggression", "resentment", "hatred", "contempt", "bitter", "violent",
              "destructive", "attack", "assault", "condemn", "denounce", "slam"},
    "fear": {"fear", "terror", "panic", "dread", "horror", "alarm", "fright",
             "terrifying", "frightening", "scary", "threatening", "dangerous",
             "perilous", "menacing", "ominous", "dire", "grave", "crisis",
             "catastrophe", "disaster", "emergency", "threat", "warned", "warns"},
    "sadness": {"sad", "grief", "sorrow", "tragic", "devastating", "heartbreaking",
                "painful", "suffering", "misery", "despair", "hopeless", "bleak",
                "grim", "somber", "mournful", "loss", "victim", "casualties",
                "death", "killed", "died", "mourn", "grieve", "lament"},
    "disgust": {"disgust", "revolting", "repulsive", "vile", "abhorrent", "loathsome",
                "sickening", "nauseating", "deplorable", "despicable", "shameful",
                "scandalous", "corrupt", "sleazy", "disgusting", "appalling",
                "atrocious", "abominable", "reprehensible", "heinous"},
    "surprise": {"surprise", "shocked", "astonishing", "stunning", "startling",
                 "unexpected", "unprecedented", "remarkable", "extraordinary",
                 "bombshell", "revelation", "twist", "staggering", "unbelievable",
                 "incredible", "jaw-dropping", "explosive", "sensational"},
    "joy": {"joy", "celebration", "triumph", "victory", "jubilant", "elated",
            "thrilled", "ecstatic", "overjoyed", "euphoric", "glorious", "heroic",
            "miraculous", "wonderful", "fantastic", "brilliant", "amazing",
            "magnificent", "spectacular", "proud", "honor", "praise"},
    "trust": {"trust", "reliable", "credible", "honest", "integrity", "faithful",
              "loyal", "dedicated", "committed", "assured", "confident", "proven",
              "verified", "confirmed", "legitimate", "authentic", "genuine"},
    "anticipation": {"anticipation", "expect", "await", "looming", "upcoming",
                     "imminent", "inevitable", "bracing", "preparing", "poised",
                     "countdown", "forecast", "predict", "speculation", "rumor"},
}

# Flatten for quick lookup
ALL_EMOTION_WORDS = {}
for category, words in EMOTION_LEXICON.items():
    for word in words:
        if word not in ALL_EMOTION_WORDS:
            ALL_EMOTION_WORDS[word] = []
        ALL_EMOTION_WORDS[word].append(category)

# Sentiment label mapping
SENTIMENT_MAP = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "positive": "positive",
}

INTENSITY_WEIGHT = {
    "negative": 1.0,
    "neutral": 0.1,
    "positive": 0.6,
}


def _preprocess_for_roberta(text: str) -> str:
    """Preprocess text for twitter-roberta model."""
    text = re.sub(r"@\w+", "@user", text)
    text = re.sub(r"https?://\S+", "http", text)
    return text


class EmotionDetector:
    """Singleton emotional language detector."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        logger.info("Loading sentiment model: cardiffnlp/twitter-roberta-base-sentiment")
        self._pipe = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment",
            top_k=None,
            truncation=True,
            max_length=512,
        )
        self._initialized = True
        logger.info("Sentiment model loaded successfully.")

    def _get_flagged_words(self, text: str) -> list[str]:
        """Find emotionally charged words using the curated lexicon."""
        flagged = set()
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        for word in words:
            if word in ALL_EMOTION_WORDS:
                flagged.add(word)
        return sorted(flagged)

    def analyze_sentences(self, sentences: list[str]) -> list[dict]:
        """
        Analyze emotional content of each sentence.

        Returns:
            List of dicts with label, score, flagged_words, uncertain.
        """
        results = []
        batch_size = 16

        preprocessed = [_preprocess_for_roberta(s) for s in sentences]
        all_sentiments = []

        for i in range(0, len(preprocessed), batch_size):
            batch = preprocessed[i : i + batch_size]
            batch_outputs = self._pipe(batch)
            all_sentiments.extend(batch_outputs)

        for idx, sentence in enumerate(sentences):
            sentiment_output = all_sentiments[idx]
            top = max(sentiment_output, key=lambda x: x["score"])
            raw_label = top["label"]
            label = SENTIMENT_MAP.get(raw_label, raw_label.lower())
            confidence = top["score"]

            intensity_mult = INTENSITY_WEIGHT.get(label, 0.5)
            base_score = confidence * intensity_mult

            flagged_words = self._get_flagged_words(sentence)
            word_boost = min(30, len(flagged_words) * 8)
            emotion_score = min(100, int(base_score * 100) + word_boost)

            results.append({
                "label": label,
                "score": emotion_score,
                "flagged_words": flagged_words,
                "uncertain": int(confidence * 100) < 50,
            })

        return results

    def aggregate_emotion(self, sentence_results: list[dict]) -> dict:
        """Compute article-level emotion score."""
        if not sentence_results:
            return {"score": 0}
        avg = sum(r["score"] for r in sentence_results) / len(sentence_results)
        return {"score": int(avg)}
