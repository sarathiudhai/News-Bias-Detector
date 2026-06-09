#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting Render build process..."

# Upgrade pip
python -m pip install --upgrade pip

# Install CPU-only torch to save 2GB of space and RAM
echo "Installing CPU-only PyTorch..."
pip install torch==2.4.1+cpu --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the requirements
echo "Installing remaining requirements..."
pip install -r requirements.txt

# Download spaCy model
echo "Downloading spaCy en_core_web_sm model..."
python -m spacy download en_core_web_sm

echo "Build complete!"
