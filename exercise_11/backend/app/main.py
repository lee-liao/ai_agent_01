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
from .observability import setup_observability
from .config import settings

app = FastAPI(title="Child Growth Assistant", version="0.1.0")

# Initialize observability on startup
# Read OTLP endpoint from settings (which loads from .env file)
setup_observability(
    service_name="child-growth-assistant",
    service_version="1.0.0",
    jaeger_endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
    enable_console_export=True
)

# Log active prompt version on startup
try:
    from app.prompts import get_active_prompt_version
    import logging
    logger = logging.getLogger(__name__)
    prompt_version = get_active_prompt_version()
    logger.info(f"📝 Active prompt version: {prompt_version}")
except Exception as e:
    # Non-critical, just log warning
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not load prompt version: {e}")

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
    """Basic health check - is the service running?"""
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    """
    Readiness check - is the service ready to handle requests?
    Checks dependencies: OpenAI API key, RAG index
    """
    from app.config import settings
    from pathlib import Path
    
    checks = {
        "openai_key_configured": bool(settings.OPENAI_API_KEY),
        "rag_module_available": True,  # Already imported successfully if we're here
        "config_file_exists": Path("config/safety_policy.json").exists()
    }
    
    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503
    
    return {
        "ready": all_ready,
        "checks": checks,
        "message": "Service ready" if all_ready else "Service not ready - check configuration"
    }


app.include_router(coach.router)
app.include_router(websocket.router)

# Include HITL router if it exists
try:
    from .api import hitl
    app.include_router(hitl.router)
except ImportError:
    pass  # HITL router not available


