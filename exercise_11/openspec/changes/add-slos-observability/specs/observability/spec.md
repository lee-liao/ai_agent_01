# Observability Capability

## ADDED Requirements

### Requirement: Distributed Tracing
The system SHALL instrument critical code paths with OpenTelemetry spans.

#### Scenario: RAG retrieval span
- **WHEN** RAG retrieval is performed
- **THEN** a span named `retrieve_context` is created
- **AND** includes attributes: query length, number of results, latency

#### Scenario: LLM generation span
- **WHEN** LLM generates advice
- **THEN** a span named `generate_advice` is created
- **AND** includes attributes: model name, prompt tokens, completion tokens, latency

#### Scenario: Guardrail span
- **WHEN** guardrail check is performed
- **THEN** a span named `classify_request` is created
- **AND** includes attributes: classification result, confidence score

### Requirement: Metrics Collection
The system SHALL collect key performance metrics.

#### Scenario: Latency metrics
- **WHEN** requests are processed
- **THEN** latency histogram is updated
- **AND** p50, p95, p99 are calculable

#### Scenario: Error rate metrics
- **WHEN** requests succeed or fail
- **THEN** counters are incremented
- **AND** error rate is calculable

### Requirement: Dashboard Exports
The system SHALL provide dashboard configurations for visualization.

#### Scenario: Dashboard JSON export
- **WHEN** dashboards are configured
- **THEN** JSON exports are saved to `observability/dashboards/`
- **AND** include latency, error rate, throughput, guardrail metrics

### Requirement: SLO Compliance
The system SHALL meet defined SLOs under load.

#### Scenario: 15-minute load test
- **WHEN** K6 load test runs for 15 minutes using SSE endpoint
- **THEN** p95 latency ≤ 5 seconds (SSE measures full stream, not just handshake)
- **AND** failure rate ≤ 1%
- **AND** SLO compliance is validated
- **NOTE**: SSE threshold is 5s because `http_req_duration` includes complete streaming response time

#### Scenario: SLO breach alerting
- **WHEN** p95 latency exceeds 5s (SSE full stream)
- **THEN** an alert is triggered
- **AND** oncall is notified

