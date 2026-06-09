# 📰 Bias Detector for News Articles

AI-powered tool that provides **sentence-level** political bias detection, emotional manipulation analysis, and factual density scoring for news articles.

## Features

- **Political Bias Classification** — Each sentence classified as Left / Center / Right using `valurank/distilroberta-mbfc-bias`
- **Emotional Language Detection** — Sentiment analysis via `cardiffnlp/twitter-roberta-base-sentiment` + NRC Emotion Lexicon word flagging
- **Factual Density Scoring** — spaCy NER entity detection + opinion marker flagging per paragraph
- **Article Comparison** — Side-by-side analysis of two articles
- **Analysis History** — SQLite-backed history of past analyses

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy, SQLite |
| Frontend | React, Vite, Axios |
| NLP | spaCy, HuggingFace Transformers, NRCLex |
| Scraping | newspaper4k, BeautifulSoup4 |

## Setup

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

# Download TextBlob corpora (for NRCLex)
python -m textblob.download_corpora

# Start server (port 8000)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

> **Note**: HuggingFace models (~500MB each) will auto-download on first startup. This may take a few minutes.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (port 5173)
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analyze` | Analyze article — `{"text": "..."}` or `{"url": "..."}` |
| `POST` | `/compare` | Compare two articles — `{"article1": {...}, "article2": {...}}` |
| `GET` | `/history` | Last 20 analyses |
| `GET` | `/history/{id}` | Single analysis by ID |

## Models

- **Political Bias**: [`valurank/distilroberta-mbfc-bias`](https://huggingface.co/valurank/distilroberta-mbfc-bias)
- **Sentiment**: [`cardiffnlp/twitter-roberta-base-sentiment`](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment)
- **NER**: spaCy `en_core_web_sm`
- **Emotion Lexicon**: NRC via `NRCLex` library

## License

MIT
