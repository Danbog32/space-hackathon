# Astro-Zoom Application Status Script
# Shows detailed information about running processes and ports

Write-Host "📊 Astro-Zoom Application Status" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Show processes on our ports
Write-Host "Processes on Application Ports:" -ForegroundColor Yellow
Write-Host "-------------------------------" -ForegroundColor Yellow

$ports = @(3000, 8000, 8001)

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pid in $processIds) {
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Port $port - " -NoNewline
                Write-Host "$($process.Name)" -ForegroundColor Green -NoNewline
                Write-Host " (PID: $pid, Memory: $([math]::Round($process.WorkingSet64/1MB, 2)) MB)"
            }
        }
    }
    else {
        Write-Host "Port $port - " -NoNewline
        Write-Host "Not in use" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "All Node.js Processes:" -ForegroundColor Yellow
Write-Host "---------------------" -ForegroundColor Yellow
$nodeProcs = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcs) {
    $nodeProcs | Format-Table -Property Id, ProcessName, @{Name="Memory (MB)"; Expression={[math]::Round($_.WorkingSet64/1MB, 2)}}, StartTime -AutoSize
}
else {
    Write-Host "No Node.js processes running" -ForegroundColor Gray
}

Write-Host ""
Write-Host "All Python Processes:" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Yellow
$pythonProcs = Get-Process -Name "python", "uvicorn" -ErrorAction SilentlyContinue
if ($pythonProcs) {
    $pythonProcs | Format-Table -Property Id, ProcessName, @{Name="Memory (MB)"; Expression={[math]::Round($_.WorkingSet64/1MB, 2)}}, StartTime -AutoSize
}
else {
    Write-Host "No Python processes running" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Network Connections:" -ForegroundColor Yellow
Write-Host "-------------------" -ForegroundColor Yellow
netstat -an | Select-String "3000|8000|8001" | Select-String "LISTENING"

Write-Host ""
Write-Host "💡 Quick Commands:" -ForegroundColor Cyan
Write-Host "  .\healthcheck.ps1  - Check service health" -ForegroundColor White
Write-Host "  .\stop.ps1         - Stop all services" -ForegroundColor White
Write-Host "  .\start.ps1        - Start all services" -ForegroundColor White
Write-Host "  .\restart.ps1      - Restart all services" -ForegroundColor White
Write-Host ""

