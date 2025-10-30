from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from .config import settings
from .database import init_db, close_db
from .api import auth_routes, customers, websocket, calls, queue_debug

# Import transcription test routes
from .api import transcription_test

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting AI Call Center Assistant...")
    await init_db()
    print("Database initialized")
    yield
    # Shutdown
    print("Shutting down...")
    await close_db()
    print("Database connections closed")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Real-Time AI Call Center Assistant API",
    lifespan=lifespan
)

# Serve transcription test HTML file
@app.get("/transcription_test")
async def serve_transcription_test():
    """Serve the transcription test HTML file"""
    html_file_path = os.path.join(os.path.dirname(__file__), "transcription_test.html")
    if os.path.exists(html_file_path):
        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return Response(content=html_content, media_type="text/html")
    else:
        return Response(content="<h1>Transcription Test Page Not Found</h1>", media_type="text/html", status_code=404)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(customers.router)
app.include_router(calls.router)
app.include_router(queue_debug.router)
app.include_router(websocket.router)
app.include_router(transcription_test.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Call Center Assistant API",
        "version": "1.0.0",
        "status": "running"
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8600,
        reload=True
    )

