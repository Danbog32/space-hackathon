#!/bin/bash

# Astro-Zoom: Start All Services
# This script starts all three services in the background

set -e

# Get the script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting Astro-Zoom Services..."

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Stopping all services..."
    jobs -p | xargs -r kill
    exit 0
}

# Set up cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start AI Service (port 8001)
echo "🤖 Starting AI Service on port 8001..."
cd "$SCRIPT_DIR/ai" && python simple_app.py &
AI_PID=$!

# Wait a moment for AI service to start
sleep 2

# Start API Backend (port 8000)
echo "🔌 Starting API Backend on port 8000..."
cd "$SCRIPT_DIR/apps/api" && make dev &
API_PID=$!

# Wait a moment for API to start
sleep 2

# Start Frontend (port 3000)
echo "🌐 Starting Frontend on port 3000..."
cd "$SCRIPT_DIR/apps/web" && pnpm dev &
WEB_PID=$!

echo ""
echo "✅ All services started!"
echo "📊 Service Status:"
echo "   - AI Service:    http://localhost:8001"
echo "   - API Backend:   http://localhost:8000"
echo "   - Frontend:      http://localhost:3000"
echo ""
echo "🎯 Open http://localhost:3000 to use the application"
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Wait for all background processes
wait
