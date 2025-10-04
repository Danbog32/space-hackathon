# Astro-Zoom Application Stop Script
# Run this script to stop all services

Write-Host "🛑 Stopping Astro-Zoom Application..." -ForegroundColor Red
Write-Host "=====================================" -ForegroundColor Red
Write-Host ""

# Function to kill processes on a specific port
function Stop-ProcessOnPort {
    param([int]$Port)
    
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($connections) {
        $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pid in $processIds) {
            try {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "  Stopping process $($process.Name) (PID: $pid) on port $Port..." -ForegroundColor Yellow
                    Stop-Process -Id $pid -Force -ErrorAction Stop
                    Write-Host "  ✓ Stopped" -ForegroundColor Green
                }
            }
            catch {
                Write-Host "  ✗ Failed to stop PID $pid" -ForegroundColor Red
            }
        }
    }
    else {
        Write-Host "  No process found on port $Port" -ForegroundColor Gray
    }
}

# Stop services on each port
Write-Host "Stopping Web Service (port 3000)..." -ForegroundColor Yellow
Stop-ProcessOnPort -Port 3000

Write-Host ""
Write-Host "Stopping API Service (port 8000)..." -ForegroundColor Yellow
Stop-ProcessOnPort -Port 8000

Write-Host ""
Write-Host "Stopping AI Service (port 8001)..." -ForegroundColor Yellow
Stop-ProcessOnPort -Port 8001

Write-Host ""
Write-Host "Stopping any remaining Node.js processes..." -ForegroundColor Yellow
$nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "" }
if ($nodeProcesses) {
    foreach ($proc in $nodeProcesses) {
        try {
            Write-Host "  Stopping Node.js process (PID: $($proc.Id))..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
        }
        catch {
            Write-Host "  ✗ Failed to stop PID $($proc.Id)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "Stopping any remaining Python/Uvicorn processes..." -ForegroundColor Yellow
$pythonProcesses = Get-Process -Name "python", "uvicorn" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "" }
if ($pythonProcesses) {
    foreach ($proc in $pythonProcesses) {
        try {
            Write-Host "  Stopping Python process (PID: $($proc.Id))..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
        }
        catch {
            Write-Host "  ✗ Failed to stop PID $($proc.Id)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "✅ All services stopped!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 To start services again, run: .\start.ps1" -ForegroundColor Yellow
Write-Host ""

