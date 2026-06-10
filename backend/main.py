"""
FastAPI application — Bias Detector for News Articles.

Endpoints:
  POST /analyze — Analyze a single article (text or URL)
  POST /compare — Compare two articles side by side
  GET  /history — Last 20 analyses
  GET  /history/{id} — Single analysis by ID
  DELETE /history/{id} — Delete single analysis by ID
"""

import os
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from database import get_db, init_db
from models import Analysis
from scraper import parse_input, ScrapingError
from nlp.aggregator import analyze_article

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Startup — preload lightweight models once
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models at startup so first request isn't slow."""
    logger.info("=== Initializing database ===")
    init_db()

    logger.info("=== Preloading NLP models ===")
    from nlp.bias import BiasClassifier
    from nlp.emotion import EmotionDetector
    from nlp.factual import FactualDensityScorer

    BiasClassifier()       # Initializes HF API client (no download)
    EmotionDetector()      # Lightweight TextBlob
    FactualDensityScorer() # spaCy en_core_web_sm (~15MB)
    logger.info("=== All models loaded. Server ready. ===")
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Bias Detector for News Articles",
    description="Detect political bias, emotional manipulation, and factual density in news articles.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — read origins from env var, fallback to localhost
cors_origins_str = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
# Parse origins, strip whitespace, and automatically remove any trailing slashes
cors_origins = []
for origin in cors_origins_str.split(","):
    origin_clean = origin.strip()
    if origin_clean:
        if origin_clean.endswith("/"):
            origin_clean = origin_clean[:-1]
        cors_origins.append(origin_clean)

logger.info(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_INPUT_LENGTH = 50000  # Max characters for article text input

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v):
        if v is not None and len(v) > MAX_INPUT_LENGTH:
            raise ValueError(
                f"Text too long ({len(v)} chars). Maximum is {MAX_INPUT_LENGTH} characters."
            )
        return v


class CompareRequest(BaseModel):
    article1: AnalyzeRequest
    article2: AnalyzeRequest


class AnalysisHistoryItem(BaseModel):
    id: int
    title: str
    url: Optional[str]
    bias_label: Optional[str]
    bias_score: Optional[int]
    emotion_score: Optional[int]
    factual_score: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_analysis(req: AnalyzeRequest, db: Session) -> dict:
    """Shared analysis logic for both /analyze and /compare."""
    # 1. Ingest article
    try:
        article = parse_input(text=req.text, url=req.url)
    except ScrapingError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not article.get("text") or len(article["text"].strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Article text is too short to analyze. Please provide more content or try a different URL.",
        )

    # 2. Run NLP analysis
    try:
        result = analyze_article(article["title"], article["text"])
    except Exception as e:
        logger.exception("NLP analysis failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # 3. Save to database
    try:
        analysis_record = Analysis(
            title=result["article_title"],
            url=article.get("url"),
            input_text=article["text"][:10000],  # Truncate for storage
            result_json=json.dumps(result),
            bias_label=result["overall_bias"]["label"],
            bias_score=result["overall_bias"]["score"],
            emotion_score=result["overall_emotion"]["score"],
            factual_score=result["overall_factual_density"]["score"],
        )
        db.add(analysis_record)
        db.commit()
        db.refresh(analysis_record)
        result["id"] = analysis_record.id
    except Exception as e:
        logger.warning(f"Failed to save analysis to database: {e}")
        db.rollback()

    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/analyze")
@limiter.limit("10/minute")
def analyze(request: Request, req: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Analyze a single article for bias, emotion, and factual density.
    Accepts either {text: string} or {url: string}.
    """
    if not req.text and not req.url:
        raise HTTPException(status_code=400, detail="Please provide either 'text' or 'url'.")

    return _run_analysis(req, db)


@app.post("/compare")
@limiter.limit("5/minute")
def compare(request: Request, req: CompareRequest, db: Session = Depends(get_db)):
    """
    Compare two articles side by side.
    Each article can be provided as text or URL.
    """
    if not (req.article1.text or req.article1.url):
        raise HTTPException(status_code=400, detail="Article 1: Please provide either 'text' or 'url'.")
    if not (req.article2.text or req.article2.url):
        raise HTTPException(status_code=400, detail="Article 2: Please provide either 'text' or 'url'.")

    result1 = _run_analysis(req.article1, db)
    result2 = _run_analysis(req.article2, db)

    return {"article1": result1, "article2": result2}


@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    """Return the last 20 analyses, most recent first."""
    analyses = (
        db.query(Analysis)
        .order_by(Analysis.created_at.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "bias_label": a.bias_label,
            "bias_score": a.bias_score,
            "emotion_score": a.emotion_score,
            "factual_score": a.factual_score,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in analyses
    ]


@app.get("/history/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Return a single saved analysis by ID."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis with id {analysis_id} not found.")

    try:
        result = json.loads(analysis.result_json)
        result["id"] = analysis.id
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Stored analysis data is corrupted.")


@app.delete("/history/{analysis_id}")
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Delete a single analysis by ID."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis with id {analysis_id} not found.")

    db.delete(analysis)
    db.commit()
    return {"status": "deleted", "id": analysis_id}


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Bias Detector for News Articles", "version": "1.0.0"}
