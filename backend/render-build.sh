#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting Render build process..."

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements (no PyTorch needed — bias model runs via HF Inference API)
echo "Installing requirements..."
pip install -r requirements.txt

# Download spaCy model
echo "Downloading spaCy en_core_web_sm model..."
python -m spacy download en_core_web_sm

# Download TextBlob corpora (for sentiment analysis)
echo "Downloading TextBlob corpora..."
python -m textblob.download_corpora

echo "Build complete!"
