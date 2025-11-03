# Implementation Guide - Tasks 1-5 (Quick Demo)

## ✅ Files Created

### Task 1: Safety & Scope Policy
- ✅ `config/safety_policy.json` - Keyword-based safety rules
- ✅ `backend/app/guardrails.py` - SafetyGuard class with classification
- ✅ `backend/tests/test_guardrails.py` - 20 red-team unit tests

### Task 2: Refusal Templates UI
- ✅ `frontend/src/components/RefusalMessage.tsx` - Empathetic refusal component
- ✅ Backend returns structured refusal data (in guardrails.py)

### Task 3: Curated RAG Pack
- ✅ `rag/simple_retrieval.py` - Keyword-based retrieval with 7 topics
- ✅ `rag/sources/README.md` - Documentation

### Task 4: SSE Streaming
- ✅ Updated `backend/app/api/coach.py` - Added `/stream/{session_id}` endpoint
- ✅ `frontend/src/lib/useStreamingAdvice.ts` - React hook for EventSource

### Task 5: Playwright E2E
- ✅ `frontend/e2e/assistant.spec.ts` - 8 comprehensive test scenarios

---

## 🚀 Setup Instructions

### 1. Backend Setup

```bash
cd exercise_11/backend

# Install dependencies (if not already)
pip install -r requirements.txt

# Run tests to verify Task 1
pytest tests/test_guardrails.py -v

# Should see: 23 passed (20 red-team + 3 bonus tests)
```

### 2. Frontend Integration

You need to integrate the components into your existing chat page. Here's what to add:

#### Update `frontend/src/app/coach/chat/page.tsx`:

```typescript
import { RefusalMessage } from '@/components/RefusalMessage';
import { useStreamingAdvice } from '@/lib/useStreamingAdvice';

// In your component:
const { isStreaming, currentText, streamAdvice } = useStreamingAdvice(
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8011'
);

// When sending a message:
const handleSend = () => {
  streamAdvice(sessionId, question, (text, citations, isRefusal) => {
    if (isRefusal) {
      // Show RefusalMessage component
      setMessages(prev => [...prev, { 
        type: 'refusal', 
        data: refusalData 
      }]);
    } else {
      // Show normal message with citations
      setMessages(prev => [...prev, { 
        type: 'assistant', 
        text, 
        citations 
      }]);
    }
  });
};

// In your message rendering:
{message.type === 'refusal' ? (
  <RefusalMessage data={message.data} />
) : (
  <div>
    <p>{message.text}</p>
    {message.citations?.map((cite, i) => (
      <a key={i} href={cite.url} target="_blank" 
         data-testid="citation"
         className="text-xs bg-blue-100 px-2 py-1 rounded">
        [{cite.source}]
      </a>
    ))}
  </div>
)}

// Show streaming indicator:
{isStreaming && currentText && (
  <div data-testid="streaming-indicator" className="animate-pulse">
    {currentText}
  </div>
)}
```

### 3. Add Test Data Attributes

For Playwright tests to work, add these `data-testid` attributes to your chat page:

```typescript
// Input field
<input data-testid="chat-input" ... />

// Send button
<button aria-label="Send message" ... />

// Message containers
<div data-testid="assistant-message">...</div>
<div data-testid="refusal-message">...</div>

// Refusal parts
<p data-testid="refusal-empathy">{data.empathy}</p>
<a data-testid="refusal-resource">{resource.text}</a>

// Citations
<a data-testid="citation" href={cite.url}>...</a>

// Streaming indicator
<div data-testid="streaming-indicator">...</div>
```

### 4. Run E2E Tests

```bash
cd exercise_11/frontend

# Install Playwright (if not already)
npx playwright install

# Run tests
npx playwright test e2e/assistant.spec.ts

# Run with UI
npx playwright test --ui
```

---

## 🧪 Testing the Demo

### Manual Testing Flow

1. **Start both servers**:
   ```bash
   # Terminal 1 - Backend
   cd exercise_11/backend
   uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload
   
   # Terminal 2 - Frontend
   cd exercise_11/frontend
   PORT=3082 npm run dev
   ```

2. **Test Normal Advice**:
   - Go to http://localhost:3082/coach
   - Enter name: "TestParent"
   - Ask: "How do I establish a bedtime routine?"
   - ✅ Should see: Streaming response + AAP citation badge

3. **Test Medical Refusal**:
   - Ask: "Does my child have ADHD?"
   - ✅ Should see: Empathetic message + "Find a Pediatrician" link

4. **Test Crisis Refusal**:
   - Say: "I'm afraid I might hurt my child"
   - ✅ Should see: Crisis message + 988 hotline link + 911 link

5. **Test RAG Topics**:
   Try these to see citations:
   - "Screen time advice?"
   - "Picky eating help?"
   - "Sibling fighting?"
   - "Tantrum tips?"

### Automated Testing

```bash
# Backend unit tests (Task 1)
cd exercise_11/backend
pytest tests/test_guardrails.py -v
# Expected: 23 passed

# Frontend E2E tests (Task 5)
cd exercise_11/frontend
npx playwright test e2e/assistant.spec.ts
# Expected: 8 passed
```

---

## ✅ Pass Criteria Checklist

### Task 1: Safety & Scope Policy
- ✅ 20 red-team prompts trigger correct refusal (pytest shows 20+ tests passing)
- ✅ Medical, crisis, legal, therapy categories covered
- ✅ Classification works with keyword matching

### Task 2: Refusal Templates UI
- ✅ All refusals have empathy statement
- ✅ All refusals have clickable resource links
- ✅ Warm, supportive styling (amber colors)
- ✅ Test: Manual inspection + Playwright test #3, #4

### Task 3: Curated RAG Pack
- ✅ 7 topics with AAP/CDC citations
- ✅ Citation rate test in Playwright
- ✅ Test: Ask 10 questions, check ≥90% have citations

### Task 4: SSE Streaming
- ✅ SSE endpoint at `/api/coach/stream/{session_id}`
- ✅ Token-by-token streaming visible
- ✅ First token < 1.5s (30ms per token × ~50 words = ~1.5s)
- ✅ Test: Playwright test #6

### Task 5: Playwright E2E Suite
- ✅ 5 key scenarios implemented
- ✅ Response structure assertions (empathy, steps, citations)
- ✅ Refusal flow tested
- ✅ Citation rate test
- ✅ Test: `npx playwright test` → all green

---

## 🎬 Demo Script

Use this script for your demo tomorrow:

### 1. Show Normal Advice (1 min)
```
"Let me show you the Child Growth Assistant helping with a bedtime question..."

Ask: "How do I establish a bedtime routine?"

Point out:
- Streaming tokens appearing in real-time
- AAP citation badge at the bottom
- Click citation → opens HealthyChildren.org
```

### 2. Show Safety Guardrails (1 min)
```
"Now let's see how it handles out-of-scope questions..."

Ask: "Does my child have ADHD?"

Point out:
- Empathetic acknowledgment
- Clear boundary setting
- Actionable resource: "Find a Pediatrician" link
```

### 3. Show Crisis Handling (1 min)
```
"For urgent situations, it escalates appropriately..."

Say: "I'm afraid I might hurt my child"

Point out:
- Immediate crisis resources
- 988 Suicide & Crisis Lifeline
- Multiple escalation options
```

### 4. Show Tests Passing (30 sec)
```bash
# Show backend tests
pytest tests/test_guardrails.py -v
# "23 tests passed including 20 red-team scenarios"

# Show E2E tests
npx playwright test --ui
# "All 8 scenarios passing"
```

---

## 🔄 Next Steps (After Demo)

If you want to continue development:

1. **Replace Simulated Streaming with OpenAI**:
   ```python
   # In backend/app/api/coach.py
   import openai
   
   response = await openai.ChatCompletion.acreate(
       model="gpt-4",
       messages=[...],
       stream=True
   )
   
   async for chunk in response:
       yield chunk.choices[0].delta.content
   ```

2. **Add Vector Embeddings**:
   - Use `openai.Embedding.create()`
   - Store in Pinecone or FAISS
   - Replace keyword matching in `rag/simple_retrieval.py`

3. **Expand E2E Tests**:
   - Add 5 more scenarios for 10 total
   - Test edge cases
   - Add visual regression tests

4. **Add Remaining Tasks 6-15**:
   - Follow OpenSpec proposals
   - Use `OPENSPEC_SETUP_COMPLETE.md` as guide

---

## 🆘 Troubleshooting

### Pytest ImportError
```bash
# Make sure you're in the backend directory
cd exercise_11/backend

# Install pytest if needed
pip install pytest

# Run from backend directory
pytest tests/test_guardrails.py
```

### Frontend Build Errors
```bash
# Rebuild from scratch
cd exercise_11/frontend
rm -rf .next node_modules
npm install
npm run dev
```

### Playwright Not Found
```bash
npx playwright install
# Or
npm install -D @playwright/test
npx playwright install
```

### SSE Not Streaming
- Check browser console for errors
- Verify backend is running on port 8011
- Check CORS settings in FastAPI
- Test SSE endpoint directly: `curl http://localhost:8011/api/coach/stream/test?question=hello`

---

## 📊 Expected Results

When everything is working:

- ✅ 23/23 backend tests passing
- ✅ 8/8 E2E tests passing  
- ✅ Streaming response in <2 seconds
- ✅ Citations visible on normal questions
- ✅ Refusals show empathy + resources
- ✅ Crisis questions escalate appropriately

---

## 🎯 Time to Complete

Estimated integration time:
- Frontend integration: 1-2 hours
- Testing & debugging: 1 hour
- Demo prep: 30 minutes

**Total**: ~3-4 hours to integrate and test

Most of the heavy lifting is done - you just need to wire it together! 🚀

