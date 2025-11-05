# HITL Queue Testing Guide

This guide walks you through testing all HITL (Human-In-The-Loop) queue requirements.

## Prerequisites

1. Backend running on `http://localhost:8011`
2. Frontend running on `http://localhost:3082`
3. Two browser tabs/windows (one for parent chat, one for mentor queue)

---

## Test 5.1: PII Detection with Sample Data

**Goal:** Verify that messages containing PII trigger HITL queue creation.

### Test Cases

#### Test Case 1: SSN Detection
1. Open parent chat: `http://localhost:3082/coach/chat`
2. Start a session
3. Send message: **"My SSN is 123-45-6789. Can you help?"**
4. **Expected:** 
   - Message should be queued to HITL (not get AI response)
   - Should see: "Thank you for reaching out. A mentor will review your message and respond shortly..."

#### Test Case 2: Phone Number Detection
1. Send message: **"My phone number is 555-123-4567"**
2. **Expected:** HITL queue triggered

#### Test Case 3: Email Detection
1. Send message: **"Contact me at john.doe@example.com"**
2. **Expected:** HITL queue triggered

#### Test Case 4: Address Detection
1. Send message: **"I live at 123 Main Street, New York"**
2. **Expected:** HITL queue triggered

#### Test Case 5: Name Detection
1. Send message: **"My name is John Smith"**
2. **Expected:** HITL queue triggered

### Verification Steps

1. **Check HITL Queue:**
   - Open mentor queue: `http://localhost:3082/hitl/queue`
   - Verify the case appears in the queue
   - Check that category is `pii`
   - Check that user message contains the PII

2. **Check Parent Chat:**
   - Verify parent sees the HITL queued message
   - Verify no AI response was given

### Document Results

```markdown
✅ PII Detection Test Results:
- SSN: ✅ Detected (message: "My SSN is 123-45-6789")
- Phone: ✅ Detected (message: "My phone number is 555-123-4567")
- Email: ✅ Detected (message: "Contact me at john.doe@example.com")
- Address: ✅ Detected (message: "I live at 123 Main Street")
- Name: ✅ Detected (message: "My name is John Smith")

All PII patterns correctly trigger HITL queue.
```

---

## Test 5.2: Crisis Routing End-to-End

**Goal:** Verify crisis keywords route to HITL queue with proper handling.

### Test Cases

#### Test Case 1: Suicide Crisis
1. Open parent chat
2. Send message: **"I'm thinking about suicide. I need help."**
3. **Expected:**
   - Refusal message with crisis resources (988, etc.)
   - Case created in HITL queue
   - Category: `crisis`

#### Test Case 2: Abuse Crisis
1. Send message: **"I'm being abused by my partner"**
2. **Expected:**
   - Crisis refusal message with resources
   - HITL queue case created

#### Test Case 3: Self-Harm Crisis
1. Send message: **"I want to hurt myself"**
2. **Expected:** Crisis routing triggered

### Verification Steps

1. **Check Parent Chat:**
   - Verify refusal message appears with crisis resources
   - Verify message includes crisis hotline numbers (988, etc.)

2. **Check HITL Queue:**
   - Open mentor queue: `http://localhost:3082/hitl/queue`
   - Verify case appears with category `crisis`
   - Verify it's marked as high priority

3. **Check Case Details:**
   - Click on the case
   - Verify full conversation history is shown
   - Verify crisis message is captured

### Document Results

```markdown
✅ Crisis Routing Test Results:
- Suicide keywords: ✅ Detected, refusal message sent, HITL case created
- Abuse keywords: ✅ Detected, refusal message sent, HITL case created
- Self-harm keywords: ✅ Detected, refusal message sent, HITL case created

All crisis scenarios correctly route to HITL with proper refusal messages.
```

---

## Test 5.3: Verify Mentor Reply Appears in Parent Chat

**Goal:** Verify that mentor replies are delivered to parent chat in real-time.

### Test Steps

1. **Trigger HITL Case:**
   - Open parent chat: `http://localhost:3082/coach/chat`
   - Send a PII message: **"My name is John Smith"**
   - Note the session ID (check browser console or URL)

2. **Open Mentor Queue:**
   - Open mentor queue: `http://localhost:3082/hitl/queue`
   - Find the case (should show the PII message)
   - Click to view case details

3. **Send Mentor Reply:**
   - Type a reply: **"Thank you for reaching out. I've reviewed your message and I'm here to help. Please feel free to ask your parenting question without sharing personal information."**
   - Click "Send Reply" button

4. **Verify in Parent Chat:**
   - Switch back to parent chat tab
   - **Expected:** Mentor reply should appear automatically (via SSE)
   - No page refresh needed
   - Reply should appear in the chat history

### Verification Checklist

- [ ] Mentor reply appears in parent chat
- [ ] No page refresh needed (real-time delivery)
- [ ] Reply appears in correct session
- [ ] Message formatting is correct
- [ ] Case status updates to "resolved" in mentor queue

### Document Results

```markdown
✅ Mentor Reply Delivery Test:
- Mentor reply sent: ✅
- Reply appeared in parent chat: ✅ (real-time, no refresh needed)
- SSE delivery working: ✅
- Case status updated: ✅

Mentor replies are correctly delivered to parent chat via SSE.
```

---

## Test 5.4 & 5.5: Measure Routing Latency

**Goal:** Verify HITL routing happens quickly (<500ms from trigger to queue creation).

### Method 1: Browser DevTools (Recommended)

1. **Open Browser DevTools:**
   - Open parent chat: `http://localhost:3082/coach/chat`
   - Press F12 (or right-click → Inspect)
   - Go to **Network** tab
   - Filter by **Fetch/XHR** or **WS** (for WebSocket)

2. **Trigger HITL:**
   - Send a PII message: **"My name is John Smith"**
   - Watch the Network tab

3. **Measure Latency:**
   - Look for the SSE request: `/api/coach/stream/{session_id}`
   - Check the **Timing** tab
   - Look for:
     - **Time to First Byte (TTFB):** When server responds
     - **Content Download:** When stream completes
   - Or check the **Response** tab - look for when HITL queued message arrives

4. **Alternative: Check Backend Logs:**
   - Look at backend console output
   - Find the log entry for HITL case creation
   - Note the timestamp

### Method 2: Backend Timing (More Accurate)

1. **Add Timing Logs:**
   - Check backend code: `backend/app/guardrails.py`
   - Look for `create_hitl_case()` function
   - The function should log when it's called

2. **Measure from Request to Queue:**
   - Time when request arrives (from FastAPI logs)
   - Time when HITL case is created (from guardrails logs)
   - Calculate difference

### Method 3: Manual Timing (Simple)

1. **Open mentor queue:** `http://localhost:3082/hitl/queue`
2. **Open parent chat** in another tab
3. **Note the current time** (or use a stopwatch)
4. **Send PII message** in parent chat
5. **Watch mentor queue** - note when case appears
6. **Calculate difference**

**Expected:** < 500ms (0.5 seconds)

### Document Results

```markdown
✅ Routing Latency Test Results:

Test 1: PII Message
- Time to HITL queue creation: ~250ms
- Status: ✅ PASS (< 500ms threshold)

Test 2: Crisis Message  
- Time to HITL queue creation: ~300ms
- Status: ✅ PASS (< 500ms threshold)

Average latency: ~275ms
All routing meets <500ms requirement.
```

---

## Complete Test Checklist

### Test 5.1: PII Detection
- [ ] SSN detected
- [ ] Phone number detected
- [ ] Email detected
- [ ] Address detected
- [ ] Name detected
- [ ] All cases appear in HITL queue

### Test 5.2: Crisis Routing
- [ ] Suicide keywords trigger crisis routing
- [ ] Abuse keywords trigger crisis routing
- [ ] Self-harm keywords trigger crisis routing
- [ ] Refusal messages include crisis resources
- [ ] Cases appear in HITL queue with `crisis` category

### Test 5.3: Mentor Reply Delivery
- [ ] Mentor can view case details
- [ ] Mentor can send reply
- [ ] Reply appears in parent chat (real-time)
- [ ] No page refresh needed
- [ ] Case status updates to resolved

### Test 5.4 & 5.5: Latency Measurement
- [ ] PII routing latency measured
- [ ] Crisis routing latency measured
- [ ] All latencies < 500ms
- [ ] Results documented

---

## Documenting Results in OpenSpec

After completing tests, update `exercise_11/openspec/changes/add-guardrails-hitl-queue/tasks.md`:

```markdown
## 5. Testing
- [x] 5.1 Test PII detection with sample data
  - ✅ SSN, phone, email, address, name all detected
  - ✅ All cases appear in HITL queue
  
- [x] 5.2 Test crisis routing end-to-end
  - ✅ Suicide, abuse, self-harm keywords trigger routing
  - ✅ Refusal messages include crisis resources
  - ✅ Cases appear in HITL queue
  
- [x] 5.3 Verify mentor reply appears in parent chat
  - ✅ Replies delivered via SSE in real-time
  - ✅ No page refresh needed
  
- [x] 5.4 Measure routing latency
  - ✅ PII: ~250ms
  - ✅ Crisis: ~300ms
  
- [x] 5.5 Assert <500ms from trigger to queue creation
  - ✅ All latencies < 500ms (average: ~275ms)
```

---

## Troubleshooting

### HITL Cases Not Appearing

**Check:**
- Backend is running: `curl http://localhost:8011/healthz`
- Frontend is connected to correct backend URL
- Browser console for errors
- Backend logs for errors

### Mentor Replies Not Appearing

**Check:**
- SSE connection is active (check Network tab)
- Session ID matches
- Backend SSE endpoint is working
- Browser console for SSE errors

### High Latency

**Check:**
- Backend performance (CPU, memory)
- Network latency
- Database/file system performance (if using)
- Check backend logs for slow operations

---

## Quick Test Script

For quick verification, you can use curl:

```bash
# Test PII detection
curl -X POST http://localhost:8011/api/coach/start \
  -H "Content-Type: application/json" \
  -d '{"parent_name": "Test Parent"}'

# Note the session_id from response, then:
curl "http://localhost:8011/api/coach/stream/{session_id}?question=My%20name%20is%20John%20Smith"

# Check HITL queue
curl http://localhost:8011/api/hitl/queue
```

---

## Next Steps

After completing all tests:
1. Document results in OpenSpec tasks.md
2. Update proposal.md with testing status
3. Mark tasks as complete

