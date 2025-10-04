#!/bin/bash
# Astro-Zoom Application Health Check Script (Bash/Linux/WSL)
# Run this script to check the status of all services

echo "🏥 Astro-Zoom Health Check"
echo "====================================="
echo ""

# Function to check if a port is listening
check_port() {
    local port=$1
    local service_name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "✓ $service_name - Port $port is LISTENING"
        return 0
    else
        echo "✗ $service_name - Port $port is NOT RUNNING"
        return 1
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local service_name=$2
    
    if curl -s -f -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
        echo "  └─ Endpoint: $url - OK (HTTP 200)"
        return 0
    else
        echo "  └─ Endpoint: $url - FAILED"
        return 1
    fi
}

# Check ports
echo "Checking Ports:"
echo "---------------"
check_port 3000 "Web Service (Next.js)"
web=$?
check_port 8000 "API Service (FastAPI)"
api=$?
check_port 8001 "AI Service (FastAPI)"
ai=$?

echo ""
echo "Checking HTTP Endpoints:"
echo "------------------------"

if [ $web -eq 0 ]; then
    echo "🌐 Web Service:"
    check_endpoint "http://localhost:3000" "Web"
fi

if [ $api -eq 0 ]; then
    echo "🔌 API Service:"
    check_endpoint "http://localhost:8000/health" "API Health"
    check_endpoint "http://localhost:8000/datasets" "API Datasets"
fi

if [ $ai -eq 0 ]; then
    echo "🤖 AI Service:"
    check_endpoint "http://localhost:8001/health" "AI Health"
fi

# Summary
echo ""
echo "Summary:"
echo "--------"

total_services=3
running_services=0
[ $web -eq 0 ] && ((running_services++))
[ $api -eq 0 ] && ((running_services++))
[ $ai -eq 0 ] && ((running_services++))

echo "Services Running: $running_services / $total_services"

if [ $running_services -eq 0 ]; then
    echo ""
    echo "⚠️  No services are running. Run ./start.sh to start them."
elif [ $running_services -lt $total_services ]; then
    echo ""
    echo "⚠️  Some services are not running. Check the output above."
else
    echo ""
    echo "✅ All services are healthy!"
    echo ""
    echo "📍 Access Points:"
    echo "   🌐 Web:      http://localhost:3000"
    echo "   🔌 API:      http://localhost:8000"
    echo "   📚 API Docs: http://localhost:8000/docs"
    echo "   🤖 AI:       http://localhost:8001"
fi

echo ""

