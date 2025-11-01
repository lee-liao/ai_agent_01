# Add SLOs & Observability

## Why
Production systems need monitoring to detect issues, measure performance, and ensure SLOs are met. OpenTelemetry provides standardized observability with traces, metrics, and logs.

## What Changes
- Create `observability/` directory with OpenTelemetry instrumentation
- Add spans for retrieval, model calls, and guardrail checks
- Export dashboard configurations (JSON)
- Run 15-minute load test and verify p95 ≤ 2.5s and failure rate ≤ 1%

## Impact
- Affected specs: New capability `observability`
- Affected code:
  - `observability/tracing.py` - OpenTelemetry setup
  - `observability/dashboards/` - Dashboard configs
  - `backend/app/main.py` - Instrumentation integration
  - `backend/app/rag.py` - RAG retrieval spans
  - `backend/app/llm.py` - Model call spans
  - `backend/app/guardrails.py` - Guardrail spans

