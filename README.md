# 📰 Bias Detector for News Articles

AI-powered tool that provides **sentence-level** political bias detection, emotional manipulation analysis, and factual density scoring for news articles.

## Features

- **Political Bias Classification** — Each sentence classified as Left / Center / Right using `valurank/distilroberta-mbfc-bias` (via HuggingFace Inference API)
- **Emotional Language Detection** — Sentiment analysis via TextBlob + curated NRC Emotion Lexicon word flagging
- **Factual Density Scoring** — spaCy NER entity detection + opinion marker flagging per paragraph
- **Article Comparison** — Side-by-side analysis of two articles
- **Analysis History** — SQLite-backed history of past analyses

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy, SQLite |
| Frontend | React, Vite, Axios |
| NLP | spaCy, TextBlob, NRC Emotion Lexicon |
| Bias Model | HuggingFace Inference API (`valurank/distilroberta-mbfc-bias`) |
| Scraping | newspaper4k, BeautifulSoup4 |

## Setup

### Prerequisites

1. Get a **free HuggingFace API token** at https://huggingface.co/settings/tokens
2. Copy `.env.example` to `.env` and set your `HF_API_TOKEN`

### Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Download TextBlob corpora
python -m textblob.download_corpora

# Set your HuggingFace API token
export HF_API_TOKEN=hf_your_token_here

# Start server (port 8000)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (port 5173)
npm run dev
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_API_TOKEN` | Yes | HuggingFace API token for bias classification |
| `CORS_ORIGINS` | No | Comma-separated allowed origins (default: `http://localhost:5173`) |
| `DATABASE_URL` | No | Database URL (default: `sqlite:///./bias_detector.db`) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analyze` | Analyze article — `{"text": "..."}` or `{"url": "..."}` |
| `POST` | `/compare` | Compare two articles — `{"article1": {...}, "article2": {...}}` |
| `GET` | `/history` | Last 20 analyses |
| `GET` | `/history/{id}` | Single analysis by ID |
| `DELETE` | `/history/{id}` | Delete analysis by ID |

## Rate Limits

- `/analyze` — 10 requests/minute per IP
- `/compare` — 5 requests/minute per IP

## Models

- **Political Bias**: [`valurank/distilroberta-mbfc-bias`](https://huggingface.co/valurank/distilroberta-mbfc-bias) (remote via HF Inference API)
- **Sentiment**: TextBlob polarity + subjectivity analysis
- **Emotion Lexicon**: Curated NRC-derived lexicon (~170 words across 8 categories)
- **NER**: spaCy `en_core_web_sm`

## Deployment (Render)

The project is configured for Render deployment via `render.yaml`:
- **Backend**: Python web service (lightweight — no PyTorch required)
- **Frontend**: Static site with auto-injected API URL

Set `HF_API_TOKEN` as an environment variable in your Render dashboard.

## License

MIT
