# How to Check SLOs (Service Level Objectives)

**SLO Targets:**
- ✅ **p95 latency ≤ 2.5 seconds** (end-to-end request time)
- ✅ **Failure rate ≤ 1%** (error requests / total requests)

---

## 🎯 Method 1: Using k6 Load Test (Recommended - Easiest!)

The k6 load test automatically calculates p95 and failure rate for you!

### Step 1: Run Load Test

```bash
cd exercise_11/load/k6
k6 run coach_scenario.js --duration 15m --vus 10
```

**Parameters:**
- `--duration 15m` - Run for 15 minutes (required for SLO validation)
- `--vus 10` - 10 virtual users (adjust based on your needs)

### Step 2: Check k6 Output

Look for these lines in the output:

```
http_req_duration......: avg=1.2s    min=500ms   med=1.1s    max=3.5s    p(95)=2.3s    p(99)=3.0s
http_req_failed........: 0.00%  ✓ 0.00% < 1.00%
```

**Interpretation:**
- `p(95)=2.3s` → **p95 latency = 2.3 seconds** ✅ (2.3s < 2.5s → **PASS**)
- `http_req_failed: 0.00%` → **Failure rate = 0%** ✅ (0% < 1% → **PASS**)

### Step 3: Document Results

```
SLO Validation Results (15-minute load test):
- p95 latency: 2.3s ✅ (target: ≤ 2.5s) - PASS
- Failure rate: 0.00% ✅ (target: ≤ 1%) - PASS
- Total requests: 1,234
- Failed requests: 0
```

---

## 🔍 Method 2: Using Jaeger UI (Visual Inspection)

Use Jaeger to visually inspect traces and manually calculate metrics.

### Step 1: Run Load Test First

```bash
cd exercise_11/load/k6
k6 run coach_scenario.js --duration 30s
```

This generates traces that will appear in Jaeger.

### Step 2: Open Jaeger UI

1. Go to: **http://103.98.213.149:4505** (or your Jaeger server URL)
2. Select service: **`child-growth-assistant`**
3. Set time range: **Last 1 hour** (or adjust to cover your test period)

### Step 3: Find Root HTTP Spans

**Important:** You need to look at **end-to-end HTTP request spans**, not child operation spans!

1. In the **Operation** dropdown, select:
   - `POST /api/coach/start` (for regular requests)
   - `GET /api/coach/stream/{session_id}` (for SSE streaming)
   - Or select **"all operations"** and look for HTTP routes

2. Click **"Find Traces"**

You should see traces like:
```
POST /api/coach/start    1.2s    [Trace ID]
POST /api/coach/start    0.9s    [Trace ID]
POST /api/coach/start    1.5s    [Trace ID]
```

**These durations are your end-to-end latencies!**

### Step 4: Calculate p95 Latency

**Option A: Quick Visual Check**

1. **Sort traces by Duration** (click the "Duration" column header)
2. Count total traces shown (e.g., 100 traces)
3. Find the trace at **95th percentile position**:
   - For 100 traces: 95th trace (when sorted longest to shortest)
4. Check its duration:
   - ✅ If < 2500ms (2.5s) → **PASS**
   - ❌ If ≥ 2500ms → **FAIL**

**Example:**
- Total traces: 100
- Trace #5 (5th longest) = p95 position
- Duration: 2.1s
- ✅ **2.1s < 2.5s → PASS!**

**Option B: Manual Calculation**

1. Note down all durations from the trace list
2. Sort them in descending order
3. Calculate p95 index: `p95_index = int(len(durations) * 0.95)`
4. The duration at that index is your p95

**Python Script:**
```python
durations = [1500, 1200, 2300, 1800, 2100, ...]  # in milliseconds
durations.sort(reverse=True)  # Sort descending
p95_index = int(len(durations) * 0.95)
p95 = durations[p95_index]
print(f"p95 latency: {p95}ms ({p95/1000:.2f}s)")
print(f"SLO Status: {'✅ PASS' if p95 < 2500 else '❌ FAIL'} (target: ≤ 2.5s)")
```

### Step 5: Calculate Failure Rate

**Identify Failed Requests:**

1. **Add tag filter** in Jaeger search:
   ```
   http.status_code>=400
   ```
   OR
   ```
   error=true
   ```

2. Click **"Find Traces"**
3. Count how many traces appear (these are failures)

**Calculate:**
```
Total requests = All traces shown (when filter is removed)
Failed requests = Traces with http.status_code >= 400
Failure rate = (Failed / Total) × 100%
```

**Example:**
- Total traces: 1000
- Failed traces: 3 (http.status_code = 500)
- Failure rate: 3/1000 = 0.3% ✅ (< 1% → **PASS**)

### Step 6: Visual Inspection

**Check individual traces:**

1. Click on any trace to see the detailed view
2. Look at the **root span duration** (top-level HTTP request)
3. Check for error indicators (⚠️ red marks)
4. Verify span tags show `http.status_code: 200` for successful requests

**Example trace view:**
```
┌─────────────────────────────────────────────────────────┐
│ POST /api/coach/start                                    │
│ Duration: 1.2s  ← END-TO-END LATENCY                    │
│                                                          │
│ Timeline View:                                           │
│ [════════════════════════════════] 1.2s                 │
│  ├─[══] guard.check_message (15ms)                      │
│  ├─[═══] retrieval.retrieve (45ms)                      │
│  └─[════════════════════] model.generate_advice (1100ms)│
│                                                          │
│ Tags:                                                    │
│   http.method: POST                                     │
│   http.route: /api/coach/start                          │
│   http.status_code: 200  ← SUCCESS                      │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Method 3: Using Prometheus + Grafana (Advanced)

If you have Prometheus and Grafana set up, you can create dashboards for automated SLO monitoring.

### Step 1: Verify Prometheus is Running

```bash
# Check if Prometheus is accessible
curl http://103.98.213.149:4506/metrics
```

### Step 2: Query Metrics

**p95 Latency Query (example):**
```promql
histogram_quantile(0.95, rate(http_server_duration_bucket[5m]))
```

**Failure Rate Query (example):**
```promql
sum(rate(http_server_requests_total{status=~"5.."}[5m])) / 
sum(rate(http_server_requests_total[5m])) * 100
```

### Step 3: Create Grafana Dashboard

1. Import the dashboard JSON from `exercise_11/observability/dashboards/performance_dashboard.json`
2. Configure Prometheus as data source
3. View real-time SLO metrics

---

## ✅ Quick Checklist

After running load test:

- [ ] k6 shows `p(95) < 2500ms` in output
- [ ] k6 shows `http_req_failed rate < 0.01` (1%)
- [ ] Jaeger UI shows traces for the test period
- [ ] Root spans show reasonable durations (< 3s most)
- [ ] No red error indicators in Jaeger (or very few)
- [ ] Failure rate calculated: (Failed / Total) × 100% < 1%

---

## 🎯 Recommended Approach for SLO Validation

### For Task 8 Completion:

1. **Run k6 load test for 15 minutes:**
   ```bash
   cd exercise_11/load/k6
   k6 run coach_scenario.js --duration 15m --vus 10
   ```

2. **Document k6 output:**
   - Copy the `http_req_duration` line showing p95
   - Copy the `http_req_failed` line showing failure rate
   - Verify both meet SLO targets

3. **Take screenshots from Jaeger:**
   - Trace timeline view showing end-to-end latency
   - Span attributes showing operation breakdown
   - Error traces (if any)

4. **Create validation report:**
   ```
   SLO Validation Results (15-minute load test):
   
   Metrics:
   - p95 latency: 2.1s ✅ (target: ≤ 2.5s) - PASS
   - Failure rate: 0.3% ✅ (target: ≤ 1%) - PASS
   - Total requests: 1,234
   - Failed requests: 4
   
   Breakdown:
   - Guard latency: ~15ms (p95)
   - Retrieval latency: ~45ms (p95)
   - Model generation: ~1.8s (p95)
   - Total overhead: ~0.2s
   
   Conclusion: All SLOs met ✅
   ```

---

## 🐛 Troubleshooting

**Can't see traces in Jaeger?**
- Check backend logs: Should see "OTLP exporter configured: http://103.98.213.149:4510"
- Verify Jaeger is running: Check server at `http://103.98.213.149:4505`
- Check time range in Jaeger UI (set to "Last 1 hour")
- Verify `.env` has: `OTEL_EXPORTER_OTLP_ENDPOINT=http://103.98.213.149:4510`

**Traces missing durations?**
- Ensure OpenTelemetry instrumentation is enabled
- Check that FastAPI instrumentation is working
- Verify spans are being created (check backend console output)

**Don't see root HTTP spans?**
- Look for operations starting with `POST /` or `GET /`
- Try selecting "all operations" first
- Check if your endpoint uses SSE (`GET /api/coach/stream/{session_id}`)

**k6 shows high p95?**
- Check Jaeger traces to identify bottlenecks
- Look at `model.generate_advice` span durations (usually the slowest)
- Consider optimizing RAG retrieval or model prompts
- Check network latency to OpenAI API

**High failure rate?**
- Check Jaeger for error traces
- Look at `http.status_code` tags
- Check backend logs for exceptions
- Verify OpenAI API key is valid

---

## 📚 Additional Resources

- **k6 Documentation**: https://k6.io/docs/
- **Jaeger UI Guide**: See `exercise_11/observability/HOW_TO_FIND_P95_IN_JAEGER.md`
- **SLO Validation**: See `exercise_11/observability/CHECK_SLO_JAEGER.md`
- **Setup Guide**: See `exercise_11/observability/SETUP_GUIDE.md`

---

## 🎓 Example: Complete SLO Check Workflow

```bash
# 1. Start backend (if not running)
cd exercise_11/backend
uvicorn app.main:app --port 8011

# 2. Run 15-minute load test
cd ../load/k6
k6 run coach_scenario.js --duration 15m --vus 10 > slo_results.txt

# 3. Check results
cat slo_results.txt | grep -E "p\(95\)|http_req_failed"

# 4. Open Jaeger UI
# http://103.98.213.149:4505
# - Select service: child-growth-assistant
# - Operation: POST /api/coach/start
# - Time range: Last 1 hour
# - Sort by Duration
# - Check p95 position trace duration

# 5. Calculate failure rate
# - Add filter: http.status_code>=400
# - Count failed traces
# - Calculate: (Failed / Total) × 100%
```

**Result:**
```
✅ p95 latency: 2.1s < 2.5s → PASS
✅ Failure rate: 0.3% < 1% → PASS
🎯 All SLOs met!
```

