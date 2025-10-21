from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
import json
import uuid
from datetime import datetime

from ..database import get_db
from ..models import Call, Transcript

router = APIRouter(tags=["WebSocket"])

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/call/{call_id}")
async def websocket_call_endpoint(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for real-time call handling
    
    Receives:
    - Audio chunks (bytes)
    - Control messages (JSON)
    
    Sends:
    - Transcription updates
    - AI suggestions
    - Status updates
    """
    await websocket.accept()
    active_connections[call_id] = websocket
    
    print(f"✅ WebSocket connected: {call_id}")
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive()
            
            if "bytes" in data:
                # Audio data received
                audio_chunk = data["bytes"]
                print(f"📊 Received audio chunk: {len(audio_chunk)} bytes")
                
                # TODO: Send to transcription service
                # For now, just acknowledge
                await websocket.send_json({
                    "type": "audio_received",
                    "size": len(audio_chunk)
                })
                
            elif "text" in data:
                # Control message received
                message = json.loads(data["text"])
                
                if message["type"] == "start_call":
                    print(f"📞 Call started: {call_id}")
                    await handle_start_call(call_id, message, websocket)
                    
                elif message["type"] == "end_call":
                    print(f"📴 Call ended: {call_id}")
                    await handle_end_call(call_id, message, websocket)
                    break
                    
                elif message["type"] == "transcript":
                    # Manual transcript entry (for testing)
                    await handle_transcript(call_id, message, websocket)
    
    except WebSocketDisconnect:
        print(f"❌ WebSocket disconnected: {call_id}")
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    
    finally:
        # Cleanup
        if call_id in active_connections:
            del active_connections[call_id]

async def handle_start_call(call_id: str, message: dict, websocket: WebSocket):
    """Handle call start"""
    await websocket.send_json({
        "type": "call_started",
        "call_id": call_id,
        "timestamp": datetime.utcnow().isoformat()
    })

async def handle_end_call(call_id: str, message: dict, websocket: WebSocket):
    """Handle call end"""
    await websocket.send_json({
        "type": "call_ended",
        "call_id": call_id,
        "timestamp": datetime.utcnow().isoformat()
    })

async def handle_transcript(call_id: str, message: dict, websocket: WebSocket):
    """Handle transcript segment"""
    # Echo back the transcript
    await websocket.send_json({
        "type": "transcript",
        "speaker": message.get("speaker", "customer"),
        "text": message.get("text", ""),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # TODO: Trigger AI suggestion generation

async def broadcast_to_call(call_id: str, message: dict):
    """Broadcast a message to a specific call's WebSocket"""
    if call_id in active_connections:
        try:
            await active_connections[call_id].send_json(message)
        except Exception as e:
            print(f"Error broadcasting to {call_id}: {e}")

