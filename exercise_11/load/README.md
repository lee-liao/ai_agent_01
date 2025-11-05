# Exercise 11 Load Testing

This folder contains load testing tools and scenarios for the Child Growth Assistant backend.

## Overview

Load tests validate system performance under various conditions:
- **SLO Validation**: Baseline performance (10 VUs, 15 minutes)
- **Ramp-up Test**: Gradual increase from 0 → 100 users over 5 minutes
- **Spike Test**: Sudden 10x traffic increase
- **Sustained Load**: Extended periods with 50-100 concurrent users

## Prerequisites

### K6 (Recommended)
```bash
# Install k6
# Windows: choco install k6
# Mac: brew install k6
# Linux: https://k6.io/docs/getting-started/installation/

# Verify installation
k6 version
```

### Locust (Optional)
```bash
cd locust
pip install -r requirements.txt
```

## Quick Start

### Option 1: Run All Tests (Automated)
```bash
# Linux/Mac
cd load
chmod +x run_tests.sh
./run_tests.sh

# Windows
cd load
run_tests.bat
```

### Option 2: Run Individual Tests

#### SLO Validation (10 VUs, 15 minutes)
```bash
k6 run --env BASE_URL=http://localhost:8011 --env VUS=10 --env DURATION=15m load/k6/coach_scenario.js
```

#### Ramp-up Test (0 → 100 users over 5 minutes)
```bash
k6 run --env BASE_URL=http://localhost:8011 load/k6/ramp_up_scenario.js
```

#### Spike Test (Sudden 10x traffic)
```bash
k6 run --env BASE_URL=http://localhost:8011 load/k6/spike_scenario.js
```

#### Sustained Load (50 VUs, 10 minutes)
```bash
k6 run --env BASE_URL=http://localhost:8011 --env VUS=50 --env DURATION=10m load/k6/coach_scenario.js
```

#### Sustained Load (100 VUs, 15 minutes)
```bash
k6 run --env BASE_URL=http://localhost:8011 --env VUS=100 --env DURATION=15m load/k6/coach_scenario.js
```

## Test Scenarios

### 1. coach_scenario.js (Standard SLO Validation)
- **Purpose**: Validates SLOs (p95 ≤ 5s, failure rate ≤ 1%)
- **Default**: 10 VUs for 15 minutes
- **Configurable**: VUS and DURATION environment variables
- **Measures**: Full SSE streaming response time

### 2. ramp_up_scenario.js (Ramp-up Test)
- **Purpose**: Tests system behavior under gradual load increase
- **Pattern**: 0 → 20 → 50 → 80 → 100 users over 5 minutes
- **Use Case**: Validates graceful degradation and resource scaling

### 3. spike_scenario.js (Spike Test)
- **Purpose**: Tests system resilience to sudden traffic spikes
- **Pattern**: 10 users → sudden jump to 100 users → return to 10
- **Thresholds**: More lenient (5% failure rate, 8s p95) to account for spike
- **Use Case**: Validates emergency handling and rate limiting

## Understanding Results

### Key Metrics

- **p95 Latency**: 95th percentile response time (target: ≤ 5s for SSE)
- **Failure Rate**: Percentage of failed requests (target: ≤ 1%)
- **Throughput**: Requests per second
- **Virtual Users (VUs)**: Concurrent simulated users

### SLO Validation Results (Baseline)

From previous runs:
- **p95 Latency**: 4.36s ✅ (target: ≤ 5s)
- **Failure Rate**: 0.02% ✅ (target: ≤ 1%)
- **Total Requests**: 4,617
- **Test Duration**: 15 minutes
- **Virtual Users**: 10

### Interpreting Results

**Good Performance:**
- p95 latency < 5s
- Failure rate < 1%
- Stable throughput
- No memory leaks or resource exhaustion

**Warning Signs:**
- p95 latency > 5s consistently
- Failure rate > 1%
- Degrading performance over time
- Memory/resource exhaustion

**Critical Issues:**
- p95 latency > 10s
- Failure rate > 5%
- System crashes or timeouts
- Complete service unavailability

## Reports

Test results are saved to `load/reports/` directory:
- `k6_slo_validation_YYYY-MM-DD_HH-MM-SS.json` - SLO validation results
- `k6_rampup_YYYY-MM-DD_HH-MM-SS.json` - Ramp-up test results
- `k6_spike_YYYY-MM-DD_HH-MM-SS.json` - Spike test results
- `k6_sustained_50vu_YYYY-MM-DD_HH-MM-SS.json` - Sustained 50 VU test
- `k6_sustained_100vu_YYYY-MM-DD_HH-MM-SS.json` - Sustained 100 VU test

### Viewing Reports

```bash
# Generate HTML report from JSON
k6 report load/reports/k6_slo_validation_*.json

# View summary statistics
k6 stats load/reports/k6_slo_validation_*.json
```

## Troubleshooting

### Backend Not Running
```bash
# Start backend first
cd exercise_11/backend
uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload
```

### Connection Errors
- Verify BASE_URL is correct (default: http://localhost:8011)
- Check backend health: `curl http://localhost:8011/healthz`
- Ensure backend is accessible from test environment

### High Latency
- Check backend logs for errors
- Verify OpenAI API key is valid
- Check system resources (CPU, memory, network)
- Consider reducing VU count for debugging

### High Failure Rate
- Check backend error logs
- Verify API endpoints are correct
- Check for rate limiting or quota issues
- Validate SSE endpoint functionality

## Locust (Alternative Tool)

### Run Locust Web UI
```bash
cd locust
locust --host http://localhost:8011
# Open http://localhost:8089 in browser
```

### Run Locust Headless
```bash
cd locust
locust -f locustfile.py --host http://localhost:8011 -u 50 -r 5 -t 10m --headless
```

**Note**: Locust currently focuses on HTTP endpoints. For SSE streaming tests, use k6.

## Notes

- **SSE vs WebSocket**: Tests use SSE endpoint (`/api/coach/stream/{session_id}`) to match frontend behavior
- **Latency Measurement**: SSE `http_req_duration` measures the complete streaming response (includes full LLM generation time)
- **Thresholds**: p95 < 5s accounts for SSE's full-stream measurement (vs WebSocket's handshake-only measurement)
- **Test Questions**: Scenarios use varied test questions to simulate realistic usage patterns

## Environment Variables

- `BASE_URL`: Backend URL (default: http://localhost:8011)
- `VUS`: Number of virtual users (default: 10)
- `DURATION`: Test duration (default: 15m)

## References

- [k6 Documentation](https://k6.io/docs/)
- [Locust Documentation](https://docs.locust.io/)
- [SSE Specification](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- See `load/k6/RUN_SLO_VALIDATION.md` for detailed SLO validation guide
