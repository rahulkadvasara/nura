#!/bin/bash
# Nura Backend - Unix/Linux/macOS Shell Script
# Simple script to start the backend server

echo "🏥 Nura Backend - Development Server"
echo "===================================="

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found, using system Python"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    echo "💡 Copy .env.example to .env and configure your settings"
    exit 1
fi

# Start the server
echo "🚀 Starting server..."
python run.py