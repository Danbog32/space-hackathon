# Astro-Zoom Application Startup Script
# Run this script to start all services

Write-Host "🌌 Starting Astro-Zoom Application..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Ensure default datasets exist (Andromeda & Earth)
Write-Host "Ensuring default datasets (Andromeda & Earth)..." -ForegroundColor Yellow
python "$PSScriptRoot\infra\ensure_datasets.py" | Write-Host

# Check if services are already running
Write-Host "Checking for running services..." -ForegroundColor Yellow
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port8001 = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue

if ($port3000) {
    Write-Host "⚠️  Port 3000 already in use. Please run stop.ps1 first." -ForegroundColor Red
    exit 1
}

# Start Web Service (Next.js)
Write-Host "🌐 Starting Web Service (port 3000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; pnpm dev" -WindowStyle Normal

# Wait a bit for pnpm to initialize
Start-Sleep -Seconds 3

# Start API Service (FastAPI)
Write-Host "🔌 Starting API Service (port 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\apps\api'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -WindowStyle Normal

# Wait a bit
Start-Sleep -Seconds 2

# Start AI Service (FastAPI)
Write-Host "🤖 Starting AI Service (port 8001)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\apps\ai'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001" -WindowStyle Normal

Write-Host ""
Write-Host "⏳ Waiting for services to start (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "✅ Services started! Running health checks..." -ForegroundColor Cyan
Write-Host ""

# Run health checks
& "$PSScriptRoot\healthcheck.ps1"

Write-Host ""
Write-Host "🎉 Astro-Zoom is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access the application at:" -ForegroundColor White
Write-Host "   🌐 Web:      http://localhost:3000" -ForegroundColor Cyan
Write-Host "   🔌 API:      http://localhost:8000" -ForegroundColor Cyan
Write-Host "   📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   🤖 AI:       http://localhost:8001" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 To stop all services, run: .\stop.ps1" -ForegroundColor Yellow
Write-Host ""

