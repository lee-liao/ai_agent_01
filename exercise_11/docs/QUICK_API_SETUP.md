# Quick OpenAI API Setup (2 Minutes)

## 🔧 What I Fixed

1. ✅ Added path setup in `main.py` so `rag` module can be found
2. ✅ Made API key optional (won't crash without it)
3. ✅ Added helpful error messages if API key missing
4. ✅ WebSocket now uses real OpenAI + guardrails + RAG

---

## 🚀 Setup (2 Steps)

### Step 1: Install OpenAI Package
```bash
cd exercise_11/backend
pip install openai==1.12.0
```

### Step 2: Create `.env` File
Create file: `exercise_11/backend/.env`

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
CORS_ORIGINS=http://localhost:3082,http://localhost:3000
```

**Get your API key**: https://platform.openai.com/api-keys

### Step 3: Restart Backend
```bash
# Stop current server (Ctrl+C)
# Then start again:
uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload
```

---

## 🧪 Test It

Now ask your question again:

**"What level am I allowed to punish my naughty boy?"**

### What Will Happen:

1. ✅ **Guardrails check**: "punish" → searches keywords
   - Not in medical/crisis/legal keywords
   - Checks therapy keywords → no match
   - **Result**: OK to proceed ✅

2. ✅ **RAG retrieval**: Searches for "punish"
   - Finds keyword match: "discipline" topic
   - Retrieves AAP Effective Discipline article

3. ✅ **OpenAI call**:
   ```
   System: You are a supportive parenting coach...
   
   Research Context:
   Source: AAP - Effective Discipline
   Content: The AAP recommends positive discipline approaches...
   
   User: What level am I allowed to punish my naughty boy?
   ```

4. ✅ **GPT-3.5 Response** (real AI):
   - Understands "punishment" context
   - References AAP discipline guidelines
   - Suggests positive approaches (time-outs, natural consequences)
   - Discourages physical punishment
   - **Will be completely different from the generic response!**

5. ✅ **Citations**: [AAP - Effective Discipline] badge

---

## 🎯 Expected Response (After Setup)

Instead of:
> ❌ "I hear you. Here are a few ideas you might try: 1) Acknowledge feelings, 2) Offer a simple choice, 3) Keep routines consistent."

You'll get something like:
> ✅ "Based on AAP - Effective Discipline: It's important to approach discipline with the goal of teaching, not punishing. The AAP recommends avoiding physical punishment and instead using positive discipline approaches. Here are some age-appropriate strategies: 1) Use time-outs (1 minute per year of age), 2) Apply natural consequences when safe, 3) Redirect to positive behaviors. Remember, the goal is teaching self-control and helping your child understand expectations. Being consistent between caregivers is key for effectiveness."
> 
> **[AAP - Effective Discipline]** ← Clickable citation

**Much more specific and helpful!** 🎯

---

## 💰 Cost

**Your question costs**: ~$0.001 (0.1 cents)

Very affordable for demo testing!

---

## ⚠️ If You See This Error

```
⚠️ OpenAI API not configured. Please set OPENAI_API_KEY in backend/.env file.
```

**Solution**: You forgot step 2. Create the `.env` file with your API key.

---

## ✅ Verify It's Working

**Without API key**:
- ❌ Response: "⚠️ OpenAI API not configured..."

**With API key**:
- ✅ Response: Detailed, contextual advice
- ✅ Different every time (AI-generated)
- ✅ References AAP guidelines
- ✅ Specific to your question

---

**Setup these 2 things and restart the server - then ask again!** 🚀

