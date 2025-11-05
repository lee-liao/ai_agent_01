# Playwright E2E Test Failures Analysis

## Summary

**Status:** 6/8 tests passing (75%)  
**Failing Tests:** 2 tests related to citations

## Problem Identified

From the error context files, all test responses include:
1. ✅ Valid AI-generated content (the actual advice)
2. ❌ Error message appended: "I apologize, but I'm having trouble generating a response right now. Please try again."
3. ❌ **Citations are not visible** in the page snapshots

## Root Cause Analysis

### Issue 1: Error Message Appended to Responses

**Location:** `backend/app/api/coach.py:206-222`

The error handler catches exceptions (likely during cost tracking) and appends an error message to the response:

```python
except Exception as e:
    # ... error logging ...
    error_msg = "I apologize, but I'm having trouble generating a response right now. Please try again."
    yield f"data: {json.dumps({'chunk': error_msg})}\n\n"
    yield f"data: {json.dumps({'done': True, 'citations': []})}\n\n"
```

**Problem:** When an error occurs, citations are sent as an empty array `[]`, so no citations appear in the UI.

**Likely Cause:** Cost tracking in `billing.ledger.log_usage()` is failing, causing the exception handler to trigger.

### Issue 2: Citations Not Rendered

**Expected Behavior:**
- Citations should appear below the message with `data-testid="citation"`
- Citations are rendered only if `m.citations && m.citations.length > 0`

**Actual Behavior:**
- Citations array is empty when error occurs
- Even when streaming succeeds, citations might not be sent properly

## Failing Tests

### Test 1: "Bedtime routine advice with citation" (Test #1)
- **Expected:** Citation visible with `data-testid="citation"`
- **Actual:** Response has content but no citations visible
- **Assertion Failure:** `await expect(citation).toBeVisible({ timeout: 2000 })`

### Test 2: "Screen time question with AAP citation" (Test #2)  
- **Expected:** Citation visible and mentions "AAP"
- **Actual:** Response has content but no citations visible
- **Assertion Failure:** `await expect(citation).toBeVisible()`

### Test 3: "Citation rate meets 90% threshold" (Test #8)
- **Expected:** At least 90% of responses have citations (3/3 = 100%)
- **Actual:** 0/3 responses have citations (0%)
- **Assertion Failure:** `expect(citationRate).toBeGreaterThanOrEqual(90)`

## Solutions

### Solution 1: Fix Cost Tracking Error (Recommended)

The cost tracking error is causing the exception handler to trigger. We should:

1. **Make cost tracking non-blocking:**
   ```python
   # After sending citations and done signal
   try:
       from billing.ledger import get_tracker
       tracker = get_tracker()
       # ... cost tracking ...
   except Exception as cost_error:
       # Log but don't fail the request
       logger.warning(f"Cost tracking failed: {type(cost_error).__name__}")
       # Don't send error message - request already succeeded
   ```

2. **Ensure citations are sent BEFORE cost tracking:**
   - Already done (line 180), but error handler might be catching earlier exceptions

### Solution 2: Improve Error Handling

Don't append error message if streaming already succeeded:

```python
except Exception as e:
    # Only send error if we haven't sent the done signal yet
    if not stream_complete:
        error_msg = "I apologize, but I'm having trouble generating a response right now. Please try again."
        yield f"data: {json.dumps({'chunk': error_msg})}\n\n"
        yield f"data: {json.dumps({'done': True, 'citations': []})}\n\n"
```

### Solution 3: Verify Citation Data Flow

Check that citations are being:
1. ✅ Extracted from RAG context (line 154-157)
2. ✅ Sent in done signal (line 181)
3. ✅ Parsed in frontend (line 196)
4. ✅ Rendered in UI (line 398-414)

## Next Steps

1. Check backend logs for cost tracking errors
2. Fix cost tracking to be non-blocking
3. Ensure citations are sent even if cost tracking fails
4. Re-run tests to verify citations appear

## Test Status

- ✅ Test 3: Medical refusal - ADHD question (PASS)
- ✅ Test 4: Crisis refusal - escalation to 988 (PASS)
- ✅ Test 5: Normal advice with structure check (PASS - content check works)
- ✅ Test 6: Streaming behavior (PASS)
- ✅ Test 7: All refusals have empathy and resources (PASS)
- ❌ Test 1: Bedtime routine advice with citation (FAIL - no citation)
- ❌ Test 2: Screen time question with AAP citation (FAIL - no citation)
- ❌ Test 8: Citation rate meets 90% threshold (FAIL - 0% citation rate)

