from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uuid
import json
import asyncio
from app.sse_manager import sse_manager, create_sse_stream

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


@router.get("/events/{session_id}")
async def stream_events(session_id: str):
    """
    Persistent SSE stream for receiving real-time events (mentor replies, etc.).
    This connection stays open and receives push messages from the server.
    """
    return StreamingResponse(
        create_sse_stream(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/hitl/events")
async def stream_hitl_events():
    """
    Persistent SSE stream for mentor queue updates.
    Pushes real-time updates when new cases are created or cases are updated.
    """
    # Use a special session ID for mentor queue
    return StreamingResponse(
        create_sse_stream("mentor_queue"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


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
        
        # Handle HITL-triggering categories (crisis, pii)
        if category in ['crisis', 'pii']:
            # Import HITL functions
            from app.guardrails import create_hitl_case
            import time as time_module
            
            # For crisis scenarios, send refusal message first (with resources like 988)
            # For PII, refusal_data is None, so skip refusal message
            if category == 'crisis' and refusal_data:
                yield f"data: {json.dumps({'type': 'refusal', 'data': refusal_data})}\n\n"
            
            # Create HITL case (measure latency for SLO)
            start_time = time_module.time()
            hitl_id = create_hitl_case(
                session_id=session_id,
                category=category,
                user_message=question,
                conversation_history=[]  # Could track history if needed
            )
            routing_latency_ms = (time_module.time() - start_time) * 1000
            
            # For PII scenarios (no refusal_data), send HITL queued message
            if category == 'pii':
                yield f"data: {json.dumps({'type': 'hitl_queued', 'message': 'Thank you for reaching out. A mentor will review your message and respond shortly. Please know that your safety and your child\'s safety are our top priority.', 'hitl_id': hitl_id, 'category': category})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            return
        
        # Handle other out-of-scope categories (medical, legal, therapy)
        if category != 'ok':
            # Only send refusal if refusal_data exists
            if refusal_data:
                yield f"data: {json.dumps({'type': 'refusal', 'data': refusal_data})}\n\n"
            else:
                # Fallback message if refusal_data is None
                yield f"data: {json.dumps({'type': 'refusal', 'data': {'empathy': 'Thank you for reaching out.', 'message': 'I\'m not able to help with that specific question. Please consult a professional for guidance.', 'resources': []}})}\n\n"
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
            async for chunk in generate_advice_streaming(question, rag_context, session_id=session_id):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                token_count += len(chunk.split())  # Rough token estimate
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
            
            # Send citations and done signal FIRST (before cost tracking)
            # This ensures citations are sent even if cost tracking fails
            yield f"data: {json.dumps({'done': True, 'citations': citations})}\n\n"
            
            # Estimate costs for streaming (can't get exact from stream)
            # Do this after sending done signal so it doesn't block the response
            try:
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
            except Exception as cost_error:
                # Log cost tracking error but don't fail the request
                # Log only error type, not full exception details to avoid exposure
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Cost tracking failed: {type(cost_error).__name__}", exc_info=True)
            
        except Exception as e:
            # Error handling - only catch errors during streaming
            # Log error server-side for debugging (never expose to users)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during advice streaming: {type(e).__name__}", exc_info=True)
            
            # Send safe, user-friendly error message (no stack traces or internal details)
            error_msg = "I apologize, but I'm having trouble generating a response right now. Please try again."
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


