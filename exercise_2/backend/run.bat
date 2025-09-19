@echo off
setlocal

pushd "%~dp0" >nul

call :ensure_venv || exit /b 1
call .venv\Scripts\activate 2>nul || call venv\Scripts\activate

set PIP_DISABLE_PIP_VERSION_CHECK=1
python -m pip install --upgrade pip setuptools wheel >nul
pip install -r requirements.txt >nul

if exist .env (
  for /f "usebackq tokens=*" %%a in (".env") do set %%a
)

set PORT=%PORT%
if "%PORT%"=="" set PORT=8000
python -m uvicorn app:app --host 0.0.0.0 --port %PORT%

popd >nul
endlocal
goto :eof

:ensure_venv
if not exist .venv if not exist venv (
  python -m venv .venv || python -m venv venv || exit /b 1
)
exit /b 0
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

rem Check for Python installation
set PYTHON_FOUND=0
for %%v in (3.12 3.11 3.10 3) do (
    where python%%v >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYBIN=python%%v"
        set PYTHON_FOUND=1
        goto :found
    )
)

:found
if %PYTHON_FOUND% equ 0 (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYBIN=python"
        set PYTHON_FOUND=1
    )
)

if %PYTHON_FOUND% equ 0 (
    echo No suitable python found. Please install Python 3.10+.
    exit /b 1
)

echo Using Python: %PYBIN%

rem Check if virtual environment exists
if exist .venv (
    rem Check if venv has a working interpreter
    if not exist .venv\Scripts\python.exe (
        echo Removing broken virtual environment
        rmdir /s /q .venv
    )
)

rem Create virtual environment if it doesn't exist
if not exist .venv (
    echo Creating virtual environment
    %PYBIN% -m venv .venv
)

rem Activate virtual environment
call .venv\Scripts\activate.bat

set PIP_DISABLE_PIP_VERSION_CHECK=1

rem Ensure pip exists in this venv
python -m pip --version >nul 2>&1
if !errorlevel! neq 0 (
    python -m ensurepip --upgrade >nul 2>&1
    if !errorlevel! neq 0 (
        echo Installing pip manually
        curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python get-pip.py
        del /f get-pip.py
    )
)

rem Upgrade pip and install requirements
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

rem Load .env if present
if exist .env (
    for /f "usebackq tokens=*" %%a in (".env") do (
        set "%%a"
    )
) else (
    echo Warning: .env file not found
    echo You need to create a .env file with your OpenAI API key
    echo There is an sample file '.env.example' at the directory 'backend'. You can rename it to '.env' and update the api key there.
    echo Example:
    echo OPENAI_API_KEY=your_api_key_here
    echo.
)

rem Check if OPENAI_API_KEY is set
if "%OPENAI_API_KEY%"=="" (
    echo Error: OPENAI_API_KEY environment variable is not set
    echo Please:
    echo 1. Create a .env file in the backend directory
    echo 2. Add your OpenAI API key to the file:
    echo    OPENAI_API_KEY=your_actual_api_key_here
    echo 3. Or set the OPENAI_API_KEY environment variable manually
    echo.
    echo Note: You can get an API key from https://platform.openai.com/api-keys
    exit /b 1
)

rem Set default port if not defined
if "%PORT%"=="" set PORT=8000

echo Starting server on port %PORT%
echo OPENAI_API_KEY is set: *********************%OPENAI_API_KEY:~-5%

rem Enable debug logging
set LOG_LEVEL=DEBUG

rem Run the application with debug logging
echo Starting server with debug logging...
uvicorn app:app --host 0.0.0.0 --port %PORT% --log-level debug