@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting AI Trading Agent...

REM Navigate to trading agent directory relative to this script
pushd "%~dp0apps\trading-agent" >nul

REM Prefer .venv if present, else venv; create .venv if neither exists
if exist .venv (
  set "VENV_DIR=.venv"
) else if exist venv (
  set "VENV_DIR=venv"
) else (
  echo 📦 Setting up virtual environment...
  set "VENV_DIR=.venv"
  python -m venv %VENV_DIR% || (
    echo Failed to create virtual environment.& popd & exit /b 1
  )
)

echo 🔧 Activating virtual environment (%VENV_DIR%)...
call %VENV_DIR%\Scripts\activate

echo 📚 Installing dependencies (this may take a moment)...
python -m pip install --upgrade pip
pip install -r requirements_simple.txt
pip install jinja2

echo 🌐 Starting server on http://localhost:8001
echo 💬 Chat UI: http://localhost:8001/
echo 📚 API docs: http://localhost:8001/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload

popd >nul
endlocal

