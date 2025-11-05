# HITL Testing Quick Checklist

Use this checklist to verify each requirement. Check off what you've tested:

## ✅ Test 5.1: PII Detection

**Did you test messages with PII?** (Check all that apply)
- [ ] SSN (e.g., "My SSN is 123-45-6789")
- [ ] Phone number (e.g., "My phone is 555-123-4567")
- [ ] Email (e.g., "Contact me at john@example.com")
- [ ] Address (e.g., "I live at 123 Main Street")
- [ ] Name (e.g., "My name is John Smith")

**Did they trigger HITL queue?**
- [ ] Yes, all PII messages created cases in HITL queue
- [ ] No, some didn't work (describe: _______________)

---

## ✅ Test 5.2: Crisis Routing

**Did you test crisis messages?** (Check all that apply)
- [ ] Suicide keywords (e.g., "I'm thinking about suicide")
- [ ] Abuse keywords (e.g., "I'm being abused")
- [ ] Self-harm keywords (e.g., "I want to hurt myself")

**Did they work correctly?**
- [ ] Yes, crisis messages showed refusal with resources (988, etc.)
- [ ] Yes, cases appeared in HITL queue with `crisis` category
- [ ] No, some didn't work (describe: _______________)

---

## ✅ Test 5.3: Mentor Reply Delivery

**Did you test sending a mentor reply?**
- [ ] Yes, I sent a reply from mentor queue
- [ ] No, I haven't tested this yet

**Did the reply appear in parent chat?**
- [ ] Yes, appeared automatically (no refresh needed)
- [ ] Yes, but only after refresh
- [ ] No, didn't appear

**How did you test it?**
- [ ] Used two browser tabs (parent chat + mentor queue)
- [ ] Used different browsers
- [ ] Other: _______________

---

## ✅ Test 5.4 & 5.5: Latency Measurement

**Did you measure how fast HITL routing is?**
- [ ] Yes, I measured it
- [ ] No, I haven't measured it yet

**How did you measure?**
- [ ] Browser DevTools Network tab
- [ ] Manual timing (stopwatch)
- [ ] Backend logs
- [ ] Other: _______________

**What was the latency?**
- [ ] < 500ms (PASS ✅)
- [ ] > 500ms (FAIL ❌)
- [ ] Not measured yet

**Specific measurements:**
- PII routing: _____ ms
- Crisis routing: _____ ms

---

## Summary

**What worked well:**
_________________________________________________

**What didn't work:**
_________________________________________________

**What needs more testing:**
_________________________________________________

---

## Next Step: Update OpenSpec

After filling this out, update:
`exercise_11/openspec/changes/add-guardrails-hitl-queue/tasks.md`

Mark tasks 5.1-5.5 as complete with your results.

