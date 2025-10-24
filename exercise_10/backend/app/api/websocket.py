from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
from datetime import datetime

router = APIRouter(tags=["WebSocket"])

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Services
from ..config import settings
from .whisper_service import WhisperService
from .ai_service import AIAssistantService

whisper_service = WhisperService(settings.OPENAI_API_KEY)
ai_service = AIAssistantService(settings.OPENAI_API_KEY)

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
                print(f"📊 Received audio chunk: {len(audio_chunk)} bytes from {call_id}")
                
                # Simulate transcription (in production, send to Whisper API)
                # For demo, we'll just acknowledge receipt
                await websocket.send_json({
                    "type": "audio_received",
                    "size": len(audio_chunk),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Route audio to partner (for future real-time audio streaming)
                from .calls import active_calls
                partner_call_id = None
                for active_call_id, call_info in active_calls.items():
                    if call_id == call_info.get("agent_call_id"):
                        partner_call_id = call_info.get("customer_call_id")
                        break
                    elif call_id == call_info.get("customer_call_id"):
                        partner_call_id = call_info.get("agent_call_id")
                        break

                # Transcribe audio and emit transcript/suggestion
                transcript_text = ""
                try:
                    transcript_text = await whisper_service.transcribe_audio(audio_chunk)
                except Exception as e:
                    print(f"Whisper error: {e}")

                if transcript_text:
                    # Determine speaker based on mapping
                    speaker = "customer"
                    for _, cinfo in active_calls.items():
                        if call_id == cinfo.get("agent_call_id"):
                            speaker = "agent"
                            break
                        elif call_id == cinfo.get("customer_call_id"):
                            speaker = "customer"
                            break

                    transcript_msg = {
                        "type": "transcript",
                        "speaker": speaker,
                        "text": transcript_text,
                        "timestamp": datetime.utcnow().isoformat()
                    }

                    # Echo to sender
                    await websocket.send_json(transcript_msg)

                    # Forward to partner
                    if partner_call_id and partner_call_id in active_connections:
                        try:
                            await active_connections[partner_call_id].send_json(transcript_msg)
                        except Exception as e:
                            print(f"Error routing transcript: {e}")

                    # Generate AI suggestion for agent when customer spoke
                    if speaker == "customer" and partner_call_id and partner_call_id in active_connections:
                        suggestion = await ai_service.generate_suggestion(call_id=call_id, customer_message=transcript_text)
                        try:
                            await active_connections[partner_call_id].send_json({
                                "type": "ai_suggestion",
                                "suggestion": suggestion.get("suggestion", ""),
                                "confidence": suggestion.get("confidence", 0.0),
                                "timestamp": suggestion.get("timestamp", datetime.utcnow().isoformat())
                            })
                        except Exception as e:
                            print(f"Error sending suggestion: {e}")
                
                # Forward audio to partner if connected
                if partner_call_id and partner_call_id in active_connections:
                    try:
                        await active_connections[partner_call_id].send_bytes(audio_chunk)
                        print(f"📤 Forwarded audio from {call_id} to {partner_call_id}")
                    except Exception as e:
                        print(f"Error forwarding audio: {e}")
                
            elif "text" in data:
                # Control message received
                message = json.loads(data["text"])
                
                if message["type"] == "start_call":
                    print(f"▶️ Call started: {call_id}")
                    await handle_start_call(call_id, message, websocket)
                    
                elif message["type"] == "end_call":
                    print(f"⏹️ Call ended: {call_id}")
                    await handle_end_call(call_id, message, websocket)
                    return
                    
                elif message["type"] == "transcript":
                    # Manual transcript entry (for testing) or real transcription
                    await handle_transcript(call_id, message, websocket)
                    # Generate suggestion for agent if customer message
                    if message.get("speaker") == "customer":
                        from .calls import active_calls
                        partner_call_id = None
                        for active_call_id, call_info in active_calls.items():
                            if call_id == call_info.get("agent_call_id"):
                                partner_call_id = call_info.get("customer_call_id")
                                break
                            elif call_id == call_info.get("customer_call_id"):
                                partner_call_id = call_info.get("agent_call_id")
                                break
                        if partner_call_id and partner_call_id in active_connections:
                            suggestion = await ai_service.generate_suggestion(call_id=call_id, customer_message=message.get("text", ""))
                            try:
                                await active_connections[partner_call_id].send_json({
                                    "type": "ai_suggestion",
                                    "suggestion": suggestion.get("suggestion", ""),
                                    "confidence": suggestion.get("confidence", 0.0),
                                    "timestamp": suggestion.get("timestamp", datetime.utcnow().isoformat())
                                })
                            except Exception as e:
                                print(f"Error sending suggestion: {e}")
    
    except WebSocketDisconnect:
        print(f"ℹ️ WebSocket disconnected: {call_id}")
    
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
    await websocket.close(code=1000)

async def handle_transcript(call_id: str, message: dict, websocket: WebSocket):
    """Handle transcript segment and route to partner"""
    speaker = message.get("speaker", "customer")
    text = message.get("text", "")
    
    transcript_msg = {
        "type": "transcript",
        "speaker": speaker,
        "text": text,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Echo back to sender (for confirmation)
    await websocket.send_json(transcript_msg)
    
    # Route to partner (agent or customer)
    # Import from calls.py to check active connections
    from .calls import active_calls
    
    # Find partner's call_id
    partner_call_id = None
    for active_call_id, call_info in active_calls.items():
        if call_id == call_info.get("agent_call_id"):
            partner_call_id = call_info.get("customer_call_id")
            break
        elif call_id == call_info.get("customer_call_id"):
            partner_call_id = call_info.get("agent_call_id")
            break
    
    # Send to partner if connected
    if partner_call_id and partner_call_id in active_connections:
        try:
            await active_connections[partner_call_id].send_json(transcript_msg)
            print(f"📤 Routed message from {call_id} to {partner_call_id}")
        except Exception as e:
            print(f"Error routing message: {e}")

async def broadcast_to_call(call_id: str, message: dict):
    """Broadcast a message to a specific call's WebSocket"""
    if call_id in active_connections:
        try:
            await active_connections[call_id].send_json(message)
        except Exception as e:
            print(f"Error broadcasting to {call_id}: {e}")

