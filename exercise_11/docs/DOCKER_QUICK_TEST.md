# Docker Quick Test Guide

## 🐳 Test Docker Setup (Tomorrow Morning - 15 minutes)

### Prerequisites

Make sure you have your OpenAI API key in `.env`:

```bash
# Create .env in exercise_11/ directory
cd exercise_11
echo "OPENAI_API_KEY=sk-your-actual-key-here" > .env
```

---

## 🚀 Test 1: Start with Docker (10 min)

```bash
cd exercise_11

# Start everything
docker compose up

# Expected output:
# [+] Building...
# [+] Creating network "child-growth-network"
# [+] Starting child-growth-backend...
# [+] Starting child-growth-frontend...
# 
# Wait for health checks to pass...
# ✅ backend healthy
# ✅ frontend healthy (depends on backend)
#
# Total time: ~15-20 seconds ✅
```

### While It's Building (First Time):

Building takes 2-5 minutes the **first time** because it:
1. Downloads Python 3.11 image
2. Downloads Node 18 image  
3. Installs all dependencies
4. Sets up volumes

**Subsequent starts**: ~10-15 seconds (uses cached images)

---

## 🧪 Test 2: Verify Services (2 min)

### Backend Health:
```bash
curl http://localhost:8011/healthz
# Expected: {"status":"ok"}

curl http://localhost:8011/readyz
# Expected: {"ready":true,"checks":{...}}
```

### Frontend:
```bash
curl http://localhost:3082
# Expected: HTML content (Next.js page)
```

### Chat Works:
1. Open browser: http://localhost:3082/coach
2. Enter name, start session
3. Ask "Bedtime tips?"
4. Should see: Streaming response + citation ✅

---

## 🎬 For Demo

### Start Services:
```bash
# Clean start for demo
docker compose down
docker compose up

# Point out during startup:
- "Building optimized containers..."
- "Health checks validating readiness..."
- "Both services healthy in 15 seconds!" ✅
```

### Show It Works:
```bash
# Terminal 2 - While services are up
curl http://localhost:8011/readyz

# Show JSON:
{
  "ready": true,
  "checks": {
    "openai_key_configured": true,
    "rag_module_available": true,
    "config_file_exists": true
  },
  "message": "Service ready"
}
```

**Say**: "Health checks ensure services are truly ready before accepting traffic - production best practice"

---

## 🆘 Troubleshooting

### Build Error: "config not found"
**Solution**: Already fixed! Build context is now parent directory.

### Build Error: "requirements.txt not found"
**Check**: Make sure you're in `exercise_11/` directory when running `docker compose up`

### Slow Build:
**Normal**: First build takes 2-5 minutes  
**Next time**: Uses cache, much faster

### Port Already in Use:
```bash
# Stop existing services
docker compose down

# Or stop non-Docker servers
# Then start Docker
docker compose up
```

### OpenAI API Key Not Found:
```bash
# Check .env exists in exercise_11/
cat .env

# Should show:
# OPENAI_API_KEY=sk-...
```

---

## ⏱️ Expected Timing

| Step | Time | Total |
|------|------|-------|
| Build images (first time) | 2-5 min | 2-5 min |
| Start containers | 5s | - |
| Backend healthy | 10s | 15s |
| Frontend healthy | 5s | 20s |

**Demo startup**: ✅ <20 seconds (using cached images)

---

## 🎯 Success Criteria

✅ `docker compose up` completes without errors  
✅ Backend healthy in <15 seconds  
✅ Frontend healthy in <20 seconds  
✅ `/healthz` returns 200  
✅ `/readyz` returns ready:true  
✅ Chat interface works  
✅ Cost tracking visible in logs  

---

## 💡 Quick Commands

```bash
# Start in background
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down

# Rebuild (if you change code)
docker compose up --build

# Clean everything
docker compose down -v
```

---

## 🎬 Demo Tip

**Don't build during demo!** Use cached images:

1. **Before demo**: Run `docker compose up` once to build images
2. **Stop**: `docker compose down`
3. **During demo**: `docker compose up` (uses cache, fast!)

This way startup is <20s, not 5 minutes! ⚡

---

*Test this tomorrow morning - should work perfectly now!* ✅

