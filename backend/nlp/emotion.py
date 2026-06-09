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

from textblob import TextBlob

class EmotionDetector:
    """Singleton emotional language detector using TextBlob + NRC Lexicon to save RAM."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        logger.info("Initializing lightweight TextBlob sentiment analyzer...")
        self._initialized = True

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
        Analyze emotional content of each sentence using TextBlob and NRC lexicon.

        Returns:
            List of dicts with label, score, flagged_words, uncertain.
        """
        results = []

        for sentence in sentences:
            blob = TextBlob(sentence)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Map polarity (-1.0 to 1.0) to labels and base score
            if polarity <= -0.1:
                label = "negative"
                base_score = abs(polarity) * 100
            elif polarity >= 0.1:
                label = "positive"
                base_score = (polarity * 100) * 0.6  # Weight positive slightly less
            else:
                label = "neutral"
                base_score = 10.0

            flagged_words = self._get_flagged_words(sentence)
            
            # Boost score based on strong emotional words found
            word_boost = min(40, len(flagged_words) * 10)
            emotion_score = min(100, int(base_score) + word_boost)

            results.append({
                "label": label,
                "score": emotion_score,
                "flagged_words": flagged_words,
                "uncertain": subjectivity < 0.3, # Low subjectivity = mostly factual, so emotion label is uncertain
            })

        return results

    def aggregate_emotion(self, sentence_results: list[dict]) -> dict:
        """Compute article-level emotion score."""
        if not sentence_results:
            return {"score": 0}
        avg = sum(r["score"] for r in sentence_results) / len(sentence_results)
        return {"score": int(avg)}
