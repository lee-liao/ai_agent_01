# Add Load Testing

## Why
Load tests validate the system can handle expected traffic and meet SLOs under stress. Scaffolds for K6 and Locust already exist; this task implements comprehensive load testing scenarios and reporting.

## What Changes
- Use existing `load/k6/coach_scenario.js` and `load/locust/locustfile.py`
- Expand scenarios to cover WebSocket connections, concurrent sessions, and edge cases
- Run load tests with varying user counts (10, 50, 100 VUs)
- Generate report with throughput, p95 latency, error rate
- Verify SLO compliance: p95 ≤ 2.5s, error rate ≤ 1%

## Impact
- Affected specs: New capability `load-testing`
- Affected code:
  - `load/k6/coach_scenario.js` - K6 test script (already exists)
  - `load/locust/locustfile.py` - Locust test script (already exists)
  - `load/README.md` - Load testing guide
  - `load/reports/` - Test result reports
  - `load/run_tests.sh` - Automated test runner

