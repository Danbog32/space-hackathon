#!/bin/bash
# Astro-Zoom Application Restart Script (Bash/Linux/WSL)
# Run this script to restart all services

echo "🔄 Restarting Astro-Zoom Application..."
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Stop all services
echo "Step 1: Stopping all services..."
"$SCRIPT_DIR/stop.sh"

# Wait a bit
echo ""
echo "Waiting 3 seconds before restart..."
sleep 3

# Start all services
echo ""
echo "Step 2: Starting all services..."
"$SCRIPT_DIR/start.sh"

