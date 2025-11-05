from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uuid
import json
import asyncio
from app.sse_manager import create_sse_stream

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
        # Track if we've already sent the done signal to avoid overwriting citations
        done_sent = False
        
        # Wrap entire generator in try/except to prevent stack trace exposure
        try:
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
                    try:
                        yield f"data: {json.dumps({'type': 'refusal', 'data': refusal_data})}\n\n"
                    except Exception:
                        # If JSON serialization fails, send generic error (no exception details)
                        yield f"data: {json.dumps({'type': 'error', 'message': 'An error occurred'})}\n\n"
                
                # Create HITL case
                hitl_id = create_hitl_case(
                    session_id=session_id,
                    category=category,
                    user_message=question,
                    conversation_history=[]  # Could track history if needed
                )
                
                # For PII scenarios (no refusal_data), send HITL queued message
                if category == 'pii':
                    try:
                        yield f"data: {json.dumps({'type': 'hitl_queued', 'message': 'Thank you for reaching out. A mentor will review your message and respond shortly. Please know that your safety and your child\'s safety are our top priority.', 'hitl_id': hitl_id, 'category': category})}\n\n"
                    except Exception:
                        # If JSON serialization fails, send generic error (no exception details)
                        yield f"data: {json.dumps({'type': 'error', 'message': 'An error occurred'})}\n\n"
                
                try:
                    yield f"data: {json.dumps({'done': True})}\n\n"
                except Exception:
                    # Silently fail if final yield fails (connection likely closed)
                    pass
                return
            
            # Handle other out-of-scope categories (medical, legal, therapy)
            if category != 'ok':
                # Only send refusal if refusal_data exists
                try:
                    if refusal_data:
                        yield f"data: {json.dumps({'type': 'refusal', 'data': refusal_data})}\n\n"
                    else:
                        # Fallback message if refusal_data is None
                        yield f"data: {json.dumps({'type': 'refusal', 'data': {'empathy': 'Thank you for reaching out.', 'message': 'I\'m not able to help with that specific question. Please consult a professional for guidance.', 'resources': []}})}\n\n"
                    yield f"data: {json.dumps({'done': True})}\n\n"
                except Exception:
                    # If JSON serialization fails, send generic error (no exception details)
                    try:
                        yield f"data: {json.dumps({'type': 'error', 'message': 'An error occurred'})}\n\n"
                        yield f"data: {json.dumps({'done': True})}\n\n"
                    except Exception:
                        pass
                return
            
            # Get RAG context
            rag_context = retrieve_context(question, max_results=2)
            
            # Extract citations for frontend
            citations = [
                {'source': doc['source'], 'url': doc['url']}
                for doc in rag_context
            ]
            
            # Stream advice from OpenAI
            token_count = 0
            try:
                async for chunk in generate_advice_streaming(question, rag_context, session_id=session_id):
                    try:
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    except Exception:
                        # If JSON serialization fails during streaming, break loop
                        break
                    token_count += len(chunk.split())  # Rough token estimate
                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)
            except Exception:
                # If streaming fails, send error message
                try:
                    yield f"data: {json.dumps({'chunk': 'I apologize, but I\'m having trouble generating a response right now. Please try again.'})}\n\n"
                except Exception:
                    pass
            
            # Send citations and done signal FIRST (before cost tracking)
            # This ensures citations are sent even if cost tracking fails
            try:
                yield f"data: {json.dumps({'done': True, 'citations': citations})}\n\n"
                done_sent = True  # Mark that we've sent the done signal
            except Exception:
                # If final yield fails, connection likely closed
                pass
            
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
            # Catch all exceptions to prevent stack trace exposure to users
            # Log error server-side for debugging (never expose to users)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during advice streaming: {type(e).__name__}", exc_info=True)
            
            # Only send error message if we haven't already sent the done signal
            # If done_sent is True, the response was already successfully sent with citations
            # Don't overwrite it with an error message
            if not done_sent:
                # Send safe, user-friendly error message (no stack traces or internal details)
                # Wrap in try/except to ensure no exception leaks even from error handling
                try:
                    error_msg = "I apologize, but I'm having trouble generating a response right now. Please try again."
                    yield f"data: {json.dumps({'chunk': error_msg})}\n\n"
                    yield f"data: {json.dumps({'done': True, 'citations': []})}\n\n"
                except Exception:
                    # If even error message fails to send, connection is likely closed
                    # No need to log or expose anything
                    pass
            else:
                # Response already sent successfully, just log the error
                logger.warning(f"Error occurred after response was sent: {type(e).__name__} (likely cost tracking)")
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


