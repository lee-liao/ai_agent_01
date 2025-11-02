import sys
from pathlib import Path

# Add parent directory to path so 'rag' module can be found
backend_dir = Path(__file__).parent.parent
exercise11_dir = backend_dir.parent
if str(exercise11_dir) not in sys.path:
    sys.path.insert(0, str(exercise11_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import coach, websocket

app = FastAPI(title="Child Growth Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3080",
        "http://localhost:3081",
        "http://localhost:3082",
        "http://localhost:3083",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    # TODO: check RAG index and model key here later
    return {"ready": True}


app.include_router(coach.router)
app.include_router(websocket.router)


