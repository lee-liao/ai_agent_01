from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import calls, websocket

# Create FastAPI app
app = FastAPI(
    title="AI Call Center Assistant",
    version="1.0.0",
    description="Real-Time AI Call Center Assistant API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "https://localhost:8501",
        "http://192.168.10.210:8501",
        "https://192.168.10.210:8501",
        "http://192.168.10.244:8501",
        "https://192.168.10.244:8501",
        "http://103.98.213.149:8501",
        "https://103.98.213.149:8501"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (without database-dependent routes for now)
app.include_router(calls.router)
app.include_router(websocket.router)

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
        "app.main_simple:app",
        host="0.0.0.0",
        port=8600,
        reload=True
    )

