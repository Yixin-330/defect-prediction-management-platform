# ═══════════════════════════════════════════════════════
# 东南亚跨境电商AI选品系统 — 一键启动
# Supervisor + Multi-Agent Backend
# ═══════════════════════════════════════════════════════

@echo off
setlocal enabledelayedexpansion

echo ╔══════════════════════════════════════════════╗
echo ║   SEA AI Selector — Multi-Agent Backend     ║
echo ║   东南亚跨境电商AI选品系统                     ║
echo ╚══════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Create venv if missing
if not exist "venv\" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
)

:: Activate
call venv\Scripts\activate.bat

:: Install deps
echo [2/3] Installing dependencies...
pip install -q -r requirements.txt

:: Check API key
if "%ANTHROPIC_API_KEY%"=="" (
    echo [WARN] ANTHROPIC_API_KEY not set. Running with placeholder.
    echo        Set your key: set ANTHROPIC_API_KEY=sk-ant-...
    echo        Or create .env file (see .env.example)
)

:: Start server
echo.
echo [3/3] Starting Multi-Agent Backend...
echo.
echo   🤖 Supervisor Agent  (orchestrator)
echo   📈 Trend Agent       (market trends)
echo   🔍 Competitor Agent  (competitive analysis)
echo   🤖 Recommend Agent   (AI recommendations)
echo   💰 Profit Agent      (profit calculation)
echo   📋 Report Agent      (report generation)
echo.
echo   🌐 http://localhost:8000
echo   🩺 http://localhost:8000/api/health
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

pause
