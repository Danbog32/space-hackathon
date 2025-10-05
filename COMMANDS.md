# Astro-Zoom Application Commands Reference

## 🚀 Quick Start Commands

### Start All Services
```powershell
.\start.ps1
```
Starts the Web, API, and AI services in separate windows.

### Stop All Services
```powershell
.\stop.ps1
```
Stops all running services on ports 3000, 8000, and 8001.

### Restart All Services
```powershell
.\restart.ps1
```
Stops and then starts all services.

### Check Health
```powershell
.\healthcheck.ps1
```
Checks if all services are running and responding correctly.

### View Status
```powershell
.\status.ps1
```
Shows detailed information about running processes and ports.

---

## 📍 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Web** | http://localhost:3000 | Next.js frontend application |
| **API** | http://localhost:8000 | FastAPI backend |
| **API Docs** | http://localhost:8000/docs | Swagger UI documentation |
| **API ReDoc** | http://localhost:8000/redoc | ReDoc documentation |
| **AI** | http://localhost:8001 | AI service for semantic search |

---

## 🔧 Manual Commands

### Start Individual Services

#### Web Service (Next.js)
```powershell
cd apps/web
pnpm dev
```

#### API Service (FastAPI)
```powershell
cd apps/api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### AI Service (FastAPI)
```powershell
cd apps/ai
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

---

## 🧪 Health Check Commands

### Check Specific Ports
```powershell
# Check if port is listening
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
```

### Test Endpoints with curl
```powershell
# Web service
curl http://localhost:3000

# API health check
curl http://localhost:8000/health

# API datasets
curl http://localhost:8000/datasets

# AI health check
curl http://localhost:8001/health
```

### Test Endpoints with Invoke-WebRequest
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET
Invoke-WebRequest -Uri "http://localhost:8001/health" -Method GET
```

---

## 🛑 Stop/Kill Commands

### Kill Process on Specific Port
```powershell
# Find and kill process on port 3000
$proc = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
Stop-Process -Id $proc -Force

# Find and kill process on port 8000
$proc = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
Stop-Process -Id $proc -Force

# Find and kill process on port 8001
$proc = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
Stop-Process -Id $proc -Force
```

### Kill All Node.js Processes
```powershell
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Kill All Python Processes
```powershell
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 📊 Monitoring Commands

### Show All Listening Ports
```powershell
netstat -an | Select-String "LISTENING"
```

### Show Specific Ports
```powershell
netstat -an | Select-String "3000|8000|8001" | Select-String "LISTENING"
```

### Show Process Information
```powershell
# Get all Node.js processes
Get-Process -Name "node" | Format-Table -Property Id, ProcessName, WorkingSet64, StartTime

# Get all Python processes
Get-Process -Name "python" | Format-Table -Property Id, ProcessName, WorkingSet64, StartTime
```

### Monitor Real-time Connections
```powershell
# Watch connections on port 8000
while ($true) {
    Clear-Host
    Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Format-Table
    Start-Sleep -Seconds 2
}
```

---

## 🔍 Troubleshooting Commands

### Check if Ports are Already in Use
```powershell
# Before starting services
Test-NetConnection -ComputerName localhost -Port 3000
Test-NetConnection -ComputerName localhost -Port 8000
Test-NetConnection -ComputerName localhost -Port 8001
```

### View Logs
```powershell
# If services are running in PowerShell windows, logs appear there
# For background processes, check the terminal where you started them
```

### Clean Database
```powershell
# Remove SQLite database and start fresh
Remove-Item -Path "data/astro.db*" -Force -ErrorAction SilentlyContinue
```

### Rebuild Packages
```powershell
# Clean and rebuild TypeScript packages
pnpm clean
pnpm install
cd packages/proto
pnpm build
cd ../ui
pnpm build
```

### Regenerate Sample Tiles
```powershell
python infra/generate_sample_tiles.py
```

---

## 🐛 Debug Mode

### Run Services with Debug Output
```powershell
# API with debug
cd apps/api
$env:LOG_LEVEL="DEBUG"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# AI with debug
cd apps/ai
$env:LOG_LEVEL="DEBUG"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 --log-level debug
```

---

## 📦 Dependency Management

### Install Dependencies
```powershell
# Node.js dependencies
pnpm install

# Python dependencies for API
pip install -r apps/api/requirements.txt

# Python dependencies for AI
pip install -r apps/ai/requirements.txt
```

### Update Dependencies
```powershell
# Update Node.js packages
pnpm update

# Update Python packages
pip install --upgrade -r apps/api/requirements.txt
pip install --upgrade -r apps/ai/requirements.txt
```

---

## 🧹 Cleanup Commands

### Clean Build Artifacts
```powershell
# Remove Next.js build
Remove-Item -Path "apps/web/.next" -Recurse -Force -ErrorAction SilentlyContinue

# Remove TypeScript build outputs
Remove-Item -Path "packages/proto/dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "packages/ui/dist" -Recurse -Force -ErrorAction SilentlyContinue

# Remove Python cache
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -Force | Remove-Item -Force
```

### Full Reset
```powershell
# Stop services
.\stop.ps1

# Clean everything
pnpm clean
Remove-Item -Path "data/astro.db*" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "node_modules" -Recurse -Force -ErrorAction SilentlyContinue

# Reinstall and rebuild
pnpm install
cd packages/proto && pnpm build && cd ../..
cd packages/ui && pnpm build && cd ../..
python infra/generate_sample_tiles.py

# Start fresh
.\start.ps1
```

---

## 💡 Tips

1. **Always stop services before restarting** to avoid port conflicts
2. **Use `.\healthcheck.ps1`** regularly to ensure all services are healthy
3. **Check `.\status.ps1`** to see memory usage and process information
4. **Run from project root** - all scripts assume you're in `C:\Hackatons\space-hackathon`
5. **Keep terminals open** - closing service terminal windows will stop those services

---

## 🆘 Common Issues

### Port Already in Use
```powershell
# Run stop script to clean up
.\stop.ps1

# Or manually kill the process
$proc = Get-NetTCPConnection -LocalPort 3000 | Select-Object -ExpandProperty OwningProcess
Stop-Process -Id $proc -Force
```

### Services Won't Start
```powershell
# Check if Python/Node are in PATH
python --version
node --version
pnpm --version

# Reinstall dependencies
pnpm install
pip install -r apps/api/requirements.txt
pip install -r apps/ai/requirements.txt
```

### Database Locked
```powershell
# Remove database lock files
Remove-Item -Path "data/astro.db-shm" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "data/astro.db-wal" -Force -ErrorAction SilentlyContinue
```

