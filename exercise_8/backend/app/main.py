"""
Main FastAPI Application with Multi-Agent Framework

This version uses the Agent/Team/Coordinator framework for orchestration.
Integrates the new multi-agent framework with existing exercise 8 functionality.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import time
import json
import redis
import os

# Import the reusable components
from contextlib import asynccontextmanager
from app.config import settings, get_settings
from app.utils import setup_app_logging

# Import our multi-agent framework
from app.agents import Agent, Team, Coordinator
from app.agents.agent import ParserAgent, RiskAnalyzerAgent, RedlineGeneratorAgent
from app.agents.team import TeamPattern

# Import existing functionality to maintain compatibility
from app.utils.analysis import analyze_risk_with_openai, parse_document_content
from app.export import export_redline_document
from app.metrics import get_slo_metrics, get_run_metrics, get_run_costs, get_run_quality_indicators
from app.agents.base import Blackboard

# Import agent modules - keeping old imports for compatibility while adding new framework
from app.agents.base import Blackboard
from app.agents.manager_worker import manager_worker_workflow
from app.agents.planner_executor import planner_executor_workflow
from app.agents.reviewer_referee import reviewer_referee_workflow
from app.agents.redline_generator import generate_redlines_for_run

# Import new framework implementations
from app.agents.manager_worker_new import manager_worker_workflow as manager_worker_framework
from app.agents.planner_executor_new import planner_executor_workflow as planner_executor_framework
from app.agents.reviewer_referee_new import reviewer_referee_workflow as reviewer_referee_framework

# Import new reviewer/referee agents
from app.agents.reviewer_referee_agents import ReviewerAgent, RefereeAgent

# Make database import optional since we're primarily using Redis
try:
    from app.database import init_database, close_database
except ImportError as e:
    print(f"Database modules not available: {e}")
    # Define dummy functions for when database is not available
    async def init_database():
        print("Database initialization skipped (not available)")
        pass
    
    async def close_database():
        print("Database close skipped (not available)")
        pass


# Global variable to hold Redis client (but initialize lazily)
_redis_client = None

def get_redis_client():
    """Function to get Redis client, creating it lazily to avoid multiprocessing issues"""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", settings.redis_url)
        try:
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test the connection
            _redis_client.ping()
        except Exception as e:
            print(f"Redis connection error: {e}")
            # Fallback to default URL if the configured URL doesn't work
            _redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
    return _redis_client


def get_from_redis(key: str) -> Dict[str, Any]:
    """Helper function to get data from Redis"""
    try:
        redis_client = get_redis_client()
        data = redis_client.get(key)
        return json.loads(data) if data else {}
    except Exception as e:
        print(f"Redis get error for key {key}: {e}")
        return {}

def set_to_redis(key: str, data: Dict[str, Any]) -> None:
    """Helper function to set data to Redis"""
    try:
        redis_client = get_redis_client()
        redis_client.set(key, json.dumps(data))
    except Exception as e:
        print(f"Redis set error for key {key}: {e}")

def get_all_docs() -> Dict[str, Any]:
    """Helper function to get all documents from Redis using pattern matching"""
    try:
        redis_client = get_redis_client()
        # Get all keys matching "doc:*"
        doc_keys = redis_client.keys("doc:*")
        docs = {}
        for key in doc_keys:
            doc_id = key.split(":")[1]  # Extract ID from "doc:{id}"
            docs[doc_id] = get_from_redis(key)
        return docs
    except Exception as e:
        print(f"Error getting all docs: {e}")
        return {}

def get_all_playbooks() -> Dict[str, Any]:
    """Helper function to get all playbooks from Redis using pattern matching"""
    try:
        redis_client = get_redis_client()
        # Get all keys matching "playbook:*"
        pb_keys = redis_client.keys("playbook:*")
        playbooks = {}
        for key in pb_keys:
            pb_id = key.split(":")[1]  # Extract ID from "playbook:{id}"
            playbooks[pb_id] = get_from_redis(key)
        return playbooks
    except Exception as e:
        print(f"Error getting all playbooks: {e}")
        return {}

def get_all_runs() -> Dict[str, Any]:
    """Helper function to get all runs from Redis using pattern matching"""
    try:
        redis_client = get_redis_client()
        # Get all keys matching "run:*"
        run_keys = redis_client.keys("run:*")
        runs = {}
        for key in run_keys:
            run_id = key.split(":")[1]  # Extract ID from "run:{id}"
            runs[run_id] = get_from_redis(key)
        return runs
    except Exception as e:
        print(f"Error getting all runs: {e}")
        return {}

def get_doc(doc_id: str) -> Dict[str, Any]:
    """Helper function to get a specific document from Redis"""
    return get_from_redis(f"doc:{doc_id}")

def set_doc(doc_id: str, data: Dict[str, Any]) -> None:
    """Helper function to set a specific document in Redis"""
    set_to_redis(f"doc:{doc_id}", data)

def get_playbook(playbook_id: str) -> Dict[str, Any]:
    """Helper function to get a specific playbook from Redis"""
    return get_from_redis(f"playbook:{playbook_id}")

def set_playbook(playbook_id: str, data: Dict[str, Any]) -> None:
    """Helper function to set a specific playbook in Redis"""
    set_to_redis(f"playbook:{playbook_id}", data)

def get_run(run_id: str) -> Dict[str, Any]:
    """Helper function to get a specific run from Redis"""
    return get_from_redis(f"run:{run_id}")

def set_run(run_id: str, data: Dict[str, Any]) -> None:
    """Helper function to set a specific run in Redis"""
    set_to_redis(f"run:{run_id}", data)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    print("🚀 Starting up application...")
    
    # Setup logging
    logger = setup_app_logging(
        level=settings.log_level,
        log_file=f"./logs/app_{uuid.uuid4().hex[:8]}.log" if settings.is_development else None
    )
    
    # Initialize database if needed
    try:
        await init_database()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Continue without database since we're using Redis for now
    
    yield
    
    # Shutdown
    print("🛑 Shutting down application...")
    try:
        await close_database()
    except Exception as e:
        print(f"Error during shutdown: {e}")


# Initialize the FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Configure CORS based on settings
cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Allow credentials if not using wildcard origins
    allow_origin_regex=None
)

# Initialize the Coordinator (manages all agents and blackboard)
coordinator = Coordinator()

# In the startup event, we'll initialize our teams
@app.on_event("startup")
async def setup_teams():
    """
    Initialize demo teams for the multi-agent framework.
    """
    print("🚀 Initializing multi-agent framework...")
    
    # Sequential Team: Parser -> Risk Analyzer -> Redline Generator
    sequential_team = Team(
        name="sequential_team",
        pattern=TeamPattern.SEQUENTIAL,
        description="Sequential execution: parse, assess, redline"
    )
    sequential_team.add_agent(ParserAgent())
    sequential_team.add_agent(RiskAnalyzerAgent())
    sequential_team.add_agent(RedlineGeneratorAgent())
    coordinator.register_team(sequential_team)
    
    # Manager-Worker Team
    manager_worker_team = Team(
        name="manager_worker_team",
        pattern=TeamPattern.MANAGER_WORKER,
        description="Manager decomposes work, workers execute in parallel"
    )
    # For now, using the same structure (students should implement proper manager/workers)
    manager_worker_team.add_agent(ParserAgent())
    manager_worker_team.add_agent(RiskAnalyzerAgent())
    manager_worker_team.add_agent(RedlineGeneratorAgent())
    coordinator.register_team(manager_worker_team)
    
    # Pipeline Team
    pipeline_team = Team(
        name="planner_executor_team",
        pattern=TeamPattern.PIPELINE,
        description="Pipeline execution with data passing between agents"
    )
    pipeline_team.add_agent(ParserAgent())
    pipeline_team.add_agent(RiskAnalyzerAgent())
    pipeline_team.add_agent(RedlineGeneratorAgent())
    coordinator.register_team(pipeline_team)
    
    # Reviewer-Referee Team
    reviewer_referee_team = Team(
        name="reviewer_referee_team",
        pattern=TeamPattern.SEQUENTIAL,  # Reviewer first, then Referee if needed
        description="Reviewer checks against checklist, Referee arbitrates contested decisions"
    )
    reviewer_referee_team.add_agent(ReviewerAgent())
    reviewer_referee_team.add_agent(RefereeAgent())
    coordinator.register_team(reviewer_referee_team)
    
    print("✅ Demo teams initialized successfully")
    print(f"📊 Coordinator stats: {coordinator.get_stats()}")


# ==================== Pydantic Models ====================

class RunRequest(BaseModel):
    doc_id: str
    agent_path: str = "sequential"  # sequential | manager_worker | planner_executor
    playbook_id: Optional[str] = None
    scope: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class RiskApprovalItem(BaseModel):
    clause_id: str
    risk_override: Optional[str] = None
    comments: Optional[str] = None

class RiskApprovalRequest(BaseModel):
    run_id: str
    items: List[RiskApprovalItem]

class FinalApproveRequest(BaseModel):
    run_id: str
    note: Optional[str] = None


# ==================== Health Check ====================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "coordinator_stats": coordinator.get_stats()
    }


@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check including external dependencies"""
    start_time = time.time()
    
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": time.time(),
        "checks": {
            "redis": {"status": "unknown", "response_time_ms": 0},
            "database": {"status": "unknown", "response_time_ms": 0},
            "disk_space": {"status": "unknown", "available_bytes": 0}
        }
    }
    
    # Check Redis
    try:
        redis_start = time.time()
        redis_client = get_redis_client()
        redis_client.ping()
        redis_duration = (time.time() - redis_start) * 1000
        health_status["checks"]["redis"] = {"status": "healthy", "response_time_ms": round(redis_duration, 2)}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "error", "error": str(e), "response_time_ms": 0}
        health_status["status"] = "degraded"
    
    # Check disk space
    import shutil
    try:
        total, used, free = shutil.disk_usage(".")
        health_status["checks"]["disk_space"] = {"status": "healthy", "available_bytes": free}
    except Exception as e:
        health_status["checks"]["disk_space"] = {"status": "error", "error": str(e), "available_bytes": 0}
        health_status["status"] = "degraded"
    
    overall_duration = (time.time() - start_time) * 1000
    health_status["response_time_ms"] = round(overall_duration, 2)
    
    return health_status


# ==================== Document Management ====================

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file content"""
    import PyPDF2
    from io import BytesIO
    
    pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file content"""
    from docx import Document
    from io import BytesIO
    
    doc = Document(BytesIO(file_content))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

@app.post("/api/docs/upload")
async def upload_doc(file: UploadFile = File(...)):
    import os
    _, ext = os.path.splitext(file.filename.lower())
    
    # Read file content based on type
    file_content = await file.read()
    
    if ext == '.pdf':
        try:
            content = extract_text_from_pdf(file_content)
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            content = file_content.decode("utf-8", errors="ignore")
    elif ext in ['.docx']:
        try:
            content = extract_text_from_docx(file_content)
        except Exception as e:
            print(f"Error extracting DOCX: {e}")
            content = file_content.decode("utf-8", errors="ignore")
    elif ext in ['.txt', '.md']:
        content = file_content.decode("utf-8", errors="ignore")
    else:
        # For unknown types, try to decode as text
        content = file_content.decode("utf-8", errors="ignore")
    
    doc_id = str(uuid.uuid4())
    
    # Parse document content into structured clauses
    doc_data = parse_document_content(content, file.filename)
    
    # Store document in Redis with individual key
    print(f"Storing document with ID: {doc_id}")
    print(f"Key will be: doc:{doc_id}")
    set_doc(doc_id, doc_data)
    
    # Verify it was stored
    stored_data = get_doc(doc_id)
    print(f"Retrieved data for {doc_id}: {stored_data}")
    
    return {"doc_id": doc_id, "name": file.filename}


@app.get("/api/docs")
async def list_docs():
    docs = get_all_docs()
    return [{"doc_id": k, "name": v.get("name")} for k, v in docs.items()]


@app.get("/api/docs/{doc_id}")
async def get_doc_by_id(doc_id: str):
    doc = get_doc(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="doc not found")
    return doc


# ==================== Playbook Management ====================

class PlaybookCreate(BaseModel):
    name: str
    rules: Dict[str, Any]

@app.post("/api/playbooks")
async def create_playbook(pb: PlaybookCreate):
    pb_id = str(uuid.uuid4())
    playbook_data = {"name": pb.name, "rules": pb.rules}
    
    # Store playbook in Redis with individual key
    set_playbook(pb_id, playbook_data)
    
    return {"playbook_id": pb_id}


@app.get("/api/playbooks")
async def list_playbooks():
    playbooks = get_all_playbooks()
    return [{"playbook_id": k, "name": v.get("name")} for k, v in playbooks.items()]


@app.get("/api/playbooks/{playbook_id}")
async def get_playbook_by_id(playbook_id: str):
    pb = get_playbook(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="playbook not found")
    return pb


@app.delete("/api/playbooks/{playbook_id}")
async def delete_playbook(playbook_id: str):
    # Delete the specific playbook
    redis_client = get_redis_client()
    redis_client.delete(f"playbook:{playbook_id}")
    return {"status": "deleted"}


# ==================== Run Orchestration using new Framework ====================

@app.post("/api/run")
async def start_run(req: RunRequest):
    """
    Start a new document review run using the multi-agent framework.
    Integrates the new coordinator framework with existing functionality.
    """
    # Validate document
    if req.doc_id not in get_all_docs():
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = get_doc(req.doc_id)
    
    # Get policy rules from playbook
    policy_rules = {}
    if req.playbook_id and req.playbook_id in get_all_playbooks():
        policy_rules = get_playbook(req.playbook_id)["rules"]
    
    # Start run using coordinator
    try:
        # Use the coordinator's start_run method
        run_id = coordinator.start_run(
            doc_id=req.doc_id,
            document_text=doc.get("content", ""),
            agent_path=req.agent_path,
            playbook_id=req.playbook_id,
            policy_rules=policy_rules
        )
        
        return {
            "run_id": run_id,
            "doc_id": req.doc_id,
            "agent_path": req.agent_path,
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/run/{run_id}")
async def get_run_by_id(run_id: str):
    """
    Get run details including blackboard state.
    """
    run = coordinator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    blackboard = coordinator.get_blackboard(run_id)
    
    # Calculate score based on risk assessments
    assessments = blackboard.get("assessments", [])
    high_count = sum(1 for a in assessments if a.get("risk_level", "").lower() == "high")
    medium_count = sum(1 for a in assessments if a.get("risk_level", "").lower() == "medium")
    
    # Basic scoring: start with 1.0 and subtract penalties
    score_value = 1.0 - (high_count * 0.3) - (medium_count * 0.1)
    score_value = max(0.0, min(1.0, score_value))  # Keep between 0 and 1
    final_score = score_value * 100  # Convert to percentage
    
    return {
        **run,
        "history": blackboard.get("history", []),
        "assessments": blackboard.get("assessments", []),
        "proposals": blackboard.get("proposals", []),
        "score": final_score
    }


@app.get("/api/runs")
async def list_runs():
    """List all runs"""
    return coordinator.list_runs()


@app.get("/api/blackboard/{run_id}")
async def get_blackboard(run_id: str):
    """
    Get the blackboard (shared memory) for a run.
    """
    blackboard = coordinator.get_blackboard(run_id)
    if not blackboard:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return blackboard


# ==================== HITL Gates ====================

@app.post("/api/hitl/risk-approve")
async def risk_approve(body: RiskApprovalRequest):
    """
    Risk Gate: Human approval for high-risk clauses.
    Uses the coordinator's approval mechanism.
    """
    # Prepare approval data
    approved_clauses = []
    rejected_clauses = []
    comments = {}
    
    for item in body.items:
        # Determine approval based on risk override or other logic
        if item.risk_override is not None:
            # If risk override exists, use that to determine approval
            if item.risk_override.lower() in ["low", "medium"]:
                approved_clauses.append(item.clause_id)
            else:
                rejected_clauses.append(item.clause_id)
        else:
            # Default to approve
            approved_clauses.append(item.clause_id)
        
        if item.comments:
            comments[item.clause_id] = item.comments
    
    success = coordinator.approve_risk(
        run_id=body.run_id,
        approved_clauses=approved_clauses,
        rejected_clauses=rejected_clauses,
        comments=comments
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {"status": "approved", "run_id": body.run_id}


@app.post("/api/hitl/final-approve")
async def final_approve(body: FinalApproveRequest):
    """
    Final Gate: Human approval for all redline proposals.
    Uses the coordinator's final approval mechanism.
    """
    # For now, we'll approve all proposals
    blackboard = coordinator.get_blackboard(body.run_id)
    if not blackboard:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get all proposal IDs
    proposal_ids = [p["clause_id"] for p in blackboard.get("proposals", [])]
    
    success = coordinator.approve_final(
        run_id=body.run_id,
        approved_proposals=proposal_ids,
        rejected_proposals=[],
        notes=body.note
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {"status": "approved", "run_id": body.run_id}


# ==================== Export ====================

@app.post("/api/export/redline")
async def export_redline(run_id: str, format: str = "md"):
    """
    Export redlined document.
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    try:
        export_content = await export_redline_document(run, format)
    except ImportError as e:
        raise HTTPException(status_code=400, detail=f"Export format '{format}' not available: {str(e)}")
    
    # Store the exported content in artifacts
    artifact_key = f"redline.{format}"
    
    run.setdefault("artifacts", {})[artifact_key] = {
        "content_type": f"application/{format}",
        "size": len(export_content),
        "generated_at": time.time()
    }
    
    # Update the run in Redis
    set_run(run_id, run)
    
    return {
        "artifact_key": artifact_key,
        "content_type": f"application/{format}",
        "size": len(export_content),
        "download_url": f"/api/export/download/{run_id}/{format}"
    }


@app.get("/api/export/download/{run_id}/{format}")
async def download_export(run_id: str, format: str):
    """Download the exported document"""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    try:
        export_content = await export_redline_document(run, format)
    except ImportError as e:
        raise HTTPException(status_code=400, detail=f"Export format '{format}' not available: {str(e)}")
    
    # Set appropriate content type
    content_type_map = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf", 
        "md": "text/markdown"
    }
    content_type = content_type_map.get(format, "application/octet-stream")
    
    from fastapi.responses import Response
    return Response(
        content=export_content,
        headers={
            "Content-Disposition": f"attachment; filename=redline-{run_id}.{format}",
        },
        media_type=content_type
    )


# ==================== Reports & Metrics ====================

@app.get("/api/report/slos")
async def report_slos():
    return get_slo_metrics()


@app.get("/api/report/performance")
async def report_performance():
    """Get performance metrics"""
    # For this implementation, we'll return example data
    # In a real implementation, this would aggregate data from multiple runs
    return {
        "p50_ms": 1200,
        "p95_ms": 3200,
        "p99_ms": 5800,
        "avg_processing_time": 2.5,  # seconds
        "requests_per_minute": 15.7,
        "active_runs": 5
    }


@app.get("/api/report/quality")
async def report_quality():
    """Get quality metrics"""
    return {
        "pass_rate": 0.89,
        "precision": 0.85,
        "recall": 0.78,
        "f1_score": 0.81,
        "mitigation_rate": 0.82
    }


@app.get("/api/report/cost")
async def report_cost():
    """Get cost metrics"""
    # This would aggregate cost data from multiple runs in a real implementation
    return {
        "total_cost_usd": 0.0,
        "cost_per_run_avg": 0.0015,
        "cost_current_period": 0.0,
        "budget_remaining": 100.0  # example budget
    }


# ==================== Replay & Debug ====================

@app.get("/api/replay/{run_id}")
async def replay(run_id: str):
    """
    Replay a run from the beginning with the same parameters
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Create a new run based on the original
    new_id = str(uuid.uuid4())

    # Get original parameters
    doc_id = run.get("doc_id")
    agent_path = run.get("agent_path", "manager_worker")
    playbook_id = run.get("playbook_id")

    # Get the document with parsed clauses
    docs = get_all_docs()
    doc_data = get_doc(doc_id) if doc_id in docs else None

    if doc_data and "clauses" in doc_data:
        clauses = doc_data["clauses"]
    else:
        clauses = [
            {"id": "c1", "heading": "Confidential Information", "text": "The parties agree to keep information secret."},
            {"id": "c2", "heading": "Term", "text": "Two (2) years from Effective Date."},
            {"id": "c3", "heading": "Liability", "text": "Liability capped at 12 months of fees."},
        ]

    # Get playbook if specified
    playbook = None
    if playbook_id:
        playbook = get_playbook(playbook_id)

    # Create a blackboard for this replay run
    blackboard = Blackboard(
        run_id=new_id,
        clauses=clauses,
        assessments=[],  
        proposals=[],    
        decisions=[],
        artifacts={},
        history=[
            {"step": "init", "agent": "system", "status": "started", "timestamp": time.time()}
        ],
        checkpoints={},
        metadata={"doc_id": doc_id, "playbook_id": playbook_id, "replayed_from": run_id}
    )

    async def execute_agent_workflow(agent_path: str, blackboard: Blackboard, playbook: Dict[str, Any] = None):
        """Execute the appropriate agent workflow based on the agent path"""
        if agent_path == "manager_worker":
            return await manager_worker_workflow(blackboard)
        elif agent_path == "planner_executor":
            return await planner_executor_workflow(blackboard)
        elif agent_path == "reviewer_referee":
            return await reviewer_referee_workflow(blackboard)
        else:
            # Default to manager-worker if unknown path
            return await manager_worker_workflow(blackboard)

    # Execute the same agent workflow that was used in the original run
    workflow_result = await execute_agent_workflow(agent_path, blackboard, playbook)

    # Calculate score based on risk assessments in the blackboard
    assessments = blackboard.assessments
    high_count = sum(1 for a in assessments if a.get("risk_level", "").lower() == "high")
    medium_count = sum(1 for a in assessments if a.get("risk_level", "").lower() == "medium")

    # Basic scoring: start with 1.0 and subtract penalties
    score_value = 1.0 - (high_count * 0.3) - (medium_count * 0.1)
    score_value = max(0.0, min(1.0, score_value))  # Keep between 0 and 1
    final_score = score_value * 100  # Convert to percentage

    # Create run data from blackboard
    new_run_data = {
        "doc_id": doc_id,
        "agent_path": agent_path,
        "playbook_id": playbook_id,
        "clauses": blackboard.clauses,
        "assessments": blackboard.assessments,
        "proposals": blackboard.proposals,
        "decisions": blackboard.decisions,
        "artifacts": blackboard.artifacts,
        "history": blackboard.history,
        "score": final_score,
        "replayed_from": run_id,
        "replay_timestamp": time.time()
    }

    # Store the new run in Redis with individual key
    set_run(new_id, new_run_data)

    return {"run_id": new_id, "workflow_result": workflow_result}


# ==================== Team Management (for debugging) ====================

@app.get("/api/teams")
async def list_teams():
    """List all registered teams"""
    return [
        team.get_info()
        for team in coordinator.teams.values()
    ]


@app.get("/api/teams/{team_name}")
async def get_team(team_name: str):
    """Get team details"""
    team = coordinator.get_team(team_name)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return team.get_info()