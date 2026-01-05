#!/bin/bash

# VeriShield Backend Startup Script

echo "🚀 Starting VeriShield Backend..."

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Start the server
echo "✅ Starting FastAPI server on http://localhost:8000"
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
