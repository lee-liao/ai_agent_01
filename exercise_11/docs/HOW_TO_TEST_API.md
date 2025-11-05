# How to Test the Coach API Endpoint

**Endpoint:** `POST http://localhost:8011/api/coach/start`

**Note:** 
- Backend API runs on port **8011** (not 3082)
- Port 3082 is the **frontend** (React app)
- You don't need Postman - there are many alternatives!

---

## 🎯 Option 1: Using curl (Command Line)

### Windows PowerShell:
```powershell
curl -X POST http://localhost:8011/api/coach/start `
  -H "Content-Type: application/json" `
  -d '{\"parent_name\": \"Test Parent\"}'
```

### Windows CMD:
```cmd
curl -X POST http://localhost:8011/api/coach/start -H "Content-Type: application/json" -d "{\"parent_name\": \"Test Parent\"}"
```

### Linux/Mac:
```bash
curl -X POST http://localhost:8011/api/coach/start \
  -H "Content-Type: application/json" \
  -d '{"parent_name": "Test Parent"}'
```

**Expected Response:**
```json
{
  "session_id": "sess_abc123def456",
  "message": "Welcome Test Parent! You can start chatting with your parenting coach."
}
```

---

## 🎯 Option 2: Using PowerShell (Invoke-RestMethod)

```powershell
$body = @{
    parent_name = "Test Parent"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8011/api/coach/start" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

---

## 🎯 Option 3: Using Python

```python
import requests

response = requests.post(
    "http://localhost:8011/api/coach/start",
    json={"parent_name": "Test Parent"}
)

print(response.json())
# Output: {'session_id': 'sess_...', 'message': 'Welcome ...'}
```

**Run it:**
```bash
python -c "import requests; print(requests.post('http://localhost:8011/api/coach/start', json={'parent_name': 'Test Parent'}).json())"
```

---

## 🎯 Option 4: Using the Frontend (Easiest!)

The frontend at `http://localhost:3082` already has a UI that calls this endpoint!

1. Open browser: `http://localhost:3082/coach`
2. Enter a parent name
3. Click "Start Session"
4. The frontend automatically calls `/api/coach/start`

**No manual API calls needed!**

---

## 🎯 Option 5: Using Postman (If You Prefer GUI)

1. **Method:** POST
2. **URL:** `http://localhost:8011/api/coach/start`
3. **Headers:**
   - `Content-Type: application/json`
4. **Body (raw JSON):**
   ```json
   {
     "parent_name": "Test Parent"
   }
   ```
5. Click "Send"

---

## 🎯 Option 6: Using Browser DevTools (For Testing)

1. Open browser: `http://localhost:3082/coach`
2. Open DevTools (F12)
3. Go to **Console** tab
4. Run:
   ```javascript
   fetch('http://localhost:8011/api/coach/start', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ parent_name: 'Browser Test' })
   })
   .then(r => r.json())
   .then(console.log)
   ```

---

## 🎯 Option 7: Using FastAPI Docs (Swagger UI)

FastAPI automatically generates interactive API documentation!

1. Start backend: `uvicorn app.main:app --port 8011`
2. Open browser: `http://localhost:8011/docs`
3. Find `/api/coach/start` endpoint
4. Click "Try it out"
5. Enter JSON:
   ```json
   {
     "parent_name": "Swagger Test"
   }
   ```
6. Click "Execute"

**This is the easiest way to test without any tools!**

---

## ✅ Quick Test Script

Save this as `test_api.ps1`:

```powershell
# Test Coach API
$response = Invoke-RestMethod -Uri "http://localhost:8011/api/coach/start" `
  -Method POST `
  -ContentType "application/json" `
  -Body (@{ parent_name = "PowerShell Test" } | ConvertTo-Json)

Write-Host "Session ID: $($response.session_id)"
Write-Host "Message: $($response.message)"
```

**Run it:**
```powershell
.\test_api.ps1
```

---

## 🐛 Troubleshooting

**"Connection refused" or "Cannot connect"?**
- Check if backend is running: `curl http://localhost:8011/healthz`
- Start backend: `cd exercise_11/backend && uvicorn app.main:app --port 8011`

**"404 Not Found"?**
- Verify endpoint: Should be `/api/coach/start` (not `/coach/start`)
- Check backend logs for route registration

**"422 Unprocessable Entity"?**
- Check JSON format: `{"parent_name": "..."}` (not `{"parentName": "..."}`)
- Verify `Content-Type: application/json` header

**CORS errors?**
- Make sure you're testing from the correct origin
- Or test directly to backend (port 8011) instead of frontend (port 3082)

---

## 📝 Summary

**You DON'T need Postman!** Choose any method:

1. ✅ **FastAPI Docs** (`http://localhost:8011/docs`) - Easiest GUI option
2. ✅ **Frontend UI** (`http://localhost:3082/coach`) - Best for end-to-end testing
3. ✅ **curl** - Quick command line test
4. ✅ **PowerShell** - Native Windows option
5. ✅ **Python** - If you're already using Python
6. ✅ **Browser DevTools** - Quick browser-based test
7. ✅ **Postman** - Only if you prefer it

**Recommended:** Use FastAPI Docs (`/docs`) for quick API testing, or the frontend UI for real-world scenarios!

