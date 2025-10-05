# Astro-Zoom Application Health Check Script
# Run this script to check the status of all services

Write-Host "🏥 Astro-Zoom Health Check" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a port is listening
function Test-Port {
    param([int]$Port, [string]$ServiceName)
    
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "✓ $ServiceName" -ForegroundColor Green -NoNewline
        Write-Host " - Port $Port is " -NoNewline
        Write-Host "LISTENING" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "✗ $ServiceName" -ForegroundColor Red -NoNewline
        Write-Host " - Port $Port is " -NoNewline
        Write-Host "NOT RUNNING" -ForegroundColor Red
        return $false
    }
}

# Function to check HTTP endpoint
function Test-Endpoint {
    param([string]$Url, [string]$ServiceName)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  └─ Endpoint: $Url - " -NoNewline
            Write-Host "OK (HTTP $($response.StatusCode))" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "  └─ Endpoint: $Url - " -NoNewline
        Write-Host "FAILED" -ForegroundColor Red
        return $false
    }
}

# Check ports
Write-Host "Checking Ports:" -ForegroundColor Yellow
Write-Host "---------------" -ForegroundColor Yellow
$web = Test-Port -Port 3000 -ServiceName "Web Service (Next.js)"
$api = Test-Port -Port 8000 -ServiceName "API Service (FastAPI)"
$ai = Test-Port -Port 8001 -ServiceName "AI Service (FastAPI)"

Write-Host ""
Write-Host "Checking HTTP Endpoints:" -ForegroundColor Yellow
Write-Host "------------------------" -ForegroundColor Yellow

if ($web) {
    Write-Host "🌐 Web Service:" -ForegroundColor Cyan
    Test-Endpoint -Url "http://localhost:3000" -ServiceName "Web"
}

if ($api) {
    Write-Host "🔌 API Service:" -ForegroundColor Cyan
    Test-Endpoint -Url "http://localhost:8000/health" -ServiceName "API Health"
    Test-Endpoint -Url "http://localhost:8000/datasets" -ServiceName "API Datasets"
}

if ($ai) {
    Write-Host "🤖 AI Service:" -ForegroundColor Cyan
    Test-Endpoint -Url "http://localhost:8001/health" -ServiceName "AI Health"
}

# Summary
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "--------" -ForegroundColor Yellow

$totalServices = 3
$runningServices = 0
if ($web) { $runningServices++ }
if ($api) { $runningServices++ }
if ($ai) { $runningServices++ }

Write-Host "Services Running: $runningServices / $totalServices" -ForegroundColor $(if ($runningServices -eq $totalServices) { "Green" } else { "Yellow" })

if ($runningServices -eq 0) {
    Write-Host ""
    Write-Host "⚠️  No services are running. Run .\start.ps1 to start them." -ForegroundColor Red
}
elseif ($runningServices -lt $totalServices) {
    Write-Host ""
    Write-Host "⚠️  Some services are not running. Check the output above." -ForegroundColor Yellow
}
else {
    Write-Host ""
    Write-Host "✅ All services are healthy!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Access Points:" -ForegroundColor White
    Write-Host "   🌐 Web:      http://localhost:3000" -ForegroundColor Cyan
    Write-Host "   🔌 API:      http://localhost:8000" -ForegroundColor Cyan
    Write-Host "   📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "   🤖 AI:       http://localhost:8001" -ForegroundColor Cyan
}

Write-Host ""

