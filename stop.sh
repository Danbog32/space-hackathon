#!/bin/bash
# Astro-Zoom Application Stop Script (Bash/Linux/WSL)
# Run this script to stop all services

echo "🛑 Stopping Astro-Zoom Application..."
echo "====================================="
echo ""

# Function to kill processes on a specific port
stop_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo "  Stopping processes on port $port..."
        for pid in $pids; do
            echo "    Killing PID $pid"
            kill -9 $pid 2>/dev/null
        done
        echo "  ✓ Stopped"
    else
        echo "  No process found on port $port"
    fi
}

# Stop services on each port
echo "Stopping Web Service (port 3000)..."
stop_port 3000

echo ""
echo "Stopping API Service (port 8000)..."
stop_port 8000

echo ""
echo "Stopping AI Service (port 8001)..."
stop_port 8001

echo ""
echo "Stopping any remaining Node.js processes..."
pkill -f "node.*pnpm" 2>/dev/null && echo "  ✓ Stopped Node.js processes" || echo "  No Node.js processes to stop"

echo ""
echo "Stopping any remaining Python/Uvicorn processes..."
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "  ✓ Stopped Python processes" || echo "  No Python processes to stop"

echo ""
echo "✅ All services stopped!"
echo ""
echo "💡 To start services again, run: ./start.sh"
echo ""

