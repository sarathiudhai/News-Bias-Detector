"""
Factual Density Scorer using spaCy NER.

Detects factual signals: named entities, numbers, dates, citations.
Flags opinion markers: hedging phrases, subjective adjectives.
Scores each sentence/paragraph: factual % vs opinion %.
"""

import re
import logging
import spacy

logger = logging.getLogger(__name__)

# Hedging / opinion phrases that indicate non-factual content
HEDGING_PHRASES = [
    "many believe",
    "some say",
    "experts warn",
    "critics argue",
    "supporters claim",
    "it is believed",
    "it seems",
    "it appears",
    "arguably",
    "reportedly",
    "allegedly",
    "apparently",
    "could be",
    "might be",
    "may be",
    "would be",
    "should be",
    "in my opinion",
    "in our view",
    "we believe",
    "I think",
    "it is thought",
    "widely considered",
    "generally accepted",
    "some experts",
    "many analysts",
    "observers note",
    "sources say",
    "insiders claim",
    "according to sources",
    "unnamed sources",
    "people familiar with",
]

# Subjective adjectives that indicate opinion rather than fact
SUBJECTIVE_ADJECTIVES = {
    "terrible", "wonderful", "horrible", "amazing", "catastrophic",
    "brilliant", "devastating", "outrageous", "stunning", "shameful",
    "heroic", "disgraceful", "remarkable", "pathetic", "glorious",
    "dreadful", "magnificent", "appalling", "sensational", "alarming",
    "shocking", "unprecedented", "controversial", "radical", "extreme",
    "dangerous", "reckless", "irresponsible", "courageous", "cowardly",
    "corrupt", "honest", "evil", "righteous", "absurd", "foolish",
    "genius", "idiotic", "fantastic", "atrocious", "tragic",
    "triumphant", "disastrous", "miraculous", "unacceptable",
    "inexcusable", "deplorable", "admirable", "despicable",
}

# spaCy entity types that count as factual signals
FACTUAL_ENTITY_TYPES = {
    "PERSON", "ORG", "GPE", "LOC", "DATE", "TIME", "MONEY",
    "PERCENT", "QUANTITY", "CARDINAL", "ORDINAL", "EVENT",
    "LAW", "WORK_OF_ART", "NORP", "FAC", "PRODUCT",
}


class FactualDensityScorer:
    """Scores factual density of text using spaCy NER and opinion markers."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        logger.info("Loading spaCy model: en_core_web_sm")
        try:
            self._nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Downloading en_core_web_sm...")
            spacy.cli.download("en_core_web_sm")
            self._nlp = spacy.load("en_core_web_sm")
        self._initialized = True
        logger.info("spaCy model loaded successfully.")

    def _find_opinion_markers(self, text: str) -> list[str]:
        """Find hedging phrases and subjective adjectives in text."""
        markers = []
        text_lower = text.lower()

        # Check hedging phrases
        for phrase in HEDGING_PHRASES:
            if phrase in text_lower:
                markers.append(phrase)

        # Check subjective adjectives
        for word in text_lower.split():
            clean_word = re.sub(r"[^\w]", "", word)
            if clean_word in SUBJECTIVE_ADJECTIVES:
                markers.append(clean_word)

        return markers

    def _extract_factual_signals(self, doc) -> list[str]:
        """Extract named entities and factual signals from a spaCy doc."""
        entities = []
        for ent in doc.ents:
            if ent.label_ in FACTUAL_ENTITY_TYPES:
                entities.append(ent.text)
        return entities

    def _has_numbers(self, text: str) -> int:
        """Count numeric references in text."""
        numbers = re.findall(r"\b\d[\d,.]*\b", text)
        return len(numbers)

    def _has_quotes(self, text: str) -> bool:
        """Check if text contains direct quotes (a factual signal)."""
        return bool(re.search(r'["\u201c\u201d].*?["\u201c\u201d]', text))

    def score_sentences(self, sentences: list[str]) -> list[dict]:
        """
        Score each sentence for factual density.

        Returns:
            List of dicts: {
                "score": int (0-100, higher = more factual),
                "entities": list[str],
                "opinion_markers": list[str]
            }
        """
        results = []

        # Process all sentences through spaCy in one batch for efficiency
        docs = list(self._nlp.pipe(sentences, batch_size=50))

        for doc, sentence in zip(docs, sentences):
            entities = self._extract_factual_signals(doc)
            opinion_markers = self._find_opinion_markers(sentence)
            num_count = self._has_numbers(sentence)
            has_quote = self._has_quotes(sentence)

            # Count tokens (excluding punctuation and stopwords)
            meaningful_tokens = [t for t in doc if not t.is_punct and not t.is_space]
            total_tokens = max(len(meaningful_tokens), 1)

            # Factual signals score
            factual_signals = len(entities) + num_count + (2 if has_quote else 0)

            # Opinion signals score
            opinion_signals = len(opinion_markers)

            # Calculate factual density
            factual_ratio = factual_signals / (factual_signals + opinion_signals + 1)

            # Base score from entity density
            entity_density = min(1.0, len(entities) / max(total_tokens * 0.15, 1))

            # Combined score
            score = int((factual_ratio * 60 + entity_density * 40))

            # Penalize for opinion markers
            penalty = min(30, opinion_signals * 10)
            score = max(0, min(100, score - penalty))

            # Boost for quotes and numbers
            boost = min(20, num_count * 5 + (10 if has_quote else 0))
            score = min(100, score + boost)

            results.append(
                {
                    "score": score,
                    "entities": entities,
                    "opinion_markers": opinion_markers,
                }
            )

        return results

    def aggregate_factual(self, sentence_results: list[dict]) -> dict:
        """
        Compute article-level factual density score.

        Returns:
            {"score": int}
        """
        if not sentence_results:
            return {"score": 0}

        avg = sum(r["score"] for r in sentence_results) / len(sentence_results)
        return {"score": int(avg)}

    def get_nlp(self):
        """Expose the spaCy nlp object for sentence tokenization by the aggregator."""
        return self._nlp
