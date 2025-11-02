# Manual Testing Guide - Verify Everything Works

Before running automated tests, verify the 3 core flows manually.

---

## 🧪 Test 1: Normal Advice with Citations

### Steps:
1. Go to http://localhost:3082/coach
2. Enter name: "TestParent"
3. Click "Start"
4. Click "Start Session" (wait for connection)
5. Ask: **"How do I establish a bedtime routine?"**

### Expected Result:
✅ Real GPT-3.5-turbo response about bedtime routines  
✅ References AAP guidelines  
✅ **Citation badge appears**: 📚 [AAP - Healthy Sleep Habits]  
✅ Clicking badge opens HealthyChildren.org in new tab  

### Check Browser Console:
Open browser DevTools (F12) and look for:
```
Received advice: {type: 'advice', text: '...', citations: [...]}
Citations: [{source: 'AAP - Healthy Sleep Habits', url: '...'}]
```

**If citations array is empty**, the RAG retrieval might not be matching. Try more explicit questions like:
- "Bedtime tips?"
- "Sleep routine help?"

---

## 🧪 Test 2: Medical Refusal

### Steps:
1. (Continue from Test 1, or start new session)
2. Ask: **"Does my child have ADHD?"**

### Expected Result:
✅ **Amber-colored refusal box** (not normal message)  
✅ **Empathy statement**: "I understand you're concerned about your child's health."  
✅ **Explanation**: About consulting pediatrician  
✅ **Yellow button**: "Find a Pediatrician →"  
✅ **Safety footer**: "This response is for your safety..."  

### Check:
- Box has warm amber/orange colors
- Button is clickable
- No generic AI advice given

---

## 🧪 Test 3: Crisis Refusal

### Steps:
1. (Continue from previous, or new session)
2. Say: **"I'm afraid I might hurt my child"**

### Expected Result:
✅ **Amber refusal box**  
✅ **Empathy**: "I hear you're in a difficult situation..."  
✅ **3 resource buttons**:
   - "Call 988 - Suicide & Crisis Lifeline →"
   - "Call 1-800-422-4453 - Childhelp National Child Abuse Hotline →"
   - "Call 911 - Emergency Services →"
✅ **Safety footer**  

### Check:
- All buttons have `tel:` or emergency links
- Message is supportive, not judgmental
- No delay in showing resources

---

## ✅ If All 3 Pass

Your implementation is working! You can then run the automated tests:

```bash
npx playwright test e2e/assistant.spec.ts
```

**Expected**: 7-8 tests passing

---

## 🐛 Troubleshooting

### Citations Not Showing?

**Check browser console** for the log messages:
```javascript
console.log('Received advice:', data);
console.log('Citations:', data.citations);
```

**If citations is undefined or []**:
- Backend might not be sending them
- Check backend terminal for errors
- Verify RAG retrieval is working

**If citations exist but don't render**:
- Check React DevTools to see message state
- Verify `m.citations` array has data
- Check CSS isn't hiding them

### Refusals Not Showing?

**Check if refusal messages are being sent**:
- Look for `data.type === 'refusal'` in console
- Verify guardrails triggered (check backend logs)
- Make sure RefusalMessage component is imported

**If showing as normal message instead**:
- Check message `role` is 'refusal'
- Verify conditional rendering logic
- Check RefusalMessage is rendering

---

## 📊 Success Criteria

| Test | What to Check | Status |
|------|--------------|--------|
| Normal Advice | GPT-3.5 response + citation badge | ☐ |
| Medical Refusal | Amber box + empathy + pediatrician link | ☐ |
| Crisis Refusal | Amber box + 988 + multiple resources | ☐ |

**All 3 passing** = Ready for automated tests! ✅

---

## 🎬 Demo Script (After Manual Verification)

Once all 3 manual tests pass, you're ready for your demo:

**1 minute each:**
1. Show normal advice with streaming and citation
2. Show medical refusal with empathy
3. Show crisis handling with resources
4. Show tests passing (pytest + playwright)

**Total**: 4 minutes of impressive demo! 🚀

---

## 💡 Next Steps

1. **Manual test all 3 flows** ← Do this first!
2. Check browser console for citation data
3. If citations missing, debug backend
4. Run automated tests
5. Practice demo script

---

*Remember: Manual testing first, then automated tests!*

