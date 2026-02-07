#!/bin/bash

# DocAI Backend Startup Script

echo "🚀 Starting DocAI Backend..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found, copying from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file with your configuration"
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Initialize database if needed
echo "🗄️  Initializing database..."
python init_db.py

# Start the server
echo "🚀 Starting server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
