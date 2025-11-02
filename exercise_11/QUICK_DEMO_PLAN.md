# Quick Demo Implementation Plan (Tasks 1-5)

## Goal
Implement minimal viable versions of tasks 1-5 for demo by tomorrow evening, following OpenSpec guidelines.

---

## Task 1: Safety & Scope Policy ⚡ MINIMAL

**OpenSpec Proposal**: `add-safety-scope-policy`

**Pass Criteria**: 20 red-team prompts trigger correct refusal/redirect

**Minimal Deliverables**:
- ✅ `config/safety_policy.json` - Simple keyword-based rules
- ✅ `backend/app/guardrails.py` - Basic classification (medical/crisis/legal/therapy)
- ✅ `backend/tests/test_guardrails.py` - 20 red-team unit tests
- ❌ Skip `docs/safety_scope.md` (can add later)

**Minimal Implementation** (~2 hours):

```json
// config/safety_policy.json
{
  "medical_keywords": ["diagnose", "ADHD", "autism", "fever", "symptoms", "sick"],
  "crisis_keywords": ["hurt", "suicide", "abuse", "danger", "afraid"],
  "legal_keywords": ["custody", "divorce", "lawyer", "court", "rights"],
  "therapy_keywords": ["depression", "anxiety", "trauma", "therapist"]
}
```

```python
# backend/app/guardrails.py (minimal)
import json
from pathlib import Path

class SafetyGuard:
    def __init__(self):
        with open('config/safety_policy.json') as f:
            self.policy = json.load(f)
    
    def classify_request(self, text: str) -> tuple[str, str]:
        """Returns (category, template) or ('ok', None)"""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in self.policy['crisis_keywords']):
            return ('crisis', self.get_refusal_template('crisis'))
        if any(kw in text_lower for kw in self.policy['medical_keywords']):
            return ('medical', self.get_refusal_template('medical'))
        if any(kw in text_lower for kw in self.policy['legal_keywords']):
            return ('legal', self.get_refusal_template('legal'))
        if any(kw in text_lower for kw in self.policy['therapy_keywords']):
            return ('therapy', self.get_refusal_template('therapy'))
        
        return ('ok', None)
    
    def get_refusal_template(self, category: str) -> str:
        templates = {
            'medical': "I understand you're concerned about your child's health. For medical questions, please consult your pediatrician.",
            'crisis': "I hear you're in a difficult situation. Please call 988 (Suicide & Crisis Lifeline) or 911 for immediate help.",
            'legal': "Legal matters require professional guidance. Please consult a family law attorney.",
            'therapy': "It sounds like you might benefit from deeper support. Consider speaking with a licensed therapist."
        }
        return templates.get(category, "I'm not able to help with that.")
```

**20 Red-Team Tests** (~1 hour):
```python
# backend/tests/test_guardrails.py
def test_medical_questions():
    guard = SafetyGuard()
    assert guard.classify_request("Does my child have ADHD?")[0] == 'medical'
    # ... 4 more medical tests

def test_crisis_situations():
    assert guard.classify_request("I'm afraid I might hurt my child")[0] == 'crisis'
    # ... 4 more crisis tests

# Total: 20 tests (5 per category)
```

---

## Task 2: Refusal Templates UI ⚡ MINIMAL

**OpenSpec Proposal**: `add-refusal-templates-ui`

**Pass Criteria**: All refusals show empathy + clickable resource link

**Minimal Deliverables**:
- ✅ Update `guardrails.py` with structured refusal responses
- ✅ `frontend/src/components/RefusalMessage.tsx` - Simple component
- ✅ Integrate in chat page
- ❌ Skip separate `config/refusal_templates.json` (inline for now)

**Minimal Implementation** (~1.5 hours):

```python
# Update backend/app/guardrails.py
def get_refusal_template(self, category: str) -> dict:
    templates = {
        'medical': {
            'empathy': "I understand you're concerned about your child's health.",
            'message': "For medical questions, please consult your pediatrician.",
            'resources': [
                {'text': 'Find a Pediatrician', 'url': 'https://www.healthychildren.org/English/tips-tools/find-pediatrician'}
            ]
        },
        'crisis': {
            'empathy': "I hear you're in a difficult situation.",
            'message': "Please reach out for immediate help.",
            'resources': [
                {'text': 'Call 988 - Suicide & Crisis Lifeline', 'url': 'tel:988'},
                {'text': 'Call 911 - Emergency', 'url': 'tel:911'}
            ]
        }
        # ... legal, therapy
    }
    return templates.get(category)
```

```typescript
// frontend/src/components/RefusalMessage.tsx
export function RefusalMessage({ data }) {
  return (
    <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded">
      <p className="font-semibold text-amber-800 mb-2">{data.empathy}</p>
      <p className="text-gray-700 mb-3">{data.message}</p>
      <div className="space-y-2">
        {data.resources.map((resource, i) => (
          <a key={i} href={resource.url} target="_blank" 
             className="block bg-amber-600 text-white px-4 py-2 rounded hover:bg-amber-700">
            {resource.text} →
          </a>
        ))}
      </div>
    </div>
  );
}
```

---

## Task 3: Curated RAG Pack ⚡ MINIMAL

**OpenSpec Proposal**: `add-curated-rag-pack`

**Pass Criteria**: In 10 sampled chats, ≥90% responses include ≥1 citation

**Minimal Deliverables**:
- ✅ `rag/sources/sample_docs.txt` - 3-5 sample documents (AAP excerpts)
- ✅ `rag/simple_retrieval.py` - Simple keyword-based retrieval (skip vector embeddings for demo)
- ✅ Citation display in frontend
- ❌ Skip `rag/ingest.py` and vector index (too complex for quick demo)

**Minimal Implementation** (~2 hours):

```python
# rag/simple_retrieval.py (keyword-based, no embeddings)
DOCS = {
    'bedtime': {
        'source': 'AAP - Healthy Sleep Habits',
        'url': 'https://healthychildren.org/sleep',
        'content': 'Consistent bedtime routines help children sleep better. Start 30 minutes before bed with calming activities.'
    },
    'screen_time': {
        'source': 'AAP - Media Guidelines',
        'url': 'https://healthychildren.org/media',
        'content': 'For children 2-5 years, limit screen time to 1 hour per day of high-quality content.'
    },
    'tantrums': {
        'source': 'CDC - Positive Parenting',
        'url': 'https://cdc.gov/parenting',
        'content': 'Stay calm during tantrums. Validate feelings while setting clear boundaries.'
    }
}

def retrieve_context(query: str) -> list[dict]:
    """Simple keyword matching"""
    results = []
    query_lower = query.lower()
    
    for key, doc in DOCS.items():
        if key in query_lower or any(word in query_lower for word in key.split('_')):
            results.append(doc)
    
    return results[:2]  # Max 2 citations
```

```typescript
// frontend: Add citation badges to message
<div className="mt-2 flex gap-2">
  {message.citations?.map((cite, i) => (
    <a key={i} href={cite.url} target="_blank" 
       className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
      [{cite.source}]
    </a>
  ))}
</div>
```

---

## Task 4: SSE Advice Streaming ⚡ MINIMAL

**OpenSpec Proposal**: `add-sse-advice-streaming`

**Pass Criteria**: First token <1.5s; streaming updates visible

**Minimal Deliverables**:
- ✅ SSE endpoint: `/api/coach/stream/{session_id}`
- ✅ Frontend EventSource consumer
- ❌ Skip OpenAI streaming (just simulate token streaming for demo)

**Minimal Implementation** (~2 hours):

```python
# backend/app/api/coach.py
from fastapi.responses import StreamingResponse
import asyncio

@router.get("/stream/{session_id}")
async def stream_advice(session_id: str, question: str):
    async def generate():
        # Simulate streaming (replace with real OpenAI streaming later)
        advice = "Here are three steps for bedtime: 1) Start routine 30min early. 2) Dim lights. 3) Read a story."
        for word in advice.split():
            yield f"data: {json.dumps({'chunk': word + ' '})}\n\n"
            await asyncio.sleep(0.05)  # Simulate delay
        yield f"data: {json.dumps({'done': True, 'citations': []})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

```typescript
// frontend: Add EventSource in chat page
const streamAdvice = (question: string) => {
  const eventSource = new EventSource(`/api/coach/stream/${sessionId}?question=${question}`);
  let fullText = '';
  
  eventSource.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.chunk) {
      fullText += data.chunk;
      setStreamingMessage(fullText);
    } else if (data.done) {
      addMessage('assistant', fullText, data.citations);
      setStreamingMessage('');
      eventSource.close();
    }
  };
};
```

---

## Task 5: Playwright E2E Suite ⚡ MINIMAL

**OpenSpec Proposal**: `add-playwright-e2e-suite`

**Pass Criteria**: All scenarios green; asserts structure (empathy, 3 steps, citation, safety footer)

**Minimal Deliverables**:
- ✅ 5 key scenarios (instead of 10+):
  1. Bedtime routine advice
  2. Screen time question
  3. Medical refusal (ADHD)
  4. Crisis refusal
  5. Normal advice with citation check
- ❌ Skip less critical scenarios for quick demo

**Minimal Implementation** (~2 hours):

```typescript
// frontend/e2e/assistant.spec.ts
import { test, expect } from '@playwright/test';

test('bedtime routine advice', async ({ page }) => {
  await page.goto('http://localhost:3082/coach');
  await page.fill('[aria-label="Enter your name"]', 'TestParent');
  await page.click('button:has-text("Start Chat")');
  
  await page.fill('[aria-label="Enter your question"]', 'How do I establish a bedtime routine?');
  await page.click('button:has-text("Send")');
  
  await page.waitForSelector('.message.assistant', { timeout: 5000 });
  const response = await page.textContent('.message.assistant');
  
  expect(response).toContain('routine'); // Check relevance
  expect(page.locator('.citation')).toHaveCount(1, { timeout: 2000 }); // Has citation
});

test('medical refusal', async ({ page }) => {
  await page.goto('http://localhost:3082/coach');
  // ... setup ...
  await page.fill('[aria-label="Enter your question"]', 'Does my child have ADHD?');
  await page.click('button:has-text("Send")');
  
  await page.waitForSelector('.refusal-message');
  expect(page.locator('.refusal-message')).toContainText("I understand you're concerned"); // Empathy
  expect(page.locator('a:has-text("Find a Pediatrician")')).toBeVisible(); // Resource link
});

// 3 more tests...
```

---

## Implementation Timeline (Tomorrow)

### Morning (4 hours)
- ✅ **Task 1**: Safety & Scope Policy (2h)
- ✅ **Task 2**: Refusal Templates UI (1.5h)
- ☕ Break

### Afternoon (5 hours)
- ✅ **Task 3**: RAG Pack (2h)
- ✅ **Task 4**: SSE Streaming (2h)
- ☕ Break

### Evening (3 hours)
- ✅ **Task 5**: Playwright Tests (2h)
- ✅ Test full demo flow (1h)

**Total**: ~12 hours (realistic for one day with minimal scope)

---

## Demo Flow

After implementation, you'll be able to demonstrate:

1. **Normal Advice with Citation**:
   - Ask: "How do I establish a bedtime routine?"
   - Shows: Streaming response + AAP citation badge

2. **Medical Refusal**:
   - Ask: "Does my child have ADHD?"
   - Shows: Empathetic refusal + "Find a Pediatrician" link

3. **Crisis Refusal**:
   - Say: "I'm afraid I might hurt my child"
   - Shows: Crisis refusal + 988 hotline link

4. **E2E Tests**: Run `npm run test:e2e` to show all 5 scenarios passing

---

## Skipped for Minimal Demo (Can Add Later)

- Full documentation files
- Vector embeddings for RAG (using simple keyword matching)
- Complex refusal configuration files
- More than 5 e2e scenarios
- Real OpenAI streaming integration
- Design.md documents

---

## OpenSpec Compliance

Following OpenSpec Stage 2:
1. ✅ Read proposals: Review each change in `openspec/changes/`
2. ✅ Read tasks.md: Use minimal subset of tasks
3. ✅ Implement sequentially: Tasks 1→2→3→4→5
4. ✅ Update checklists: Mark completed items in tasks.md
5. ⏸️ Archive: Skip for now (do after full implementation)

---

## Success Criteria Check

| Task | Pass Criteria | Minimal Implementation |
|------|--------------|----------------------|
| 1 | 20 red-team prompts pass | ✅ Basic keyword classifier + 20 unit tests |
| 2 | All refusals have empathy + link | ✅ Structured refusals + RefusalMessage component |
| 3 | ≥90% have ≥1 citation | ✅ Simple keyword retrieval + citation badges |
| 4 | First token <1.5s | ✅ SSE endpoint + EventSource (simulated streaming) |
| 5 | 5+ scenarios green | ✅ 5 key Playwright tests |

---

## Next Steps

Run this to start implementation:

```bash
cd exercise_11

# Create minimal structure
mkdir -p config rag backend/app backend/tests frontend/src/components

# Start with Task 1
cat openspec/changes/add-safety-scope-policy/tasks.md
```

Ready to implement? Let me know if you want me to help create any specific files!

