# SLO Validation Guide

This guide walks you through running a 15-minute load test to validate SLO compliance.

## Prerequisites

### 1. Install k6

**Windows:**
```powershell
# Using Chocolatey
choco install k6

# Or download from: https://k6.io/docs/getting-started/installation/
# Or using winget
winget install k6
```

**macOS:**
```bash
brew install k6
```

**Linux:**
```bash
# Using package manager
sudo apt-get install k6
# Or
sudo yum install k6
```

### 2. Start Backend Server

Ensure the backend is running on port 8011:

```bash
cd exercise_11/backend
# Activate virtual environment if using one
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8011
```

Verify backend is accessible:
```bash
curl http://localhost:8011/healthz
# Should return: {"status":"ok"}
```

### 3. Configure OpenAI API Key (Required)

Make sure your `.env` file in `exercise_11/backend/` has:
```
OPENAI_API_KEY=your-api-key-here
```

The backend needs OpenAI API access to generate advice responses.

## Running the Load Test

**Note:** The k6 test now uses **SSE (Server-Sent Events)** to match what the frontend actually uses, not WebSocket. This ensures accurate load testing of the production code path.

### Basic 15-Minute Test

```bash
cd exercise_11/load/k6
k6 run coach_scenario.js --duration 15m --vus 10
```

### Custom Configuration

You can override defaults using environment variables:

```bash
# Custom base URL
BASE_URL=http://localhost:8011 k6 run coach_scenario.js --duration 15m --vus 10

# More virtual users for higher load
k6 run coach_scenario.js --duration 15m --vus 20

# Shorter test for quick validation
k6 run coach_scenario.js --duration 5m --vus 10
```

### Save Results to File

```bash
k6 run coach_scenario.js --duration 15m --vus 10 > slo_results.txt 2>&1
```

## Understanding the Results

### Key Metrics to Check

Look for these lines in the k6 output:

```
http_req_duration......: avg=1.2s    min=500ms   med=1.1s    max=3.5s    p(95)=2.3s    p(99)=3.0s
http_req_failed........: 0.00%  ✓ 0.00% < 1.00%
```

### SLO Compliance

**✅ PASS Criteria:**
- `p(95)` (p95 latency) **≤ 5 seconds** (5000ms) - SSE measures full stream
- `http_req_failed` (failure rate) **≤ 1%** (0.01)

**Example Good Results:**
```
http_req_duration......: p(95)=4.1s    ✅ PASS (4.1s < 5s)
http_req_failed........: 0.00%         ✅ PASS (0% < 1%)
```

**Example Failing Results:**
```
http_req_duration......: p(95)=6.2s    ❌ FAIL (6.2s > 5s)
http_req_failed........: 1.5%          ❌ FAIL (1.5% > 1%)
```

### Full Output Example

```
     ✓ health 200
     ✓ start 200
     ✓ ws connected/closed

     checks.........................: 100.00% ✓ 3000  ✗ 0
     data_received..................: 2.5 MB  2.8 kB/s
     data_sent......................: 450 kB  500 B/s
     http_req_blocked................: avg=5ms    min=0s      med=0s      max=50ms
     http_req_connecting.............: avg=2ms    min=0s      med=0s      max=20ms
     http_req_duration..............: avg=1.2s   min=500ms   med=1.1s    max=3.5s    p(95)=2.3s    p(99)=3.0s
       { expected_response:true }...: avg=1.2s   min=500ms   med=1.1s    max=3.5s    p(95)=2.3s    p(99)=3.0s
     http_req_failed................: 0.00%   ✓ 0.00% < 1.00%
     http_req_receiving.............: avg=15ms   min=5ms     med=10ms    max=100ms
     http_req_sending................: avg=0.5ms  min=0s      med=0s      max=5ms
     http_req_waiting................: avg=1.18s min=490ms   med=1.09s   max=3.4s    p(95)=2.28s   p(99)=2.95s
     http_reqs......................: 1000    11.1/s
     iteration_duration.............: avg=2.5s   min=1.2s     med=2.3s     max=5.0s    p(95)=4.2s    p(99)=4.8s
     iterations.....................: 1000    11.1/s
     vus............................: 10      min=10       max=10
     vus_max........................: 10      min=10       max=10
     ws_connecting..................: avg=10ms  min=0s      med=0s      max=50ms
     ws_msgs_received................: 1000    11.1/s
     ws_msgs_sent...................: 1000    11.1/s
     ws_session_duration.............: avg=1.5s  min=800ms    med=1.4s     max=4.0s    p(95)=2.8s    p(99)=3.5s
```

**Key Metrics:**
- `http_req_duration p(95)=2.3s` → **p95 latency = 2.3 seconds** ✅
- `http_req_failed: 0.00%` → **Failure rate = 0%** ✅
- `http_reqs: 1000` → Total requests sent
- `iterations: 1000` → Total test iterations completed

## Troubleshooting

### High p95 Latency (> 5s)

**Possible causes:**
- OpenAI API is slow or rate-limited
- Network latency to OpenAI
- Backend is overloaded
- RAG retrieval is slow

**Solutions:**
- Check OpenAI API status
- Reduce virtual users (VUs)
- Check backend logs for errors
- Verify RAG index is optimized

### High Failure Rate (> 1%)

**Possible causes:**
- Backend crashes or errors
- OpenAI API key invalid or rate-limited
- Network connectivity issues
- Timeouts

**Solutions:**
- Check backend logs for errors
- Verify OpenAI API key is valid
- Check network connectivity
- Increase timeout values in k6 script

### No Traces in Jaeger

If you're using Jaeger for observability:
- Verify `.env` has `OTEL_EXPORTER_OTLP_ENDPOINT` set
- Check backend logs for "OTLP exporter configured"
- Ensure Jaeger collector is running
- Check time range in Jaeger UI

## Documenting Results

After running the test, document your results:

```markdown
## SLO Validation Results (15-minute load test)

**Test Configuration:**
- Duration: 15 minutes
- Virtual Users: 10
- Test Date: 2024-01-XX

**Results:**
- p95 Latency: 4.1s ✅ (target: ≤ 5s) - **PASS**
- Failure Rate: 0.3% ✅ (target: ≤ 1%) - **PASS**
- Total Requests: 1,234
- Failed Requests: 4

**Conclusion:**
All SLOs met. System is performing within acceptable limits.
```

## Next Steps

1. ✅ Run the 15-minute load test
2. ✅ Verify p95 ≤ 5s (SSE full stream) and failure rate ≤ 1%
3. ✅ Document results in OpenSpec tasks.md
4. ✅ Update proposal.md with validation status

