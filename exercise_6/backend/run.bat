@echo off
setlocal

rem Get the directory of the script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

rem Default values
set "HOST=0.0.0.0"
set "PORT=8000"
set "RELOAD="
set "LOG_LEVEL=info"
set "WORKERS=1"

rem Parse command-line arguments
:arg_loop
if not "%~1"=="" (
    if "%~1"=="--host" (
        set "HOST=%~2"
        shift
    ) else if "%~1"=="--port" (
        set "PORT=%~2"
        shift
    ) else if "%~1"=="--reload" (
        set "RELOAD=--reload"
    ) else if "%~1"=="--log-level" (
        set "LOG_LEVEL=%~2"
        shift
    ) else if "%~1"=="--workers" (
        set "WORKERS=%~2"
        shift
    ) else (
        echo Unknown parameter passed: %~1
        exit /b 1
    )
    shift
    goto :arg_loop
)

rem Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating Python virtual environment...
    call venv\Scripts\activate.bat
)

rem Check if uvicorn is installed
where uvicorn >nul 2>nul
if %errorlevel% neq 0 (
    echo uvicorn could not be found. Installing dependencies...
    pip install -r requirements.txt
)

rem Run the FastAPI application
echo Starting FastAPI server on %HOST%:%PORT%...
uvicorn app.main:app --host "%HOST%" --port "%PORT%" %RELOAD% --log-level "%LOG_LEVEL%" --workers "%WORKERS%"

endlocal
