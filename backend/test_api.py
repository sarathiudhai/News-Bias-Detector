"""
Basic test suite for the Bias Detector backend.
Run with: pytest test_api.py -v
"""

import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

def test_root_health_check():
    """GET / should return status ok."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Bias Detector" in data["service"]


# ---------------------------------------------------------------------------
# Input Validation
# ---------------------------------------------------------------------------

def test_analyze_no_input():
    """POST /analyze with no text or url should return 400."""
    response = client.post("/analyze", json={})
    assert response.status_code == 400


def test_analyze_empty_text():
    """POST /analyze with empty text should return 400."""
    response = client.post("/analyze", json={"text": ""})
    assert response.status_code == 400


def test_analyze_text_too_short():
    """POST /analyze with very short text should return 400."""
    response = client.post("/analyze", json={"text": "Too short."})
    assert response.status_code == 400


def test_analyze_text_too_long():
    """POST /analyze with text exceeding max length should return 422."""
    long_text = "A" * 60000
    response = client.post("/analyze", json={"text": long_text})
    assert response.status_code == 422  # Pydantic validation error


def test_compare_missing_article():
    """POST /compare with missing article should return 400."""
    response = client.post("/compare", json={
        "article1": {"text": "Some article text here that is long enough for analysis."},
        "article2": {}
    })
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Scraper Tests
# ---------------------------------------------------------------------------

def test_scraper_clean_text():
    """Test text cleaning removes ads and normalizes whitespace."""
    from scraper import _clean_text

    dirty = "Read more: Some actual content here. Follow us on Twitter  Copyright © 2024"
    clean = _clean_text(dirty)
    assert "Read more" not in clean
    assert "Follow us on Twitter" not in clean
    assert "Copyright" not in clean
    assert "Some actual content here." in clean


def test_scraper_parse_raw_text():
    """Test raw text parsing extracts title from first line."""
    from scraper import parse_input

    text = "My Article Title\nThis is the body of the article with enough content to be meaningful."
    result = parse_input(text=text)
    assert result["title"] == "My Article Title"
    assert "body of the article" in result["text"]
    assert result["url"] is None


# ---------------------------------------------------------------------------
# NLP Module Tests
# ---------------------------------------------------------------------------

def test_emotion_detector():
    """Test EmotionDetector produces valid output."""
    from nlp.emotion import EmotionDetector

    detector = EmotionDetector()
    results = detector.analyze_sentences([
        "This is a terrible disaster that has shocked the nation.",
        "The weather is sunny today.",
    ])

    assert len(results) == 2
    for r in results:
        assert "label" in r
        assert "score" in r
        assert "flagged_words" in r
        assert r["label"] in ("negative", "neutral", "positive")
        assert 0 <= r["score"] <= 100


def test_emotion_aggregate():
    """Test emotion aggregation returns correct structure."""
    from nlp.emotion import EmotionDetector

    detector = EmotionDetector()
    results = [{"score": 60}, {"score": 40}, {"score": 80}]
    agg = detector.aggregate_emotion(results)
    assert agg["score"] == 60  # (60+40+80) / 3 = 60


def test_factual_scorer():
    """Test FactualDensityScorer produces valid output."""
    from nlp.factual import FactualDensityScorer

    scorer = FactualDensityScorer()
    results = scorer.score_sentences([
        "President Biden met with German Chancellor Scholz on January 15, 2024.",
        "Many believe this could be a terrible mistake.",
    ])

    assert len(results) == 2
    for r in results:
        assert "score" in r
        assert "entities" in r
        assert "opinion_markers" in r
        assert 0 <= r["score"] <= 100

    # First sentence should have higher factual score (has entities + date)
    assert results[0]["score"] >= results[1]["score"]


def test_bias_classifier_mock():
    """Test BiasClassifier with mocked API response."""
    from nlp.bias import BiasClassifier

    classifier = BiasClassifier()

    mock_response = [
        [
            {"label": "leastbiased", "score": 0.85},
            {"label": "left", "score": 0.10},
            {"label": "right", "score": 0.05},
        ]
    ]

    with patch.object(classifier, '_call_hf_api', return_value=mock_response):
        results = classifier.classify_sentences(["The senate voted 52-48 on the bill."])

    assert len(results) == 1
    assert results[0]["label"] == "Center"
    assert results[0]["score"] == 85
    assert results[0]["uncertain"] is False


def test_bias_aggregate():
    """Test bias aggregation logic."""
    from nlp.bias import BiasClassifier

    classifier = BiasClassifier()
    results = [
        {"label": "Center", "score": 80, "raw_label": "leastbiased"},
        {"label": "Center", "score": 70, "raw_label": "leastbiased"},
        {"label": "Left", "score": 60, "raw_label": "left"},
    ]
    agg = classifier.aggregate_bias(results)
    assert "label" in agg
    assert "score" in agg
    assert agg["label"] in ("Left", "Center", "Right")


# ---------------------------------------------------------------------------
# History Endpoints
# ---------------------------------------------------------------------------

def test_history_empty():
    """GET /history should return a list."""
    response = client.get("/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_history_not_found():
    """GET /history/99999 should return 404."""
    response = client.get("/history/99999")
    assert response.status_code == 404


def test_delete_not_found():
    """DELETE /history/99999 should return 404."""
    response = client.delete("/history/99999")
    assert response.status_code == 404
