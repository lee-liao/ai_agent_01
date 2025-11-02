from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import json

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/coach/{session_id}")
async def coach_ws(websocket: WebSocket, session_id: str):
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
                
                if category != 'ok':
                    # Send refusal message
                    await websocket.send_json({
                        "type": "refusal",
                        "data": refusal_data,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    continue
                
                # Get RAG context
                rag_context = retrieve_context(user_text, max_results=2)
                
                # Generate advice with OpenAI
                advice = await generate_advice_non_streaming(user_text, rag_context)
                
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


