@echo off
setlocal

pushd "%~dp0" >nul

call :ensure_venv || exit /b 1
if exist .venv (
  call .venv\Scripts\activate
) else (
  call venv\Scripts\activate
)

set BACKEND_BASE=%BACKEND_BASE%
if "%BACKEND_BASE%"=="" set BACKEND_BASE=http://localhost:8020

python -m pip install --upgrade pip setuptools wheel >nul
pip install -r requirements.txt >nul

streamlit run app.py --server.port=4020 --server.headless=true

popd >nul
endlocal
goto :eof

:ensure_venv
if not exist venv if not exist .venv (
  python -m venv .venv || python -m venv venv || exit /b 1
)
exit /b 0

