# Implementation Tasks

## 1. OpenTelemetry Setup
- [ ] 1.1 Add opentelemetry dependencies to `requirements.txt`
- [ ] 1.2 Create `observability/tracing.py` module
- [ ] 1.3 Initialize tracer provider with service name
- [ ] 1.4 Configure exporters (console, OTLP)
- [ ] 1.5 Integrate tracing in FastAPI middleware

## 2. Instrumentation
- [ ] 2.1 Add span for RAG retrieval (`retrieve_context`)
- [ ] 2.2 Add span for LLM calls (`generate_advice`)
- [ ] 2.3 Add span for guardrail checks (`classify_request`)
- [ ] 2.4 Add span for end-to-end request handling
- [ ] 2.5 Include attributes: session_id, prompt length, token count

## 3. Metrics
- [ ] 3.1 Add counter for total requests
- [ ] 3.2 Add histogram for latency distribution
- [ ] 3.3 Add counter for guardrail triggers
- [ ] 3.4 Add counter for RAG retrievals
- [ ] 3.5 Add gauge for active connections

## 4. Dashboards
- [ ] 4.1 Create latency dashboard (p50, p95, p99)
- [ ] 4.2 Create error rate dashboard
- [ ] 4.3 Create throughput dashboard
- [ ] 4.4 Create guardrail metrics dashboard
- [ ] 4.5 Export dashboard configs to `observability/dashboards/`

## 5. SLO Validation
- [ ] 5.1 Run K6 load test for 15 minutes
- [ ] 5.2 Collect metrics during test
- [ ] 5.3 Calculate p95 latency
- [ ] 5.4 Calculate failure rate
- [ ] 5.5 Assert p95 ≤ 2.5s and failure rate ≤ 1%

