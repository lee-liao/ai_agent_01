@echo off
REM Load Testing Automation Script for Windows
REM Runs k6 load tests with different scenarios and generates reports

set BASE_URL=%BASE_URL%
if "%BASE_URL%"=="" set BASE_URL=http://localhost:8011

set REPORTS_DIR=load\reports
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set TIMESTAMP=%mydate%_%mytime%

REM Create reports directory if it doesn't exist
if not exist "%REPORTS_DIR%" mkdir "%REPORTS_DIR%"

echo Starting Load Tests...
echo Base URL: %BASE_URL%
echo Reports will be saved to: %REPORTS_DIR%
echo.

REM Test 1: Standard SLO Validation (10 VUs, 15 minutes)
echo Test 1: SLO Validation (10 VUs, 15 minutes)...
k6 run --env BASE_URL="%BASE_URL%" --env VUS=10 --env DURATION=15m --out json="%REPORTS_DIR%\k6_slo_validation_%TIMESTAMP%.json" load\k6\coach_scenario.js
echo SLO Validation complete
echo.

REM Test 2: Ramp-up Test (0 -^> 100 users over 5 minutes)
echo Test 2: Ramp-up Test (0 -^> 100 users over 5 minutes)...
k6 run --env BASE_URL="%BASE_URL%" --out json="%REPORTS_DIR%\k6_rampup_%TIMESTAMP%.json" load\k6\ramp_up_scenario.js
echo Ramp-up test complete
echo.

REM Test 3: Spike Test (Sudden 10x traffic)
echo Test 3: Spike Test (Sudden 10x traffic increase)...
k6 run --env BASE_URL="%BASE_URL%" --out json="%REPORTS_DIR%\k6_spike_%TIMESTAMP%.json" load\k6\spike_scenario.js
echo Spike test complete
echo.

REM Test 4: Sustained Load (50 VUs, 10 minutes)
echo Test 4: Sustained Load (50 VUs, 10 minutes)...
k6 run --env BASE_URL="%BASE_URL%" --env VUS=50 --env DURATION=10m --out json="%REPORTS_DIR%\k6_sustained_50vu_%TIMESTAMP%.json" load\k6\coach_scenario.js
echo Sustained load test complete
echo.

REM Test 5: Sustained Load (100 VUs, 15 minutes)
echo Test 5: Sustained Load (100 VUs, 15 minutes)...
k6 run --env BASE_URL="%BASE_URL%" --env VUS=100 --env DURATION=15m --out json="%REPORTS_DIR%\k6_sustained_100vu_%TIMESTAMP%.json" load\k6\coach_scenario.js
echo Sustained load test complete
echo.

echo All load tests completed!
echo Reports saved to: %REPORTS_DIR%
echo.
echo To view results, use:
echo   k6 stats %REPORTS_DIR%\k6_*.json
echo   or
echo   k6 report %REPORTS_DIR%\k6_*.json

