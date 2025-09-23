"""
Exercise 6: RAG Chatbot - Main FastAPI Application
Comprehensive RAG system with knowledge base management
"""

import logging
import time
import os
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import application modules
from app.config import settings
from app.database import init_database, close_database
from app.api import knowledge_base, documents, qa_pairs, chat
from app.services.vector_store import init_chromadb, close_chromadb
from app.services.llm_service import init_llm_service
from app.utils.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting RAG Chatbot application...")
    
    try:
        # Initialize database
        logger.info("📊 Initializing database connection...")
        await init_database()
        
        # Initialize ChromaDB
        logger.info("🔍 Initializing ChromaDB vector store...")
        await init_chromadb()
        
        # Initialize LLM service
        logger.info("🤖 Initializing LLM service...")
        await init_llm_service()
        
        logger.info("✅ Application startup completed successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        raise
    finally:
        # Cleanup on shutdown
        logger.info("🛑 Shutting down application...")
        await close_chromadb()
        await close_database()
        logger.info("✅ Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="Exercise 6: RAG Chatbot",
    description="""
    A comprehensive RAG (Retrieval-Augmented Generation) chatbot system that demonstrates:
    
    - **Knowledge Base Management**: Upload and manage documents and Q&A pairs
    - **Document Processing**: PDF, text, and document parsing with chunking
    - **Vector Search**: Semantic similarity search using ChromaDB
    - **RAG Pipeline**: Retrieval-augmented generation with LLM integration
    - **Chat Interface**: Real-time chat with source attribution
    - **Admin Console**: Full management interface for knowledge bases
    
    Built with FastAPI, PostgreSQL + pgvector, ChromaDB, and modern LLMs.
    """,
    version=settings.app_version,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted host middleware (for production)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )

# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource '{request.url.path}' was not found",
            "path": request.url.path,
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "path": request.url.path,
        }
    )

# =============================================================================
# MIDDLEWARE FOR REQUEST LOGGING
# =============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log request details
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rag-chatbot",
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check with service dependencies"""
    from app.database import get_database_health
    from app.services.vector_store import get_chromadb_health
    from app.services.llm_service import get_llm_health
    
    health_status = {
        "status": "healthy",
        "service": "rag-chatbot",
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {}
    }
    
    try:
        # Check database
        db_health = await get_database_health()
        health_status["dependencies"]["database"] = db_health
        
        # Check ChromaDB
        chromadb_health = await get_chromadb_health()
        health_status["dependencies"]["chromadb"] = chromadb_health
        
        # Check LLM service
        llm_health = await get_llm_health()
        health_status["dependencies"]["llm"] = llm_health
        
        # Determine overall status
        all_healthy = all(
            dep.get("status") == "healthy" 
            for dep in health_status["dependencies"].values()
        )
        
        if not all_healthy:
            health_status["status"] = "degraded"
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
    
    return health_status

# =============================================================================
# API ROUTES
# =============================================================================

# Include API routers
app.include_router(
    knowledge_base.router,
    prefix="/api/v1/knowledge-bases",
    tags=["Knowledge Bases"]
)

app.include_router(
    documents.router,
    prefix="/api/v1/documents",
    tags=["Documents"]
)

app.include_router(
    qa_pairs.router,
    prefix="/api/v1/qa-pairs",
    tags=["Q&A Pairs"]
)

app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["Chat"]
)

# =============================================================================
# STATIC FILES (for uploaded files)
# =============================================================================

# Mount uploads directory for serving files
if os.path.exists(settings.upload_directory):
    app.mount(
        "/uploads",
        StaticFiles(directory=settings.upload_directory),
        name="uploads"
    )

# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Exercise 6: RAG Chatbot API",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs_url": "/docs" if not settings.is_production else None,
        "health_url": "/health",
        "api_prefix": "/api/v1",
        "features": [
            "Knowledge Base Management",
            "Document Processing & Upload",
            "Q&A Pair Management",
            "Vector Similarity Search",
            "RAG Pipeline",
            "Real-time Chat",
            "Source Attribution",
        ],
        "endpoints": {
            "knowledge_bases": "/api/v1/knowledge-bases",
            "documents": "/api/v1/documents",
            "qa_pairs": "/api/v1/qa-pairs",
            "chat": "/api/v1/chat",
        }
    }

# =============================================================================
# WEBSOCKET ENDPOINT (for real-time chat)
# =============================================================================

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    from app.api.chat import handle_websocket_chat
    await handle_websocket_chat(websocket, session_id)

# =============================================================================
# METRICS ENDPOINT (optional)
# =============================================================================

if settings.enable_metrics:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

# =============================================================================
# DEVELOPMENT UTILITIES
# =============================================================================

if settings.is_development:
    
    @app.get("/dev/info", tags=["Development"])
    async def development_info():
        """Development information endpoint"""
        return {
            "settings": {
                "database_url": settings.database_url.replace(
                    settings.database_url.split('@')[0].split('//')[1], 
                    "***:***"
                ),
                "chromadb_url": settings.chromadb_url,
                "embedding_model": settings.embedding_model,
                "chunk_size": settings.chunk_size,
                "max_file_size_mb": settings.max_file_size_mb,
            },
            "directories": {
                "uploads": settings.upload_directory,
                "temp": settings.temp_directory,
            },
            "llm_config": {
                "openai_available": bool(settings.openai_api_key),
                "anthropic_available": bool(settings.anthropic_api_key),
                "use_openai_embeddings": settings.use_openai_embeddings,
            }
        }

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
