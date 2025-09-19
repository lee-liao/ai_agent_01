@echo off
setlocal

echo 🚀 Starting AI Agent Training API...

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

if not exist data mkdir data

set OTEL_SERVICE_NAME=ai-agent-training-api-dev
set OTEL_SERVICE_VERSION=1.0.0
set OTEL_CONSOLE_EXPORT=true

echo 🌟 Starting FastAPI server on http://localhost:8000
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

endlocal

