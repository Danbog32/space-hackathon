[CmdletBinding()]
param(
    [switch]$SkipAi,
    [switch]$SkipApi,
    [switch]$SkipWeb
)

$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $PSCommandPath
if (-not $scriptRoot) {
    $scriptRoot = (Get-Location).Path
}

$services = New-Object System.Collections.Generic.List[object]

function Write-Info {
    param(
        [string]$Message,
        [System.ConsoleColor]$Color = [System.ConsoleColor]::Cyan
    )

    $currentColor = [System.Console]::ForegroundColor
    try {
        [System.Console]::ForegroundColor = $Color
        Write-Host $Message
    }
    finally {
        [System.Console]::ForegroundColor = $currentColor
    }
}

function Ensure-Command {
    param(
        [string]$CommandName,
        [string]$InstallHint
    )

    if (-not (Get-Command -Name $CommandName -ErrorAction SilentlyContinue)) {
        throw "Required command '$CommandName' was not found. Install $InstallHint and try again."
    }
}

function Stop-ProcessesOnPorts {
    param(
        [int[]]$Ports
    )

    if (-not $Ports) {
        return
    }

    Write-Info "Checking for processes on required ports..." -Color ([System.ConsoleColor]::Yellow)

    foreach ($port in ($Ports | Sort-Object -Unique)) {
        try {
            $connections = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction Stop
        }
        catch {
            Write-Info "  - Unable to inspect port ${port}: $($_.Exception.Message)" -Color ([System.ConsoleColor]::DarkYellow)
            continue
        }

        if (-not $connections) {
            Write-Info "  - Port ${port} is free." -Color ([System.ConsoleColor]::DarkGreen)
            continue
        }

        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -and $_ -ne 0 }
        if (-not $pids) {
            Write-Info "  - Port ${port} is reserved but process id unavailable." -Color ([System.ConsoleColor]::DarkYellow)
            continue
        }

        foreach ($processId in $pids) {
            try {
                $proc = Get-Process -Id $processId -ErrorAction Stop
                Write-Info "  - Stopping $($proc.ProcessName) (PID $processId) using port ${port}." -Color ([System.ConsoleColor]::Yellow)
                Stop-Process -Id $processId -Force -ErrorAction Stop
            }
            catch {
                Write-Info "    (warning) Could not stop PID $processId on port ${port}: $($_.Exception.Message)" -Color ([System.ConsoleColor]::Red)
            }
        }
    }
}

function Start-ServiceProcess {
    param(
        [string]$Name,
        [string]$Executable,
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )

    Write-Info "-> Starting $Name..." -Color ([System.ConsoleColor]::Green)

    $process = Start-Process -FilePath $Executable `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -NoNewWindow `
        -PassThru

    if (-not $process) {
        throw "Failed to start $Name."
    }

    $services.Add([pscustomobject]@{ Name = $Name; Process = $process }) | Out-Null
}

function Stop-AllServices {
    if ($services.Count -eq 0) {
        return
    }

    Write-Info "`nStopping services..." -Color ([System.ConsoleColor]::Yellow)

    foreach ($service in $services | Sort-Object { $_.Process.StartTime } -Descending) {
        $proc = $service.Process
        if ($proc -and -not $proc.HasExited) {
            Write-Info "  - $($service.Name)" -Color ([System.ConsoleColor]::Yellow)
            try {
                Stop-Process -Id $proc.Id -ErrorAction SilentlyContinue
                $proc.WaitForExit(2000) | Out-Null
            }
            catch {
                Write-Info "    (warning) Unable to stop $($service.Name): $($_.Exception.Message)" -Color ([System.ConsoleColor]::Red)
            }
        }
    }
}

$locationPushed = $false
try {
    Push-Location -LiteralPath $scriptRoot
    $locationPushed = $true

    Ensure-Command -CommandName 'python' -InstallHint 'Python 3.x'
    if (-not $SkipWeb) {
        Ensure-Command -CommandName 'pnpm' -InstallHint 'pnpm from https://pnpm.io/installation'
    }

    $portsToClear = @()
    if (-not $SkipAi) { $portsToClear += 8001 }
    if (-not $SkipApi) { $portsToClear += 8000 }
    if (-not $SkipWeb) { $portsToClear += 3000 }
    Stop-ProcessesOnPorts -Ports $portsToClear

    if (-not $SkipAi) {
        Start-ServiceProcess -Name 'AI Service (port 8001)' `
            -Executable 'python' `
            -Arguments @('simple_app.py') `
            -WorkingDirectory (Join-Path $scriptRoot 'ai')
    }

    if (-not $SkipApi) {
        Start-ServiceProcess -Name 'API Backend (port 8000)' `
            -Executable 'python' `
            -Arguments @('-m', 'uvicorn', 'app.main:app', '--reload', '--host', '0.0.0.0', '--port', '8000') `
            -WorkingDirectory (Join-Path $scriptRoot 'apps/api')
    }

    if (-not $SkipWeb) {
        $frontendWorkingDir = Join-Path $scriptRoot 'apps/web'
        $nextPs1 = Join-Path $frontendWorkingDir 'node_modules/.bin/next.ps1'
        if (-not (Test-Path -Path $nextPs1 -PathType Leaf)) {
            throw "Cannot find Next.js launcher at $nextPs1. Install dependencies with 'pnpm install' and try again."
        }

        Start-ServiceProcess -Name 'Frontend (port 3000)' `
            -Executable 'powershell.exe' `
            -Arguments @('-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $nextPs1, 'dev', '-p', '3000') `
            -WorkingDirectory $frontendWorkingDir
    }

    if ($services.Count -eq 0) {
        Write-Info 'No services were started. Use switches to control which ones to skip.' -Color ([System.ConsoleColor]::Yellow)
        return
    }

    Write-Host ''
    Write-Info 'All services started:' -Color ([System.ConsoleColor]::Green)
    foreach ($service in $services) {
        Write-Info "  - $($service.Name)" -Color ([System.ConsoleColor]::Green)
    }
    Write-Host ''
    Write-Info 'Press Ctrl+C to stop all services.' -Color ([System.ConsoleColor]::Yellow)

    Wait-Process -InputObject ($services | ForEach-Object { $_.Process })
}
finally {
    Stop-AllServices
    if ($locationPushed) {
        Pop-Location
    }
}

