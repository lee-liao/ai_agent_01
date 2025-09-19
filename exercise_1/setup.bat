@echo off
setlocal

pushd "%~dp0" >nul

set PYTHON_BIN=python

if not exist .venv (
  %PYTHON_BIN% -m venv .venv || ( echo python not found. Please install Python 3.10+. & exit /b 1 )
)

call .venv\Scripts\activate

set PIP_DISABLE_PIP_VERSION_CHECK=1
set PIP_NO_PYTHON_VERSION_WARNING=1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

if exist .env (
  echo .env found. The app will load it via python-dotenv.
) else (
  echo No .env found. Copy .env.example to .env and fill in keys.
)

echo Setup complete. To activate later: call .venv\Scripts\activate

popd >nul
endlocal

