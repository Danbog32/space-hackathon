@echo off
echo ============================================================
echo   Starting All Services for Astro-Zoom Platform
echo ============================================================
echo.
echo This will start all 3 services in separate windows:
echo   1. AI Service (port 8001)
echo   2. API Backend (port 8000)
echo   3. Frontend (port 3000)
echo.
echo Press Ctrl+C in each window to stop services
echo ============================================================
echo.

cd /d "%~dp0"

echo Starting AI Service...
start "AI Service (Port 8001)" cmd /k "cd ai && python simple_app.py"
timeout /t 3

echo Starting API Backend...
start "API Backend (Port 8000)" cmd /k "cd apps\api && python -m uvicorn app.main:app --reload --port 8000"
timeout /t 5

echo Starting Frontend...
start "Frontend (Port 3000)" cmd /k "cd apps\web && npm run dev"
timeout /t 2

echo.
echo ============================================================
echo   All services are starting...
echo ============================================================
echo.
echo AI Service:  http://localhost:8001
echo API Backend: http://localhost:8000
echo Frontend:    http://localhost:3000
echo.
echo Wait ~10 seconds, then open: http://localhost:3000
echo.
echo To stop: Close each terminal window or press Ctrl+C
echo ============================================================
echo.

pause


