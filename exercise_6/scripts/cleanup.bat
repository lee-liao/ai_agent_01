@echo off
setlocal

echo Cleaning up all services, volumes, and networks...
docker-compose down -v --remove-orphans

echo Cleanup complete.

endlocal
