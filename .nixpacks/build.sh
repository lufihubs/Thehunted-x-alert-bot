#!/bin/bash
set -e

echo "🏗️ Starting custom build process..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv /app/venv

# Activate virtual environment and install dependencies
echo "⚡ Installing dependencies in virtual environment..."
/app/venv/bin/pip install --upgrade pip
/app/venv/bin/pip install -r requirements.txt

echo "✅ Build completed successfully!"
