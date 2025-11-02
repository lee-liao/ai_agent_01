from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uuid
import json
import asyncio

router = APIRouter(prefix="/api/coach", tags=["Coach"])

# Track tokens for streaming (since we can't get usage from stream directly)
streaming_token_estimate = {}


class StartSessionRequest(BaseModel):
    parent_name: str


@router.post("/start")
async def start_session(req: StartSessionRequest):
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    return {
        "session_id": session_id,
        "message": f"Welcome {req.parent_name}! You can start chatting with your parenting coach.",
    }


@router.get("/cost-status")
async def get_cost_status():
    """
    Get current cost tracking status.
    Useful for admin monitoring and budget checks.
    """
    from billing.ledger import get_tracker
    tracker = get_tracker()
    return tracker.get_budget_status()


@router.get("/stream/{session_id}")
async def stream_advice(session_id: str, question: str):
    """
    SSE endpoint for streaming advice responses using OpenAI API.
    Includes guardrails checking and RAG context.
    """
    
    async def generate():
        # Import here to avoid circular dependency
        from app.guardrails import get_guard
        from rag.simple_retrieval import retrieve_context
        from app.llm import generate_advice_streaming
        
        # Check guardrails first
        guard = get_guard()
        category, refusal_data = guard.classify_request(question)
        
        if category != 'ok':
            # Send refusal as a single chunk
            yield f"data: {json.dumps({'type': 'refusal', 'data': refusal_data})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
            return
        
        # Get RAG context
        rag_context = retrieve_context(question, max_results=2)
        
        # Extract citations for frontend
        citations = [
            {'source': doc['source'], 'url': doc['url']}
            for doc in rag_context
        ]
        
        # Stream advice from OpenAI
        try:
            token_count = 0
            async for chunk in generate_advice_streaming(question, rag_context):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                token_count += len(chunk.split())  # Rough token estimate
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
            
            # Estimate costs for streaming (can't get exact from stream)
            # Rough estimate: ~1.3 tokens per word
            from billing.ledger import get_tracker
            tracker = get_tracker()
            estimated_prompt = len(question.split()) * 1.3 + 200  # Question + system prompt
            estimated_completion = token_count * 1.3
            tracker.log_usage(
                session_id=session_id,
                model="gpt-3.5-turbo",
                prompt_tokens=int(estimated_prompt),
                completion_tokens=int(estimated_completion)
            )
            
            # Send citations and done signal
            yield f"data: {json.dumps({'done': True, 'citations': citations})}\n\n"
            
        except Exception as e:
            # Error handling
            error_msg = f"I apologize, but I'm having trouble generating a response right now. Please try again."
            yield f"data: {json.dumps({'chunk': error_msg})}\n\n"
            yield f"data: {json.dumps({'done': True, 'citations': []})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


