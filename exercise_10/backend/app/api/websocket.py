from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Optional, List
import json
from datetime import datetime

router = APIRouter(tags=["WebSocket"])

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
# Agent queue subscribers (agent call_id -> True)
agent_queue_subscribers: Dict[str, bool] = {}

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
                from .calls import active_conversations as active_calls
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

                elif message["type"] == "subscribe_queue":
                    # Mark this agent connection as a queue subscriber and send initial snapshot
                    agent_queue_subscribers[call_id] = True
                    try:
                        from .calls import waiting_customers
                        print(f"[WS] Agent {call_id} subscribed; waiting count={len(waiting_customers)}")
                    except Exception:
                        pass
                    await send_queue_update(target_ws=websocket)

                elif message["type"] == "pickup":
                    # Agent requests to pick up a customer. If account_number absent, pick top of queue (FIFO)
                    account_number = message.get("account_number")
                    if not account_number:
                        result = await try_pickup_top(agent_call_id=call_id)
                    else:
                        result = await try_pickup_customer(agent_call_id=call_id, account_number=account_number)
                    print(f"[WS] Pickup requested by {call_id} for {account_number}: {result}")
                    await websocket.send_json({"type": "pickup_result", **result})
                    # If success, notify both ends of conversation start
                    if result.get("status") == "success":
                        await websocket.send_json({
                            "type": "conversation_started",
                            "call_id": call_id,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        customer_call_id = result.get("customer_call_id")
                        if customer_call_id and customer_call_id in active_connections:
                            try:
                                await active_connections[customer_call_id].send_json({
                                    "type": "conversation_started",
                                    "call_id": customer_call_id,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            except Exception:
                                pass
                    # Push latest queue to all subscribers after any pickup attempt
                    await broadcast_queue_update()

                elif message["type"] == "transcript":
                    # Manual transcript entry (for testing) or real transcription
                    await handle_transcript(call_id, message, websocket)
                    # Generate suggestion for agent if customer message
                    if message.get("speaker") == "customer":
                        from .calls import active_conversations as active_calls
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
                
                elif message["type"] == "ping":
                    # Heartbeat response
                    await websocket.send_json({
                        "type": "pong",
                        "ts": datetime.utcnow().isoformat()
                    })
    
    except WebSocketDisconnect:
        print(f"ℹ️ WebSocket disconnected: {call_id}")
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    
    finally:
        # If an active conversation exists for this call_id, notify partner before cleanup
        try:
            from .calls import active_conversations as active_calls
            partner_call_id = None
            key_to_delete = None
            for active_key, call_info in list(active_calls.items()):
                if call_id == call_info.get("agent_call_id"):
                    partner_call_id = call_info.get("customer_call_id")
                    key_to_delete = active_key
                    break
                elif call_id == call_info.get("customer_call_id"):
                    partner_call_id = call_info.get("agent_call_id")
                    key_to_delete = active_key
                    break
            if key_to_delete:
                try:
                    del active_calls[key_to_delete]
                except Exception:
                    pass
                if partner_call_id and partner_call_id in active_connections:
                    try:
                        await active_connections[partner_call_id].send_json({
                            "type": "conversation_ended",
                            "call_id": partner_call_id,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except Exception:
                        pass
        except Exception:
            pass
        # Cleanup connection maps
        if call_id in active_connections:
            del active_connections[call_id]
        if call_id in agent_queue_subscribers:
            del agent_queue_subscribers[call_id]

async def handle_start_call(call_id: str, message: dict, websocket: WebSocket):
    """Acknowledge connection without starting a call automatically."""
    await websocket.send_json({
        "type": "connected",
        "call_id": call_id,
        "timestamp": datetime.utcnow().isoformat()
    })

async def handle_end_call(call_id: str, message: dict, websocket: WebSocket):
    """Handle call end: notify partner and cleanup conversation/waiting state"""
    # Notify sender
    await websocket.send_json({
        "type": "conversation_ended",
        "call_id": call_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    # Try to remove from active conversations and notify partner
    from .calls import active_conversations as active_calls, waiting_customers, available_agents
    partner_call_id = None
    key_to_delete = None
    for active_key, call_info in list(active_calls.items()):
        if call_id == call_info.get("agent_call_id"):
            partner_call_id = call_info.get("customer_call_id")
            key_to_delete = active_key
            break
        elif call_id == call_info.get("customer_call_id"):
            partner_call_id = call_info.get("agent_call_id")
            key_to_delete = active_key
            break
    if key_to_delete:
        try:
            del active_calls[key_to_delete]
        except Exception:
            pass
        if partner_call_id and partner_call_id in active_connections:
            try:
                await active_connections[partner_call_id].send_json({
                    "type": "conversation_ended",
                    "call_id": partner_call_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception:
                pass
    else:
        # Not in active conversation: remove from waiting (Redis) and available list
        removed_waiting = False
        removed_agents = False
        # Try Redis removal first
        try:
            from .queue_service import remove_from_queue as _rm
            await _rm(call_id)
            removed_waiting = True
        except Exception:
            # Fallback to in-memory cleanup for legacy state
            try:
                from .calls import waiting_customers, available_agents
                for i in range(len(waiting_customers) - 1, -1, -1):
                    if waiting_customers[i].get("call_id") == call_id:
                        waiting_customers.pop(i)
                        removed_waiting = True
                        break
                for i in range(len(available_agents) - 1, -1, -1):
                    if available_agents[i].get("call_id") == call_id:
                        available_agents.pop(i)
                        removed_agents = True
                        break
            except Exception:
                pass
        # If queues changed, broadcast updated queue to subscribers
        if removed_waiting or removed_agents:
            try:
                await broadcast_queue_update()
            except Exception:
                pass
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
    from .calls import active_conversations as active_calls
    
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

async def build_queue_items() -> List[dict]:
    from .queue_service import list_queue_items
    return await list_queue_items()

async def send_queue_update(target_ws: Optional[WebSocket] = None):
    payload = {
        "type": "queue_update",
        "items": await build_queue_items(),
        "timestamp": datetime.utcnow().isoformat(),
    }
    if target_ws is not None:
        try:
            await target_ws.send_json(payload)
        except Exception:
            pass
        return
    # broadcast
    for agent_id in list(agent_queue_subscribers.keys()):
        if agent_id in active_connections:
            try:
                await active_connections[agent_id].send_json(payload)
            except Exception:
                pass

async def broadcast_queue_update():
    await send_queue_update(None)

async def try_pickup_customer(agent_call_id: str, account_number: str) -> dict:
    from .calls import active_conversations as active_calls
    from .queue_service import dequeue_by_account_number
    customer_info = await dequeue_by_account_number(account_number)
    if not customer_info:
        return {"status": "not_found"}
    active_calls[agent_call_id] = {
        "agent_call_id": agent_call_id,
        "customer_call_id": customer_info["call_id"],
        "agent_name": "agent",
        "customer_name": customer_info.get("customer_name"),
        "account_number": customer_info.get("account_number"),
        "started_at": datetime.utcnow().isoformat(),
        "status": "active"
    }
    return {
        "status": "success",
        "customer_call_id": customer_info["call_id"],
        "customer_name": customer_info.get("customer_name"),
        "account_number": customer_info.get("account_number"),
    }

async def try_pickup_top(agent_call_id: str) -> dict:
    from .calls import active_conversations as active_calls
    from .queue_service import dequeue_top
    customer_info = await dequeue_top()
    if not customer_info:
        return {"status": "not_found"}
    active_calls[agent_call_id] = {
        "agent_call_id": agent_call_id,
        "customer_call_id": customer_info["call_id"],
        "agent_name": "agent",
        "customer_name": customer_info.get("customer_name"),
        "account_number": customer_info.get("account_number"),
        "started_at": datetime.utcnow().isoformat(),
        "status": "active"
    }
    return {
        "status": "success",
        "customer_call_id": customer_info["call_id"],
        "customer_name": customer_info.get("customer_name"),
        "account_number": customer_info.get("account_number"),
    }

