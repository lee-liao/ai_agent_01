# Load Test Summary Report Template

**Test Date**: [YYYY-MM-DD]  
**Test Duration**: [Duration]  
**Backend URL**: [URL]  
**Test Scenarios**: [List scenarios run]

---

## Executive Summary

[Brief 2-3 sentence summary of overall test results and pass/fail status]

---

## Test Results by Scenario

### 1. SLO Validation (10 VUs, 15 minutes)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **p95 Latency** | ≤ 5s | [value] | ✅/❌ |
| **Failure Rate** | ≤ 1% | [value] | ✅/❌ |
| **Total Requests** | - | [value] | - |
| **Throughput** | - | [value] req/s | - |

**Analysis**: [Brief analysis of results]

---

### 2. Ramp-up Test (0 → 100 users over 5 minutes)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **p95 Latency** | ≤ 5s | [value] | ✅/❌ |
| **Failure Rate** | ≤ 1% | [value] | ✅/❌ |
| **Peak VUs** | 100 | [value] | - |
| **Throughput** | - | [value] req/s | - |

**Analysis**: [Brief analysis of results, particularly during ramp-up phases]

---

### 3. Spike Test (Sudden 10x traffic)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **p95 Latency** | ≤ 8s | [value] | ✅/❌ |
| **Failure Rate** | ≤ 5% | [value] | ✅/❌ |
| **Spike Peak** | 100 VUs | [value] | - |
| **Recovery Time** | - | [value] | - |

**Analysis**: [Brief analysis of spike handling and recovery]

---

### 4. Sustained Load - 50 VUs (10 minutes)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **p95 Latency** | ≤ 5s | [value] | ✅/❌ |
| **Failure Rate** | ≤ 1% | [value] | ✅/❌ |
| **Throughput** | - | [value] req/s | - |
| **Stability** | Stable | [Stable/Degrading] | ✅/❌ |

**Analysis**: [Brief analysis of sustained performance]

---

### 5. Sustained Load - 100 VUs (15 minutes)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **p95 Latency** | ≤ 5s | [value] | ✅/❌ |
| **Failure Rate** | ≤ 1% | [value] | ✅/❌ |
| **Throughput** | - | [value] req/s | - |
| **Stability** | Stable | [Stable/Degrading] | ✅/❌ |

**Analysis**: [Brief analysis of sustained performance at higher load]

---

## Overall Assessment

### ✅ Pass Criteria
- [ ] SLO validation meets targets (p95 ≤ 5s, failure rate ≤ 1%)
- [ ] Ramp-up test shows graceful degradation
- [ ] Spike test recovers successfully
- [ ] Sustained load maintains stability

### ⚠️ Issues Identified
- [List any issues or concerns]

### 🔧 Recommendations
- [List recommendations for improvements]

---

## Test Artifacts

- SLO Validation Report: `load/reports/k6_slo_validation_[timestamp].json`
- Ramp-up Test Report: `load/reports/k6_rampup_[timestamp].json`
- Spike Test Report: `load/reports/k6_spike_[timestamp].json`
- Sustained Load Reports: `load/reports/k6_sustained_*_[timestamp].json`

---

## Next Steps

- [ ] Review and address any issues identified
- [ ] Run follow-up tests if needed
- [ ] Update SLO thresholds if baseline performance changes
- [ ] Document performance characteristics for capacity planning

