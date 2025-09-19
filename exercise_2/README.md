# Exercise 2 — Chat App: Next.js + FastAPI (OpenAI proxy)

This exercise provides:
- a Python FastAPI backend that proxies `/chat` to OpenAI Chat Completions
- a minimal Next.js frontend that calls the backend and renders a chat UI

## Folder structure
- `backend/`: FastAPI app (`/chat`, `/health`)
- `frontend/`: Next.js app with a simple chat interface

## Backend setup

1) Configure env:
```bash
cd backend
cp .env.example .env
```

On Windows:
```cmd
cd backend
copy .env.example .env
```

2) Edit the `.env` file and replace `your_actual_api_key_here` with your actual OpenAI API key:
   - Get your API key from: https://platform.openai.com/api-keys
   - Open the `.env` file in a text editor
   - Replace `your_actual_api_key_here` with your actual API key
   - Save the file

3) Run the server:
```bash
# Using the provided scripts (recommended)
bash run.sh
# Server starts on http://localhost:8000
```

On Windows:
```cmd
# In Command Prompt
run.bat
# Or in PowerShell
.\run.bat
# Server starts on http://localhost:8000
```

Alternative method (if you have uvicorn installed):
```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Health check:
```bash
curl http://localhost:8000/health
```

## Frontend setup

1) Set backend base URL:
```bash
cd frontend
echo "NEXT_PUBLIC_BACKEND_BASE=http://localhost:8000" > .env.local
```

2) Install dependencies and start dev server:
```bash
npm install
npm run dev
```

Open: http://localhost:3000

## Notes
- CORS defaults to `http://localhost:3000` and `http://localhost:4000`, configure more via `CORS_ORIGINS` in backend `.env`.
- The backend is a thin wrapper; the frontend never uses OpenAI directly.
- Update the model or temperature in the frontend call if desired.
- If you encounter "Python was not found" errors when running run.bat, try using the uvicorn command directly or ensure Python is properly installed.