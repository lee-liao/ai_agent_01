# Implementation Tasks

## 1. Demo Script Planning
- [ ] 1.1 Create `docs/demo_script.md`
- [ ] 1.2 Plan 3 demo flows (~40 seconds each):
  - Flow 1: Refusal (medical question → empathetic refusal)
  - Flow 2: Normal advice (bedtime question → advice with citations)
  - Flow 3: HITL escalation (crisis mention → mentor queue → response)
- [ ] 1.3 Write narration script for each flow
- [ ] 1.4 Identify key UI elements to highlight
- [ ] 1.5 Add timing notes (~2 minutes total)

## 2. Demo Environment Setup
- [ ] 2.1 Ensure clean `docker compose up` works flawlessly
- [ ] 2.2 Pre-seed demo data if needed (mentor account, sample RAG docs)
- [ ] 2.3 Create `scripts/run_demo.sh` to automate setup
- [ ] 2.4 Test reproducibility on fresh machine
- [ ] 2.5 Document any prerequisites (API keys, etc.)

## 3. Demo Recording
- [ ] 3.1 Record Flow 1: Refusal scenario
- [ ] 3.2 Record Flow 2: Normal advice with citations
- [ ] 3.3 Record Flow 3: HITL escalation
- [ ] 3.4 Add voiceover narration
- [ ] 3.5 Edit to 2-minute final video
- [ ] 3.6 Add captions/subtitles for accessibility
- [ ] 3.7 Save to `demo/video.mp4`

## 4. One-Pager Report Structure
- [ ] 4.1 Create `docs/one_pager.md` template
- [ ] 4.2 Section 1: Executive Summary (2-3 sentences)
- [ ] 4.3 Section 2: Key Metrics
  - p95 latency
  - Failure rate
  - Citation rate
  - Cost per day
- [ ] 4.4 Section 3: Safety & Quality
  - Red-team test results
  - Refusal accuracy
  - Alpha test feedback
- [ ] 4.5 Section 4: Key Risks
- [ ] 4.6 Section 5: Next Steps

## 5. Metrics Collection
- [ ] 5.1 Run load test and capture p95 latency
- [ ] 5.2 Calculate failure rate from test results
- [ ] 5.3 Sample 10 sessions and measure citation rate
- [ ] 5.4 Calculate average cost per day from token tracking
- [ ] 5.5 Validate all metrics meet SLOs

## 6. One-Pager Content
- [ ] 6.1 Write executive summary
- [ ] 6.2 Populate metrics with actual data
- [ ] 6.3 List 3-5 key risks (e.g., cost escalation, RAG coverage gaps)
- [ ] 6.4 Define next steps (e.g., expand RAG, beta launch)
- [ ] 6.5 Add visualizations (charts, graphs) if helpful
- [ ] 6.6 Keep to 1 page (~500 words max)

## 7. Validation
- [ ] 7.1 Test demo reproducibility via `docker compose up`
- [ ] 7.2 Verify all 3 flows work as expected
- [ ] 7.3 Confirm metrics in one-pager align with SLOs
- [ ] 7.4 Review one-pager with team for accuracy
- [ ] 7.5 Get stakeholder feedback on clarity

## 8. Distribution
- [ ] 8.1 Upload demo video to shared location
- [ ] 8.2 Export one-pager as PDF
- [ ] 8.3 Create demo package (video + one-pager + setup instructions)
- [ ] 8.4 Send to stakeholders
- [ ] 8.5 Prepare for live demo presentation if needed

