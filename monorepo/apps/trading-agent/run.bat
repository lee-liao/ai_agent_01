@echo off
setlocal

echo 🤖 Starting AI Trading Agent (Exercise 5)...

REM Prefer .venv if present, else venv; create .venv if neither exists
if exist .venv (
  set "VENV_DIR=.venv"
) else if exist venv (
  set "VENV_DIR=venv"
) else (
  echo 📦 Creating virtual environment...
  set "VENV_DIR=.venv"
  python -m venv %VENV_DIR% || ( echo Failed to create venv & exit /b 1 )
)

echo 🔧 Activating virtual environment (%VENV_DIR%)...
call %VENV_DIR%\Scripts\activate

echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Create directories
if not exist reports mkdir reports
if not exist data mkdir data

REM Environment variables
set OTEL_SERVICE_NAME=trading-agent
set OTEL_SERVICE_VERSION=1.0.0
set OTEL_CONSOLE_EXPORT=true
set DATABASE_URL=postgresql://trader:trading123@localhost:5432/trading_db
set LLM_PROVIDER=openai
set REPORTS_DIR=reports

echo 🌟 Starting Trading Agent API on http://localhost:8001
python app.py

endlocal

