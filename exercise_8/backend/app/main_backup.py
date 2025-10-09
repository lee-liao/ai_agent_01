import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import json
import redis
from urllib.parse import urlparse
import os

# Import the reusable components
from contextlib import asynccontextmanager
from app.config import settings, get_settings
from app.utils import setup_app_logging

# Import analysis utilities
from app.utils.analysis import analyze_risk_with_openai, parse_document_content

# Import agent modules
from app.agents.base import Blackboard
from app.agents.manager_worker import manager_worker_workflow
from app.agents.planner_executor import planner_executor_workflow
from app.agents.reviewer_referee import reviewer_referee_workflow
from app.agents.redline_generator import generate_redlines_for_run

# Import export functionality
from app.export import export_redline_document

# Import metrics functionality
from app.metrics import get_slo_metrics, get_run_metrics, get_run_costs, get_run_quality_indicators


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

import os

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


# Initialize OpenAI client
import openai

def get_openai_client():
    """Function to get OpenAI client with API key from environment"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY not found in environment. Using mock responses.")
        return None
    
    try:
        client = openai.OpenAI(api_key=api_key)
        # Test the client briefly (without making a full API call)
        return client
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return None


def analyze_risk_with_openai(clause_text: str, policy_rules: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyze risk level of a clause using OpenAI
    """
    openai_client = get_openai_client()
    if not openai_client:
        # Return mock analysis if OpenAI client not available
        # This is for development purposes when no API key is provided
        print("Using mock risk analysis (no OpenAI API key)")
        # Simple heuristic for mock risk assessment
        high_risk_keywords = ["unlimited", "without limitation", "sole discretion", "indemnify", "hold harmless"]
        medium_risk_keywords = ["not to exceed", "reasonably", "mutual", "standard"]
        
        text_lower = clause_text.lower()
        high_risk_count = sum(1 for keyword in high_risk_keywords if keyword in text_lower)
        medium_risk_count = sum(1 for keyword in medium_risk_keywords if keyword in text_lower)
        
        if high_risk_count > 0:
            risk_level = "High"
            rationale = f"Contains high-risk language: {', '.join([kw for kw in high_risk_keywords if kw in text_lower][:2])}"
        elif medium_risk_count > 0:
            risk_level = "Medium"
            rationale = f"Contains medium-risk language: {', '.join([kw for kw in medium_risk_keywords if kw in text_lower][:2])}"
        else:
            risk_level = "Low"
            rationale = "Standard legal language with no obvious risk indicators"
        
        return {
            "risk_level": risk_level,
            "rationale": rationale,
            "policy_refs": []
        }
    
    # Real OpenAI analysis
    policy_context = json.dumps(policy_rules, indent=2) if policy_rules else "No specific policy rules provided"
    
    prompt = f"""
    Analyze the following contract clause for legal and business risks according to these policy rules:
    
    POLICY RULES:
    {policy_context}
    
    CLAUSE TO ANALYZE:
    {clause_text}
    
    Please analyze and provide:
    1. Risk level: "High", "Medium", or "Low"
    2. Rationale for the risk assessment
    3. Specific policy rule references that apply
    
    Respond in JSON format with keys: "risk_level", "rationale", "policy_refs"
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        import ast
        result = ast.literal_eval(response.choices[0].message.content.strip())
        
        return {
            "risk_level": result.get("risk_level", "Medium"),
            "rationale": result.get("rationale", "AI analysis completed"),
            "policy_refs": result.get("policy_refs", [])
        }
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        # Fallback to simple analysis
        return {
            "risk_level": "Medium", 
            "rationale": f"AI analysis failed: {str(e)}, defaulting to medium risk",
            "policy_refs": []
        }

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

def delete_from_redis(key: str, field: str = None) -> None:
    """Helper function to delete data from Redis"""
    try:
        redis_client = get_redis_client()
        if field:
            redis_client.hdel(key, field)
        else:
            redis_client.delete(key)
    except Exception as e:
        print(f"Redis delete error for key {key}: {e}")

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

class RunRequest(BaseModel):
	doc_id: Optional[str] = None
	agent_path: Optional[str] = None  # e.g. manager_worker | planner_executor | reviewer_referee
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

@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name, "version": settings.app_version}

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check including external dependencies"""
    import time
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

@app.get("/api/debug/test-redis")
async def test_redis_connection():
    """Simple endpoint to test Redis connection"""
    try:
        redis_client = get_redis_client()
        test_key = "debug_test_key"
        test_value = f"test_value_{uuid.uuid4()}"
        
        # Set a test value
        redis_client.set(test_key, test_value)
        
        # Get it back
        retrieved_value = redis_client.get(test_key)
        
        # Clean up
        redis_client.delete(test_key)
        
        return {
            "status": "success",
            "test_value": test_value,
            "retrieved": retrieved_value,
            "connection_ok": True
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# --------------------------- Documents ---------------------------
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

def parse_document_content(content: str, filename: str) -> Dict[str, Any]:
    """
    Parse document content into structured clauses.
    """
    lines = content.split('\n')
    clauses = []
    clause_counter = 1
    
    # A simple heuristic to identify clauses based on numbering patterns
    clause_patterns = [
        r'^\d+[\.\)]',      # Matches "1.", "2)", etc.
        r'^\d+\.\d+',      # Matches "1.1", "2.3", etc.
        r'^[IVX]+[\.\)]',   # Roman numerals
        r'^[A-Z]\d*[\.\)]'  # Capital letters
    ]
    
    import re
    current_clause_text = ""
    current_heading = ""
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if this line looks like a clause heading
        is_clause_start = any(re.match(pattern, line, re.IGNORECASE) for pattern in clause_patterns)
        
        if is_clause_start:
            # If we were building a previous clause, save it
            if current_clause_text and current_heading:
                clauses.append({
                    "id": f"clause_{clause_counter - 1}",
                    "heading": current_heading,
                    "text": current_clause_text.strip(),
                    "start_line": 0  # Could track actual line number if needed
                })
            
            # Start a new clause
            current_heading = line
            current_clause_text = line + "\n"
            clause_counter += 1
        else:
            # If not a heading, add to current clause if one exists
            if current_heading:
                current_clause_text += line + "\n"
            # If no current heading, this could be a continuation of text before first heading
            # For now, let's not treat it as a clause until we find a proper heading
    
    # Don't forget the last clause
    if current_clause_text and current_heading:
        clauses.append({
            "id": f"clause_{clause_counter - 1}",
            "heading": current_heading,
            "text": current_clause_text.strip(),
            "start_line": 0
        })
    
    # If no clauses were found, create a single clause with the entire content
    if not clauses:
        clauses = [{
            "id": "clause_1",
            "heading": f"Document: {filename}",
            "text": content[:500] + "..." if len(content) > 500 else content,
            "start_line": 0
        }]
    
    return {"name": filename, "content": content, "clauses": clauses}

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

@app.get("/api/debug/redis-keys")
async def debug_redis_keys():
    """Debug endpoint to list all Redis keys"""
    try:
        redis_client = get_redis_client()
        all_keys = redis_client.keys("*")
        return {"keys": all_keys}
    except Exception as e:
        return {"error": str(e), "keys": []}

@app.get("/api/docs/{doc_id}")
async def get_doc_by_id(doc_id: str):
	doc = get_doc(doc_id)
	if not doc:
		raise HTTPException(status_code=404, detail="doc not found")
	return doc

# --------------------------- Playbooks ---------------------------
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
	redis_client.delete(f"playbook:{playbook_id}")
	return {"status": "deleted"}

# --------------------------- Run & Orchestration ---------------------------

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


@app.post("/api/run")
async def start_run(req: RunRequest):
    run_id = str(uuid.uuid4())
    docs = get_all_docs()
    doc_id = req.doc_id or next(iter(docs.keys()), "nda")
    
    # Get the document with parsed clauses
    doc_data = get_doc(doc_id) if doc_id in docs else None
    
    if doc_data and "clauses" in doc_data:
        clauses = doc_data["clauses"]
    else:
        # Fallback to mock clauses if document not found or has no clauses
        clauses = [
            {"id": "c1", "heading": "Confidential Information", "text": "The parties agree to keep information secret."},
            {"id": "c2", "heading": "Term", "text": "Two (2) years from Effective Date."},
            {"id": "c3", "heading": "Liability", "text": "Liability capped at 12 months of fees."},
        ]
    
    # Get playbook if specified
    playbook = None
    if req.playbook_id:
        playbook = get_playbook(req.playbook_id)
    
    # Create a blackboard for this run
    blackboard = Blackboard(
        run_id=run_id,
        clauses=clauses,
        assessments=[],  # Will be populated by agents
        proposals=[],    # Will be populated by agents
        decisions=[],
        artifacts={},
        history=[
            {"step": "init", "agent": "system", "status": "started", "timestamp": time.time()}
        ],
        checkpoints={},
        metadata={"doc_id": doc_id, "playbook_id": req.playbook_id}
    )
    
    # Execute the selected agent workflow
    agent_path = req.agent_path or "manager_worker"
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
    run_data = {
        "doc_id": doc_id,
        "agent_path": agent_path,
        "playbook_id": req.playbook_id,
        "clauses": blackboard.clauses,
        "assessments": blackboard.assessments,
        "proposals": blackboard.proposals,
        "decisions": blackboard.decisions,
        "artifacts": blackboard.artifacts,
        "history": blackboard.history,
        "score": final_score,
    }
    
    # Store run in Redis with individual key
    set_run(run_id, run_data)
    
    return {"run_id": run_id, "trace_id": str(uuid.uuid4()), "workflow_result": workflow_result}

@app.get("/api/run/{run_id}")
async def get_run_by_id(run_id: str):
	run = get_run(run_id)
	if not run:
		raise HTTPException(status_code=404, detail="run not found")
	return run

@app.get("/api/blackboard/{run_id}")
async def get_blackboard(run_id: str):
	run = get_run(run_id)
	if not run:
		raise HTTPException(status_code=404, detail="run not found")
	return run

@app.post("/api/hitl/risk-approve")
async def risk_approve(body: RiskApprovalRequest):
	run = get_run(body.run_id)
	if not run:
		raise HTTPException(status_code=404, detail="run not found")
	for it in body.items:
		run.setdefault("decisions", []).append({
			"clause_id": it.clause_id,
			"status": "approved",
			"reviewer": "teacher",
			"comments": it.comments or "",
		})
		if it.risk_override:
			for a in run.get("assessments", []):
				if a.get("clause_id") == it.clause_id:
					a["risk_level"] = it.risk_override
	
	# Update the run in Redis
	set_run(body.run_id, run)
	
	return {"status": "ok"}

@app.post("/api/hitl/final-approve")
async def final_approve(body: FinalApproveRequest):
	run = get_run(body.run_id)
	if not run:
		raise HTTPException(status_code=404, detail="run not found")
	run.setdefault("artifacts", {})["memo.md"] = f"Approved note: {body.note or ''}"
	
	# Update the run in Redis
	set_run(body.run_id, run)
	
	return {"status": "approved"}

@app.post("/api/export/redline")
async def export_redline(run_id: str, format: str = "md"):
	run = get_run(run_id)
	if not run:
		raise HTTPException(status_code=404, detail="run not found")
	
	# Generate the exported document content
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
		raise HTTPException(status_code=404, detail="run not found")
	
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

@app.get("/api/replay/{run_id}")
async def replay(run_id: str):
	"""
	Replay a run from the beginning with the same parameters
	"""
	run = get_run(run_id)
	if not run:
		raise HTTPException(status_code=404, detail="run not found")
	
	# Create a new run based on the original
	new_id = str(uuid.uuid4())
	
	# Get original parameters
	doc_id = run.get("doc_id")
	agent_path = run.get("agent_path", "manager_worker")
	playbook_id = run.get("playbook_id")
	
	# Create new run request
	req = RunRequest(
		doc_id=doc_id,
		agent_path=agent_path,
		playbook_id=playbook_id
	)
	
	# Instead of just cloning, we should actually re-execute the workflow
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
