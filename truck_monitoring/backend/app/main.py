"""
Main FastAPI Application for Truck Monitoring System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from .database import init_db
from .api import auth_routes, trucks, statistics, edge, media
from .seed_data import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events - startup and shutdown"""
    # Startup
    print("🚀 Starting Truck Monitoring System...")
    init_db()
    seed_database()
    print("✅ Server ready at http://localhost:8095")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="Truck Monitoring System",
    description="Backend portal for monitoring truck traffic with user authentication",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / "images").mkdir(exist_ok=True)
(UPLOAD_DIR / "videos").mkdir(exist_ok=True)
(UPLOAD_DIR / "thumbnails").mkdir(exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Include routers
app.include_router(auth_routes.router)
app.include_router(trucks.router)
app.include_router(statistics.router)
app.include_router(edge.router)  # Edge computer endpoints (no auth required)
app.include_router(media.router)  # Media upload endpoints (no auth required)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Truck Monitoring System API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "truck-monitoring"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8095,
        reload=True
    )




