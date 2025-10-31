@echo off
setlocal

echo Starting all services...
docker-compose up -d

echo All services started.

endlocal
