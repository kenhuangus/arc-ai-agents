#!/bin/bash

# Arc Coordination System - Quick Start Script

set -e

echo "🌐 Arc Coordination System - Quick Start"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f "config/.env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp config/.env.example config/.env
    echo "✅ Created config/.env - Please edit with your settings"
    echo "❌ Exiting. Please configure config/.env and run again."
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✅ Dependencies installed"
echo ""

# Check Foundry
if ! command -v forge &> /dev/null; then
    echo "⚠️  Foundry not found. Smart contracts will not be available."
    echo "   Install from: https://github.com/foundry-rs/foundry"
else
    echo "✅ Foundry found: $(forge --version | head -1)"

    # Build contracts if not built
    if [ ! -d "contracts/out" ]; then
        echo "🔨 Building smart contracts..."
        cd contracts
        forge build
        cd ..
        echo "✅ Contracts built"
    fi
fi

echo ""
echo "🚀 Starting services..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $(jobs -p) 2>/dev/null || true
    wait
    echo "✅ All services stopped"
}

trap cleanup EXIT

# Start services in background
echo "Starting Indexer..."
python3 services/indexer.py > logs/indexer.log 2>&1 &
INDEXER_PID=$!

sleep 2

echo "Starting Auction Engine..."
python3 services/auction_engine.py > logs/auction_engine.log 2>&1 &
ENGINE_PID=$!

sleep 2

echo "Starting REST API..."
python3 services/api.py > logs/api.log 2>&1 &
API_PID=$!

sleep 3

echo ""
echo "✅ All services started!"
echo ""
echo "Service Status:"
echo "  - Indexer (PID: $INDEXER_PID)"
echo "  - Auction Engine (PID: $ENGINE_PID)"
echo "  - REST API (PID: $API_PID)"
echo ""
echo "📊 Starting Streamlit Dashboard..."
echo ""
echo "Dashboard will open at: http://localhost:8501"
echo "API available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start Streamlit (foreground)
streamlit run ui/streamlit_app.py

# Cleanup will be called automatically on exit
