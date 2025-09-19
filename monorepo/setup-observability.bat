@echo off
setlocal

echo 🎯 AI Agent Training - Observability Setup
echo ==========================================

REM Check Docker is running
docker info >nul 2>&1
if errorlevel 1 (
  echo ❌ Docker is not running. Please start Docker Desktop first.
  exit /b 1
)

REM Check docker-compose (v1 or v2 via docker compose)
docker-compose --version >nul 2>&1
if errorlevel 1 (
  docker compose version >nul 2>&1 || (
    echo ❌ docker-compose is not available. Install Docker Compose or ensure Docker Desktop is up to date.
    exit /b 1
  )
)

pushd "%~dp0" >nul

echo 📦 Pulling Docker images...
docker-compose pull 2>nul || docker compose pull

echo 🚀 Starting observability stack...
docker-compose up -d 2>nul || docker compose up -d

echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

echo 🔍 Checking service health...
curl -s http://localhost:16686 >nul 2>&1 && echo ✅ Jaeger UI is ready at http://localhost:16686 || echo ⚠️  Jaeger UI might still be starting...
curl -s http://localhost:9090 >nul 2>&1 && echo ✅ Prometheus is ready at http://localhost:9090 || echo ⚠️  Prometheus might still be starting...
curl -s http://localhost:3001 >nul 2>&1 && echo ✅ Grafana is ready at http://localhost:3001 (admin/admin) || echo ⚠️  Grafana might still be starting...
curl -s http://localhost:4318/v1/traces >nul 2>&1 && echo ✅ OpenTelemetry Collector is responding || echo ⚠️  OTEL Collector might still be starting...

echo.
echo 🎉 Observability stack is starting up!
echo.
echo 📊 Access URLs:
echo   • Jaeger UI (Traces):     http://localhost:16686
echo   • Grafana (Metrics):     http://localhost:3001 (admin/admin)
echo   • Prometheus:            http://localhost:9090
echo   • OTEL Collector:        http://localhost:4317 (gRPC), http://localhost:4318 (HTTP)
echo.
echo 🛑 To stop: docker-compose down  (or: docker compose down)

popd >nul
endlocal

