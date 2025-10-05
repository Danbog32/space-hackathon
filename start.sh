#!/bin/bash
# Astro-Zoom Application Startup Script (Bash/Linux/WSL)
# Run this script to start all services

echo "🌌 Starting Astro-Zoom Application..."
echo "====================================="
echo ""

# Ensure default datasets exist (Andromeda & Earth)
echo "Ensuring default datasets (Andromeda & Earth)..."
python3 infra/ensure_datasets.py || true

# Check if services are already running
echo "Checking for running services..."
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 3000 already in use. Please run ./stop.sh first."
    exit 1
fi

# Start Web Service (Next.js)
echo "🌐 Starting Web Service (port 3000)..."
cd "$(dirname "$0")"
pnpm dev > /dev/null 2>&1 &
sleep 3

# Start API Service (FastAPI)
echo "🔌 Starting API Service (port 8000)..."
cd apps/api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
cd ../..
sleep 2

# Start AI Service (FastAPI)
echo "🤖 Starting AI Service (port 8001)..."
cd apps/ai
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 > /dev/null 2>&1 &
cd ../..

echo ""
echo "⏳ Waiting for services to start (15 seconds)..."
sleep 15

echo ""
echo "✅ Services started! Running health checks..."
echo ""

# Run health checks
./healthcheck.sh

echo ""
echo "🎉 Astro-Zoom is ready!"
echo ""
echo "📍 Access the application at:"
echo "   🌐 Web:      http://localhost:3000"
echo "   🔌 API:      http://localhost:8000"
echo "   📚 API Docs: http://localhost:8000/docs"
echo "   🤖 AI:       http://localhost:8001"
echo ""
echo "💡 To stop all services, run: ./stop.sh"
echo ""

