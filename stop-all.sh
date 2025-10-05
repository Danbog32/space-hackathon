#!/bin/bash
# Stop all services by killing processes on their ports

echo "🛑 Stopping all services..."
echo ""

ports=(8000 8001 3000)
killed_any=false

for port in "${ports[@]}"; do
    echo "Checking port $port..."
    
    # Find process using the port
    if command -v lsof > /dev/null 2>&1; then
        # Using lsof (macOS, Linux)
        pid=$(lsof -ti:$port 2>/dev/null)
    elif command -v ss > /dev/null 2>&1; then
        # Using ss (Linux)
        pid=$(ss -lptn "sport = :$port" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | head -1)
    elif command -v netstat > /dev/null 2>&1; then
        # Using netstat (fallback)
        pid=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
    else
        echo "  ⚠️  No suitable command found to check port"
        continue
    fi
    
    if [ -n "$pid" ]; then
        process_name=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        echo "  ⚠️  Killing process: $process_name (PID: $pid)"
        kill -9 $pid 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Process stopped"
            killed_any=true
        else
            echo "  ❌ Failed to kill process $pid"
        fi
    else
        echo "  ✓ Port $port is free"
    fi
    
    echo ""
done

if [ "$killed_any" = true ]; then
    echo "⏳ Waiting for processes to fully terminate..."
    sleep 2
    echo ""
fi

echo "✅ All services stopped!"
echo ""
echo "Ports checked: 8000 (API), 8001 (AI), 3000 (Web)"

