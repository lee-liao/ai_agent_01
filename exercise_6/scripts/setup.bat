@echo off
setlocal

rem Exercise 6 RAG Chatbot Setup Script
rem Comprehensive setup for the entire RAG system

echo Exercise 6: RAG Chatbot Setup
echo =================================
set "PROJECT_DIR=%~dp0..\"
echo Project Directory: %PROJECT_DIR%
echo.

rem =============================================================================
rem PREREQUISITES CHECK
rem =============================================================================

echo Checking Prerequisites...
echo ----------------------------

rem Check Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo Docker is not installed. Please install Docker first.
    exit /b 1
)

rem Check Docker Compose
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

rem Check Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo Node.js is not installed. Please install Node.js 18+ first.
    exit /b 1
)

rem Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python 3 is not installed. Please install Python 3.8+ first.
    exit /b 1
)

echo All prerequisites are installed
echo.

rem =============================================================================
rem ENVIRONMENT SETUP
rem =============================================================================

echo Setting up Environment...
echo ----------------------------

cd /d "%PROJECT_DIR%"

rem Copy environment file if it doesn't exist
if not exist ".env" (
    if exist "env.example" (
        copy env.example .env
        echo Created .env file from env.example
    ) else (
        echo No env.example found. You'll need to create .env manually.
    )
) else (
    echo .env file already exists
)

rem Create necessary directories
echo Creating directories...
mkdir uploads temp logs data\samples backend\logs >nul 2>nul
echo Directories created

rem =============================================================================
rem DOCKER SERVICES SETUP
rem =============================================================================

echo Setting up Docker Services...
echo --------------------------------

rem Stop any existing services
echo Stopping existing services...
docker-compose down --remove-orphans 2>nul || echo.

rem Pull required images
echo Pulling Docker images...
docker-compose pull

rem Start infrastructure services first (database, chromadb, redis)
echo Starting infrastructure services...
docker-compose up -d postgres-rag chromadb redis-rag

rem Wait for services to be ready
echo Waiting for services to start...
timeout /t 15 /nobreak >nul

rem Check service health
echo Checking service health...

rem Check PostgreSQL
docker-compose exec -T postgres-rag pg_isready -U rag_user -d rag_chatbot >nul
if %errorlevel% equ 0 (
    echo PostgreSQL is ready
) else (
    echo PostgreSQL is not ready
    exit /b 1
)

rem Check ChromaDB
curl -s http://localhost:8000/api/v1/heartbeat >nul
if %errorlevel% equ 0 (
    echo ChromaDB is ready
) else (
    echo ChromaDB might still be starting...
)

rem Check Redis
docker-compose exec -T redis-rag redis-cli --raw incr ping >nul 2>nul
if %errorlevel% equ 0 (
    echo Redis is ready
) else (
    echo Redis might still be starting...
)

echo.

rem =============================================================================
rem BACKEND SETUP
rem =============================================================================

echo Setting up Backend...
echo -----------------------

cd /d "%PROJECT_DIR%backend"

rem Create Python virtual environment
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

rem Activate virtual environment
call venv\Scripts\activate

rem Upgrade pip
echo Upgrading pip...
pip install --upgrade pip

rem Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

echo Backend setup completed
echo.

rem =============================================================================
rem FRONTEND SETUP
rem =============================================================================

echo Setting up Frontend...
echo ------------------------

rem Setup Admin Console
if exist "%PROJECT_DIR%frontend\admin" (
    echo Setting up Admin Console...
    cd /d "%PROJECT_DIR%frontend\admin"
    
    if exist "package.json" (
        npm install
        echo Admin Console dependencies installed
    ) else (
        echo Admin Console package.json not found
    )
)

rem Setup Chat Interface
if exist "%PROJECT_DIR%frontend\chat" (
    echo Setting up Chat Interface...
    cd /d "%PROJECT_DIR%frontend\chat"
    
    if exist "package.json" (
        npm install
        echo Chat Interface dependencies installed
    ) else (
        echo Chat Interface package.json not found
    )
)

echo.

rem =============================================================================
rem DATABASE INITIALIZATION
rem =============================================================================

echo Initializing Database...
echo ---------------------------

cd /d "%PROJECT_DIR%"

rem The database should already be initialized by the init.sql script
rem Let's verify the tables exist
echo Verifying database tables...

docker-compose exec -T postgres-rag psql -U rag_user -d rag_chatbot -c "\dt" >nul 2>nul
if %errorlevel% equ 0 (
    echo Database tables verified
) else (
    echo Database tables verification failed
)

echo.

rem =============================================================================
rem SAMPLE DATA LOADING (Optional)
rem =============================================================================

echo Loading Sample Data...
echo ------------------------

rem Check if sample data should be loaded
if "%LOAD_SAMPLE_DATA%"=="" set "LOAD_SAMPLE_DATA=true"
if "%LOAD_SAMPLE_DATA%"=="true" (
    if exist "%PROJECT_DIR%data\samples\load_samples.py" (
        cd /d "%PROJECT_DIR%backend"
        call venv\Scripts\activate
        python "%PROJECT_DIR%data\samples\load_samples.py"
        echo Sample data loaded
    ) else (
        echo Sample data script not found
    )
) else (
    echo Skipping sample data loading
)

echo.

rem =============================================================================
rem FINAL VERIFICATION
rem =============================================================================

echo Final Verification...
echo -----------------------

rem Start all services
echo Starting all services...
docker-compose up -d

rem Wait for backend to be ready
echo Waiting for backend to start...
timeout /t 20 /nobreak >nul

rem Check backend health
curl -s http://localhost:8002/health >nul
if %errorlevel% equ 0 (
    echo Backend is healthy
) else (
    echo Backend might still be starting...
)

rem Check frontend services
curl -s http://localhost:3002 >nul
if %errorlevel% equ 0 (
    echo Admin Console is accessible
) else (
    echo Admin Console might still be starting...
)

curl -s http://localhost:3003 >nul
if %errorlevel% equ 0 (
    echo Chat Interface is accessible
) else (
    echo Chat Interface might still be starting...
)

echo.

rem =============================================================================
rem SUCCESS MESSAGE
rem =============================================================================

echo Setup Completed Successfully!
echo ===============================
echo.
echo Access URLs:
    echo   . Admin Console:     http://localhost:3002
    echo   . Chat Interface:    http://localhost:3003
    echo   . Backend API:       http://localhost:8002
    echo   . API Documentation: http://localhost:8002/docs
    echo   . ChromaDB:          http://localhost:8000

echo Database Access:
    echo   . Host: localhost
    echo   . Port: 5433
    echo   . Database: rag_chatbot
    echo   . User: rag_user
    echo   . Password: rag_password_2024

echo Next Steps:
    echo   1. Open http://localhost:3002 to access the Admin Console
    echo   2. Upload some documents to create your knowledge base
    echo   3. Add Q&A pairs for direct question matching
    echo   4. Test the chat interface at http://localhost:3003
    echo   5. Explore the API documentation at http://localhost:8002/docs

echo To stop all services: docker-compose down
echo To restart services: docker-compose up -d

echo Happy chatting!

endlocal