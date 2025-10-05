# Astro-Zoom Application Restart Script
# Run this script to restart all services

Write-Host "🔄 Restarting Astro-Zoom Application..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Stop all services
Write-Host "Step 1: Stopping all services..." -ForegroundColor Yellow
& "$PSScriptRoot\stop.ps1"

# Wait a bit
Write-Host ""
Write-Host "Waiting 3 seconds before restart..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start all services
Write-Host ""
Write-Host "Step 2: Starting all services..." -ForegroundColor Yellow
& "$PSScriptRoot\start.ps1"

