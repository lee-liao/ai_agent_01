# Child Growth Assistant - Demo Script

**Total Duration:** ~2 minutes (3 flows × ~40 seconds each)  
**Audience:** Stakeholders, investors, product managers  
**Purpose:** Demonstrate key capabilities: safety guardrails, evidence-based advice, and human-in-the-loop escalation

---

## 🎬 Flow 1: Safety Guardrails - Medical Refusal (40 seconds)

### Setup
- Navigate to: `http://localhost:3082/coach`
- Enter parent name: "Sarah"
- Click "Start Session"

### Narration Script
> "First, let's see how our safety guardrails protect users. I'll ask a medical question that the AI should not answer."

### Actions
1. **Type question** (5s): `"Can you diagnose my child with ADHD?"`
2. **Click Send** (2s)
3. **Wait for response** (8s) - Response appears with:
   - Empathetic acknowledgment: "I understand your concerns..."
   - Clear refusal: "I cannot provide medical diagnoses..."
   - Resource link: "Consult with a pediatrician..."
   - Safety footer visible

### Highlight Points
- ✅ **Point 1** (15s): "Notice the empathetic tone - we acknowledge the parent's concern first"
- ✅ **Point 2** (20s): "The refusal is clear but respectful, with a safety footer at the bottom"
- ✅ **Point 3** (30s): "We provide a helpful resource link to guide them to professional help"

### Transition
> "Now let's see how the system provides evidence-based advice for appropriate questions."

**Time Check:** ~40 seconds

---

## 🎬 Flow 2: Evidence-Based Advice with Citations (40 seconds)

### Setup
- Continue in same session (or start new if needed)

### Narration Script
> "Next, let's ask a parenting question that the AI can answer with evidence-based guidance."

### Actions
1. **Type question** (5s): `"How do I establish a bedtime routine for my 3-year-old?"`
2. **Click Send** (2s)
3. **Wait for streaming** (15s) - Watch tokens stream in:
   - Message appears gradually
   - Citations appear at the end
   - Response includes: empathy, 3 concrete steps, citation links

### Highlight Points
- ✅ **Point 1** (10s): "Watch how the response streams in real-time - this is Server-Sent Events (SSE) for smooth UX"
- ✅ **Point 2** (25s): "Notice the structured response: empathy first, then three actionable steps"
- ✅ **Point 3** (35s): "Here's the citation - every major claim is backed by AAP guidelines. Click it to see the source."

### Transition
> "Finally, let's see how the system handles crisis situations that require immediate human intervention."

**Time Check:** ~40 seconds

---

## 🎬 Flow 3: HITL Escalation - Crisis Detection (40 seconds)

### Setup
- Continue in same session (or start new if needed)

### Narration Script
> "Our most critical feature: detecting crisis situations and routing them to human mentors immediately."

### Actions
1. **Type question** (5s): `"I'm afraid I might hurt my child"` 
2. **Click Send** (2s)
3. **Wait for response** (10s) - Crisis detection triggers:
   - Immediate empathetic response
   - Crisis resources (988 hotline)
   - HITL queue notification
   - Message: "A mentor will review your message and respond shortly"

### Highlight Points
- ✅ **Point 1** (12s): "The system immediately detected crisis keywords and triggered our safety protocol"
- ✅ **Point 2** (20s): "Notice the emergency resources - 988 Suicide & Crisis Lifeline is prominently displayed"
- ✅ **Point 3** (30s): "The message was automatically queued to a human mentor for review. This ensures no crisis situation goes unaddressed."

### Wrap-up
> "This demonstrates our three-layer safety approach: preventive guardrails, evidence-based guidance, and human oversight for critical situations."

**Time Check:** ~40 seconds

---

## 📝 Key Talking Points (If Questions Arise)

### Performance Metrics
- **p95 Latency:** 4.36s (target: ≤5s) ✅
- **Failure Rate:** 0.02% (target: ≤1%) ✅
- **Citation Rate:** 90%+ ✅
- **E2E Tests:** 8/8 passing ✅

### Technical Highlights
- **SSE Streaming:** Real-time token streaming for better UX
- **RAG Retrieval:** Curated knowledge base with AAP guidelines
- **Cost Tracking:** Token usage monitoring with budget caps
- **Observability:** OpenTelemetry instrumentation for production monitoring

### Safety Features
- **Medical Refusal:** Automatic refusal with empathy + resources
- **Crisis Detection:** PII/crisis keyword detection → HITL queue
- **Guardrails:** Scope policy enforcement, refusal templates
- **Human Oversight:** Mentor queue for sensitive cases

---

## 🎥 Recording Tips

1. **Browser Window:** Use 1920×1080 resolution, full-screen browser
2. **Zoom:** Set browser zoom to 100% (no zoom)
3. **Speed:** Slow down mouse movements slightly for clarity
4. **Pauses:** Add 2-3 second pauses after each highlight point
5. **Transitions:** Smooth transitions between flows (no jarring cuts)
6. **Audio:** Record voiceover separately if possible (better quality)

## 📦 Demo Package Checklist

- [ ] Demo video recorded (2 minutes)
- [ ] Voiceover added (or live narration)
- [ ] Captions/subtitles added
- [ ] One-pager report completed
- [ ] Setup instructions documented
- [ ] All files saved to `exercise_11/demo/` directory

