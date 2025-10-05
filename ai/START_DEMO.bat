@echo off
echo ========================================
echo   Starting AI Service - Quick Demo
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9 or higher
    pause
    exit /b 1
)

echo.
echo Running quick demo setup...
echo This will:
echo   1. Create/use a demo space image
echo   2. Build FAISS index (first run only, 2-5 mins)
echo   3. Start AI service on port 8001
echo.

python quick_demo.py

pause

