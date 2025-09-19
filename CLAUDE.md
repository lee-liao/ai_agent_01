# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This repository contains AI training exercises organized in separate folders:

- **exercise_1/**: CLI-based stock screening agent using Python, Alpha Vantage API, and OpenAI
- **exercise_2/**: Full-stack chat application with Next.js frontend and FastAPI backend

## Exercise 1: Stock Screener Agent

### Architecture
- Python CLI application that fetches stock data from Alpha Vantage
- Uses OpenAI API to generate BUY/SELL recommendations
- Supports both one-time execution and interactive mode

### Common Commands
```bash
# Setup (installs dependencies and creates virtual environment)
cd exercise_1 && bash setup.sh

# Quick run (uses existing venv or system python)
cd exercise_1 && bash run.sh

# Manual run
cd exercise_1 && python hello_agent.py

# Interactive mode
cd exercise_1 && python hello_agent.py --interactive
```

### Key Configuration
- Environment variables: `ALPHA_VANTAGE_KEY`, `OPENAI_API_KEY`, `STOCK_SYMBOLS`
- Virtual environment: `.venv/`
- Configuration file: `.env` (copy from `.env.example`)

### Architecture Notes
- Main module: `hello_agent.py`
- Dependencies: `requests`, `openai`, `python-dotenv`
- Interactive mode supports commands like `add`, `remove`, `price`, `history`, `screen`, `ask`

## Exercise 2: Chat Application

### Architecture
- **Backend**: FastAPI server that proxies requests to OpenAI Chat Completions API
- **Frontend**: Next.js application with React-based chat interface
- Communication: Frontend → Backend → OpenAI API

### Backend Commands
```bash
# Setup and run (auto-creates venv, installs deps, starts server)
cd exercise_2/backend && bash run.sh

# Manual run (requires uvicorn)
cd exercise_2/backend && uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Health check
curl http://localhost:8000/health
```

### Frontend Commands
```bash
# Setup and run
cd exercise_2/frontend
pnpm install
pnpm run dev

# Build for production
pnpm run build
pnpm start
```

### Key Configuration
- Backend: `OPENAI_API_KEY` in `.env`, `CORS_ORIGINS` for CORS configuration
- Frontend: `NEXT_PUBLIC_BACKEND_BASE` (defaults to http://localhost:8000)
- Default ports: Backend 8000, Frontend 3000

### Architecture Notes
- Backend endpoints: `/chat` (POST), `/health` (GET)
- Frontend is a single-page application in `app/page.tsx`
- Backend validates request models and handles OpenAI API communication
- CORS is configured to allow localhost development

## Development Environment Setup

### Exercise 1 Dependencies
- Python 3.10+ with virtual environment
- Alpha Vantage API key (free tier available)
- OpenAI API key

### Exercise 2 Dependencies
- Python 3.11+ for backend (FastAPI, uvicorn, openai, python-dotenv)
- Node.js and npm for frontend (Next.js, React, TypeScript)
- OpenAI API key

## File Structure Patterns

- Each exercise has its own `README.md` with detailed setup instructions
- Configuration files follow `.env.example` → `.env` pattern
- Shell scripts (`run.sh`, `setup.sh`) handle common operations
- Virtual environments are stored in `.venv/` directories
- Frontend uses standard Next.js App Router structure

## Important Notes

- The backend run scripts include sophisticated Python version detection to avoid system Python issues
- Exercise 1 has rate limiting considerations for Alpha Vantage free tier
- Exercise 2 backend is designed as a proxy - frontend never directly calls OpenAI
- Both exercises require proper API key configuration in environment variables