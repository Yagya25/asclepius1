#!/bin/bash
# Asclepius - Quick Setup Script

echo "Setting up Asclepius..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
pip install ruff pytest httpx

# Create uploads directory
mkdir -p uploads

# Run tests
echo "Running tests..."
pytest tests/ -v || true

# Start server
echo "Starting server..."
echo "API docs will be at http://localhost:8000/docs"
uvicorn app.main:app --reload
