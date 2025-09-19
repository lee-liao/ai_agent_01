@echo off
setlocal

pushd "%~dp0" >nul

call :ensure_venv || exit /b 1
if exist .venv (
  call .venv\Scripts\activate
) else (
  call venv\Scripts\activate
)

python -m pip install --upgrade pip setuptools wheel >nul
pip install -r requirements.txt >nul

if exist .env (
  for /f "usebackq tokens=*" %%a in (".env") do set %%a
)

set PORT=%PORT:=%
if "%PORT%"=="" set PORT=8000
python -m uvicorn app:app --host 0.0.0.0 --port %PORT%

popd >nul
endlocal
goto :eof

:ensure_venv
if not exist venv if not exist .venv (
  python -m venv .venv || python -m venv venv || exit /b 1
)
exit /b 0

