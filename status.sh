#!/bin/bash
# Astro-Zoom Application Status Script (Bash/Linux/WSL)
# Shows detailed information about running processes and ports

echo "📊 Astro-Zoom Application Status"
echo "====================================="
echo ""

# Show processes on our ports
echo "Processes on Application Ports:"
echo "-------------------------------"

for port in 3000 8000 8001; do
    pids=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pids" ]; then
        for pid in $pids; do
            proc_name=$(ps -p $pid -o comm= 2>/dev/null)
            mem=$(ps -p $pid -o rss= 2>/dev/null)
            mem_mb=$((mem / 1024))
            echo "Port $port - $proc_name (PID: $pid, Memory: ${mem_mb} MB)"
        done
    else
        echo "Port $port - Not in use"
    fi
done

echo ""
echo "All Node.js Processes:"
echo "---------------------"
if pgrep -f node >/dev/null 2>&1; then
    ps aux | grep "[n]ode" | awk '{printf "PID: %-7s  Memory: %-6s KB  Command: %s\n", $2, $6, $11}'
else
    echo "No Node.js processes running"
fi

echo ""
echo "All Python Processes:"
echo "--------------------"
if pgrep -f python >/dev/null 2>&1; then
    ps aux | grep "[p]ython" | awk '{printf "PID: %-7s  Memory: %-6s KB  Command: %s\n", $2, $6, $11}'
else
    echo "No Python processes running"
fi

echo ""
echo "Network Connections:"
echo "-------------------"
if command -v netstat >/dev/null 2>&1; then
    netstat -tuln | grep -E "3000|8000|8001" | grep LISTEN
elif command -v ss >/dev/null 2>&1; then
    ss -tuln | grep -E "3000|8000|8001"
else
    lsof -iTCP -sTCP:LISTEN | grep -E "3000|8000|8001"
fi

echo ""
echo "💡 Quick Commands:"
echo "  ./healthcheck.sh  - Check service health"
echo "  ./stop.sh         - Stop all services"
echo "  ./start.sh        - Start all services"
echo "  ./restart.sh      - Restart all services"
echo ""

