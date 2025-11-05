from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import json

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/coach/{session_id}")
async def coach_ws(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for coach chat.
    Used by load tests (k6). Frontend uses SSE instead.
    """
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "session_started",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except Exception:
                msg = {"type": "text", "text": data}

            if msg.get("type") == "text":
                user_text = msg.get("text", "").strip()
                
                # Import guardrails, RAG, and LLM
                from app.guardrails import get_guard
                from rag.simple_retrieval import retrieve_context
                from app.llm import generate_advice_non_streaming
                
                # Check guardrails first
                guard = get_guard()
                category, refusal_data = guard.classify_request(user_text)
                
                # Handle HITL-triggering categories (crisis, pii)
                if category in ['crisis', 'pii']:
                    # Import HITL functions
                    from app.guardrails import create_hitl_case
                    
                    # Create HITL case
                    hitl_id = create_hitl_case(
                        session_id=session_id,
                        category=category,
                        user_message=user_text,
                        conversation_history=[]  # Could track history if needed
                    )
                    
                    # Send holding message to parent
                    await websocket.send_json({
                        "type": "hitl_queued",
                        "message": "Thank you for reaching out. A mentor will review your message and respond shortly. Please know that your safety and your child's safety are our top priority.",
                        "hitl_id": hitl_id,
                        "category": category,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    continue
                
                if category != 'ok':
                    # Send refusal message for other out-of-scope categories
                    await websocket.send_json({
                        "type": "refusal",
                        "data": refusal_data,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    continue
                
                # Get RAG context
                rag_context = retrieve_context(user_text, max_results=2)
                
                # Generate advice with OpenAI (with session_id for cost tracking)
                advice = await generate_advice_non_streaming(user_text, rag_context, session_id)
                
                # Extract citations
                citations = [
                    {'source': doc['source'], 'url': doc['url']}
                    for doc in rag_context
                ]
                
                await websocket.send_json({
                    "type": "advice",
                    "text": advice,
                    "citations": citations,
                    "echo": user_text,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            else:
                await websocket.send_json({"type": "noop"})

    except WebSocketDisconnect:
        pass


