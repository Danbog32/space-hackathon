# Stop all services by killing processes on their ports

Write-Host "Stopping all services..." -ForegroundColor Cyan
Write-Host ""

$ports = @(8000, 8001, 3000)
$killedAny = $false

foreach ($port in $ports) {
    Write-Host "Checking port $port..." -ForegroundColor Yellow
    
    try {
        # Get process using the port
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        
        if ($connections) {
            foreach ($conn in $connections) {
                $processId = $conn.OwningProcess
                
                if ($processId -gt 0) {
                    try {
                        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                        
                        if ($process) {
                            $processName = $process.ProcessName
                            Write-Host "  Killing process: $processName (PID: $processId)" -ForegroundColor Red
                            Stop-Process -Id $processId -Force -ErrorAction Stop
                            $killedAny = $true
                            Write-Host "  Process stopped" -ForegroundColor Green
                        }
                    }
                    catch {
                        Write-Host "  Failed to kill process $processId : $_" -ForegroundColor Red
                    }
                }
            }
        }
        else {
            Write-Host "  Port $port is free" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  Could not check port $port : $_" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

if ($killedAny) {
    Write-Host "Waiting for processes to fully terminate..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    Write-Host ""
}

Write-Host "All services stopped!" -ForegroundColor Green
Write-Host ""
Write-Host "Ports checked: 8000 (API), 8001 (AI), 3000 (Web)" -ForegroundColor Gray
