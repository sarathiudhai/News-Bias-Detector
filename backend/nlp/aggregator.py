"""
Score Aggregator — orchestrates all three NLP analyzers and assembles
the unified JSON response structure.
"""

import re
import logging
from collections import Counter
from nlp.bias import BiasClassifier, DIRECTION_WEIGHT
from nlp.emotion import EmotionDetector, ALL_EMOTION_WORDS
from nlp.factual import FactualDensityScorer

logger = logging.getLogger(__name__)


def _tokenize_sentences(text: str, nlp) -> list[str]:
    """
    Split article text into sentences using spaCy.
    Filters out very short sentences (< 5 chars) that are likely artifacts.
    """
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) >= 5]
    return sentences


def _group_into_paragraphs(sentences: list[str], original_text: str) -> list[list[int]]:
    """
    Group sentence indices into paragraphs based on double-newline splits
    in the original text. Uses character-offset tracking for robustness
    against duplicate sentences.
    """
    paragraphs_text = original_text.split("\n\n")
    paragraphs_text = [p.strip() for p in paragraphs_text if p.strip()]

    if not paragraphs_text:
        return [list(range(len(sentences)))]

    # Build paragraph boundaries using character offsets
    para_boundaries = []
    search_start = 0
    for para in paragraphs_text:
        idx = original_text.find(para, search_start)
        if idx == -1:
            idx = search_start  # Fallback if not found
        para_boundaries.append((idx, idx + len(para)))
        search_start = idx + len(para)

    # Assign each sentence to a paragraph by finding its position in the text
    sentence_positions = []
    text_cursor = 0
    for sent in sentences:
        pos = original_text.find(sent, text_cursor)
        if pos == -1:
            pos = text_cursor  # Fallback
        sentence_positions.append(pos)
        text_cursor = pos + len(sent)

    # Group sentences into paragraphs
    paragraph_groups = [[] for _ in paragraphs_text]
    for sent_idx, sent_pos in enumerate(sentence_positions):
        assigned = False
        for para_idx, (start, end) in enumerate(para_boundaries):
            if start <= sent_pos < end:
                paragraph_groups[para_idx].append(sent_idx)
                assigned = True
                break
        if not assigned:
            # Assign to the last paragraph as fallback
            paragraph_groups[-1].append(sent_idx)

    # Remove empty paragraph groups
    paragraph_groups = [g for g in paragraph_groups if g]

    # If nothing got assigned, put everything in one group
    if not paragraph_groups:
        paragraph_groups = [list(range(len(sentences)))]

    return paragraph_groups


# ── Readability (Flesch-Kincaid) ─────────────────────────────────────────

def _count_syllables(word: str) -> int:
    """Estimate syllable count using a simple heuristic."""
    word = word.lower().strip()
    if len(word) <= 2:
        return 1
    # Remove trailing silent 'e'
    if word.endswith("e"):
        word = word[:-1]
    # Count vowel groups
    count = len(re.findall(r"[aeiouy]+", word))
    return max(1, count)


def _compute_readability(sentences: list[str]) -> dict:
    """
    Compute Flesch-Kincaid readability metrics.
    Returns grade level (0-18+) and ease score (0-100).
    """
    total_sentences = len(sentences)
    if total_sentences == 0:
        return {"grade_level": 0, "ease_score": 100, "label": "Very Easy"}

    words = []
    for s in sentences:
        words.extend(re.findall(r"[a-zA-Z]+", s))

    total_words = len(words)
    if total_words == 0:
        return {"grade_level": 0, "ease_score": 100, "label": "Very Easy"}

    total_syllables = sum(_count_syllables(w) for w in words)

    # Flesch-Kincaid Grade Level
    grade = 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59
    grade = max(0, min(18, round(grade, 1)))

    # Flesch Reading Ease
    ease = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
    ease = max(0, min(100, round(ease)))

    # Label
    if ease >= 80:
        label = "Very Easy"
    elif ease >= 60:
        label = "Standard"
    elif ease >= 40:
        label = "Moderate"
    elif ease >= 20:
        label = "Difficult"
    else:
        label = "Very Difficult"

    return {"grade_level": grade, "ease_score": int(ease), "label": label}


# ── Topic Detection ──────────────────────────────────────────────────────

# Map spaCy entity types to human-readable categories
TOPIC_CATEGORY_MAP = {
    "PERSON": "People",
    "ORG": "Organizations",
    "GPE": "Locations",
    "LOC": "Locations",
    "EVENT": "Events",
    "LAW": "Legislation",
    "NORP": "Groups",
    "FAC": "Facilities",
    "PRODUCT": "Products",
    "WORK_OF_ART": "Works",
}


def _detect_topics(text: str, nlp) -> list[dict]:
    """
    Extract named entities from the full article and group by category.
    Returns top entities with their type and count.
    """
    doc = nlp(text)
    entity_counter = Counter()
    entity_types = {}

    for ent in doc.ents:
        if ent.label_ in TOPIC_CATEGORY_MAP:
            name = ent.text.strip()
            if len(name) > 1:
                entity_counter[name] += 1
                entity_types[name] = TOPIC_CATEGORY_MAP[ent.label_]

    # Return top 12 entities
    topics = []
    for name, count in entity_counter.most_common(12):
        topics.append({
            "name": name,
            "category": entity_types[name],
            "count": count,
        })

    return topics


# ── Word Cloud Data ──────────────────────────────────────────────────────

def _build_word_cloud(sentence_emotion_results: list[dict]) -> list[dict]:
    """
    Aggregate flagged emotion words across all sentences with frequencies.
    Returns a list of {word, category, count} sorted by count descending.
    """
    word_counter = Counter()

    for result in sentence_emotion_results:
        for word in result.get("flagged_words", []):
            word_counter[word] += 1

    cloud = []
    for word, count in word_counter.most_common(40):
        categories = ALL_EMOTION_WORDS.get(word, ["unknown"])
        cloud.append({
            "word": word,
            "category": categories[0] if categories else "unknown",
            "count": count,
        })

    return cloud


# ── Bias Flow ────────────────────────────────────────────────────────────

def _compute_bias_flow(bias_results: list[dict]) -> list[dict]:
    """
    Compute per-sentence bias direction for the flow chart.
    Returns list of {index, direction, label, score}.
    direction: -1.0 (Left) to +1.0 (Right), 0 = Center.
    """
    flow = []
    for i, r in enumerate(bias_results):
        raw_label = r.get("raw_label", "unknown")
        direction = DIRECTION_WEIGHT.get(raw_label, 0.0)
        confidence = r["score"] / 100.0
        flow.append({
            "index": i,
            "direction": round(direction * confidence, 3),
            "label": r["label"],
            "score": r["score"],
        })
    return flow


# ── Bias Distribution ────────────────────────────────────────────────────

def _compute_bias_distribution(bias_results: list[dict]) -> dict:
    """
    Count sentences by bias label.
    Returns {left: int, center: int, right: int, total: int}.
    """
    dist = {"left": 0, "center": 0, "right": 0}
    for r in bias_results:
        label = r["label"].lower()
        if label in dist:
            dist[label] += 1
    dist["total"] = len(bias_results)
    return dist


# ── Main Pipeline ────────────────────────────────────────────────────────

def analyze_article(title: str, text: str) -> dict:
    """
    Full analysis pipeline: bias + emotion + factual density + readability + topics.

    Args:
        title: Article title.
        text: Article body text.

    Returns:
        Unified JSON structure with article-level and sentence-level scores.
    """
    # Get singleton instances
    bias_clf = BiasClassifier()
    emotion_det = EmotionDetector()
    factual_scorer = FactualDensityScorer()

    # Tokenize into sentences using shared spaCy model
    nlp = factual_scorer.get_nlp()
    sentences = _tokenize_sentences(text, nlp)

    if not sentences:
        return {
            "article_title": title,
            "overall_bias": {"label": "Center", "score": 0},
            "overall_emotion": {"score": 0},
            "overall_factual_density": {"score": 0},
            "readability": {"grade_level": 0, "ease_score": 100, "label": "Very Easy"},
            "topics": [],
            "bias_distribution": {"left": 0, "center": 0, "right": 0, "total": 0},
            "word_cloud": [],
            "bias_flow": [],
            "sentences": [],
            "paragraphs": [],
        }

    logger.info(f"Analyzing {len(sentences)} sentences for article: {title[:50]}")

    # Run all three analyzers
    bias_results = bias_clf.classify_sentences(sentences)
    emotion_results = emotion_det.analyze_sentences(sentences)
    factual_results = factual_scorer.score_sentences(sentences)

    # Aggregate article-level scores
    overall_bias = bias_clf.aggregate_bias(bias_results)
    overall_emotion = emotion_det.aggregate_emotion(emotion_results)
    overall_factual = factual_scorer.aggregate_factual(factual_results)

    # ── NEW: Compute additional metrics ──
    readability = _compute_readability(sentences)
    topics = _detect_topics(text, nlp)
    bias_distribution = _compute_bias_distribution(bias_results)
    word_cloud = _build_word_cloud(emotion_results)
    bias_flow = _compute_bias_flow(bias_results)

    # Build sentence-level combined results
    sentence_data = []
    for i, sentence in enumerate(sentences):
        bias = bias_results[i] if i < len(bias_results) else {"label": "Center", "score": 0, "uncertain": True}
        emotion = emotion_results[i] if i < len(emotion_results) else {"label": "neutral", "score": 0, "flagged_words": [], "uncertain": True}
        factual = factual_results[i] if i < len(factual_results) else {"score": 0, "entities": [], "opinion_markers": []}

        uncertain = bias.get("uncertain", False) or emotion.get("uncertain", False)

        sentence_data.append(
            {
                "text": sentence,
                "bias": {
                    "label": bias["label"],
                    "score": bias["score"],
                },
                "emotion": {
                    "label": emotion["label"],
                    "score": emotion["score"],
                    "flagged_words": emotion["flagged_words"],
                },
                "factual": {
                    "score": factual["score"],
                    "entities": factual["entities"],
                },
                "uncertain": uncertain,
            }
        )

    # Build paragraph-level factual density
    paragraph_groups = _group_into_paragraphs(sentences, text)
    paragraph_scores = []
    for group in paragraph_groups:
        if group:
            avg = sum(factual_results[i]["score"] for i in group if i < len(factual_results)) / len(group)
            paragraph_scores.append({"sentence_indices": group, "factual_score": int(avg)})

    return {
        "article_title": title,
        "overall_bias": overall_bias,
        "overall_emotion": overall_emotion,
        "overall_factual_density": overall_factual,
        "readability": readability,
        "topics": topics,
        "bias_distribution": bias_distribution,
        "word_cloud": word_cloud,
        "bias_flow": bias_flow,
        "sentences": sentence_data,
        "paragraphs": paragraph_scores,
    }
