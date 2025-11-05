# Add SLOs & Observability

## Why
Production systems need monitoring to detect issues, measure performance, and ensure SLOs are met. OpenTelemetry provides standardized observability with traces, metrics, and logs.

## What Changes
- Create `observability/` directory with OpenTelemetry instrumentation
- Add spans for retrieval, model calls, and guardrail checks
- Export dashboard configurations (JSON)
- Run 15-minute load test and verify p95 ≤ 5s (SSE full stream) and failure rate ≤ 1%

## Implementation Status

✅ **Complete** - All tasks implemented and validated

**SLO Validation Results:**
- p95 Latency: 4.36s ✅ (target: ≤ 5s) - PASS
- Failure Rate: 0.02% ✅ (target: ≤ 1%) - PASS
- Test: 15-minute k6 load test with SSE endpoint
- See `exercise_11/openspec/changes/add-slos-observability/tasks.md` for details

## Impact
- Affected specs: New capability `observability`
- Affected code:
  - `observability/tracing.py` - OpenTelemetry setup
  - `observability/dashboards/` - Dashboard configs
  - `backend/app/main.py` - Instrumentation integration
  - `backend/app/rag.py` - RAG retrieval spans
  - `backend/app/llm.py` - Model call spans
  - `backend/app/guardrails.py` - Guardrail spans

