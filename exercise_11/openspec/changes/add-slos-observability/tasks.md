# Implementation Tasks

## 1. OpenTelemetry Setup
- [x] 1.1 Add opentelemetry dependencies to `requirements.txt`
- [x] 1.2 Create `observability/tracing.py` module (already existed as `app/observability.py`)
- [x] 1.3 Initialize tracer provider with service name
- [x] 1.4 Configure exporters (console, OTLP)
- [x] 1.5 Integrate tracing in FastAPI middleware (via FastAPIInstrumentor)

## 2. Instrumentation
- [x] 2.1 Add span for RAG retrieval (`retrieve_context`)
- [x] 2.2 Add span for LLM calls (`generate_advice` and `generate_advice_stream`)
- [x] 2.3 Add span for guardrail checks (`classify_request`)
- [x] 2.4 Add span for end-to-end request handling (via FastAPI instrumentation)
- [x] 2.5 Include attributes: session_id, prompt length, token count, latency, classification
- [x] 2.6 Add span for cost tracking (`billing.log_usage`) with cost, tokens, budget status

## 3. Metrics
- [ ] 3.1 Add counter for total requests (deferred - using spans for now)
- [ ] 3.2 Add histogram for latency distribution (deferred - using spans for now)
- [ ] 3.3 Add counter for guardrail triggers (tracked via span attributes)
- [ ] 3.4 Add counter for RAG retrievals (tracked via span attributes)
- [ ] 3.5 Add gauge for active connections (deferred)

## 4. Dashboards
- [x] 4.1 Create latency dashboard (p50, p95, p99) - exists in `observability/dashboards/latency_dashboard.json`
- [x] 4.2 Create error rate dashboard - exists in `observability/dashboards/performance_dashboard.json`
- [x] 4.3 Create throughput dashboard - exists in `observability/dashboards/performance_dashboard.json`
- [x] 4.4 Create guardrail metrics dashboard - exists in `observability/dashboards/classification_dashboard.json`
- [x] 4.5 Export dashboard configs to `observability/dashboards/`

## 5. SLO Validation
- [x] 5.1 Update K6 test script for 15-minute duration (updated `load/k6/coach_scenario.js`)
- [x] 5.2 Create SLO validation guide (`load/k6/RUN_SLO_VALIDATION.md`)
- [ ] 5.3 Run K6 load test for 15 minutes (manual testing required - see `load/k6/RUN_SLO_VALIDATION.md`)
- [ ] 5.4 Collect metrics during test (k6 output provides p95 and failure rate automatically)
- [ ] 5.5 Calculate p95 latency (from k6 output: `http_req_duration p(95)`)
- [ ] 5.6 Calculate failure rate (from k6 output: `http_req_failed` rate)
- [ ] 5.7 Assert p95 ≤ 2.5s and failure rate ≤ 1% (validate against k6 thresholds)

**Note:** K6 test script is configured with:
- Default duration: 15 minutes
- Default VUs: 10
- Thresholds: p95 < 2500ms, failure rate < 1%
- Varied test questions for realistic load
- See `load/k6/RUN_SLO_VALIDATION.md` for detailed instructions

