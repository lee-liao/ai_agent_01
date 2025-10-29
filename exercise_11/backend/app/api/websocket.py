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
                advice = (
                    "I hear you. Here are a few ideas you might try: "
                    "1) Acknowledge feelings, 2) Offer a simple choice, 3) Keep routines consistent."
                )
                await websocket.send_json({
                    "type": "advice",
                    "text": advice,
                    "echo": user_text,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            else:
                await websocket.send_json({"type": "noop"})

    except WebSocketDisconnect:
        pass


