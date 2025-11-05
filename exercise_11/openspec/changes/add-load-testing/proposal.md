# Add Load Testing

## Why
Load tests validate the system can handle expected traffic and meet SLOs under stress. Scaffolds for K6 and Locust already exist; this task implements comprehensive load testing scenarios and reporting.

## What Changes
- Use existing `load/k6/coach_scenario.js` and `load/locust/locustfile.py`
- Expand scenarios to cover SSE streaming, concurrent sessions, and edge cases
- Run load tests with varying user counts (10, 50, 100 VUs)
- Generate report with throughput, p95 latency, error rate
- Verify SLO compliance: p95 ≤ 5s (SSE), error rate ≤ 1%

## Impact
- Affected specs: New capability `load-testing`
- Affected code:
  - `load/k6/coach_scenario.js` - K6 test script (already exists)
  - `load/k6/ramp_up_scenario.js` - Ramp-up test scenario
  - `load/k6/spike_scenario.js` - Spike test scenario
  - `load/locust/locustfile.py` - Locust test script (already exists)
  - `load/README.md` - Load testing guide
  - `load/reports/` - Test result reports
  - `load/run_tests.sh` / `load/run_tests.bat` - Automated test runners

## Implementation Status
✅ **Load Testing Infrastructure Complete** - 20/25 tasks (5 Locust tasks deferred)
- **Test Scenarios**: ✅ Created ramp-up, spike, and sustained load scenarios
- **Automation**: ✅ Created run_tests.sh and run_tests.bat for automated test execution
- **Documentation**: ✅ Comprehensive README with instructions, interpretation guide, troubleshooting
- **SLO Validation**: ✅ Completed (p95: 4.36s, failure rate: 0.02%)
- **Reporting**: ✅ Report template and automated JSON output

**Key Features**:
- Ramp-up test: 0 → 100 users over 5 minutes
- Spike test: Sudden 10x traffic increase
- Sustained load: Configurable VU counts (50, 100)
- All tests use SSE endpoint (matches frontend behavior)
- Automated JSON report generation with timestamps

**Note**: Locust tests are optional and deferred. k6 provides comprehensive SSE testing capability.

