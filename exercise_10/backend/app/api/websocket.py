from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Optional, List
import json
from datetime import datetime

router = APIRouter(tags=["WebSocket"])

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
# Agent queue subscribers (agent call_id -> True)
agent_queue_subscribers: Dict[str, bool] = {}

# Audio buffers for transcription (call_id -> bytearray)
audio_buffers: Dict[str, bytearray] = {}

# Buffer size: 4 seconds of audio - balancing responsiveness with transcription quality
BUFFER_SIZE_SECONDS = 4

# Services
from ..config import settings
from .whisper_service import transcribe_audio
from .ai_service import generate_suggestion
from .context_manager import get_context

import io
import wave
from pydub import AudioSegment

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
    audio_buffers[call_id] = bytearray()  # Initialize audio buffer

    print(f"✅ WebSocket connected: {call_id}")
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive()
            
            if "bytes" in data:
                # Audio data received
                audio_chunk = data["bytes"]
                print(f"📊 Received audio chunk: {len(audio_chunk)} bytes from {call_id}")
                
                # Route audio to partner (for real-time audio streaming)
                from .calls import active_conversations as active_calls
                partner_call_id = None
                speaker = "customer"  # default
                
                # Find partner and determine speaker
                for active_call_id, call_info in active_calls.items():
                    if call_id == call_info.get("agent_call_id"):
                        partner_call_id = call_info.get("customer_call_id")
                        speaker = "agent"
                        break
                    elif call_id == call_info.get("customer_call_id"):
                        partner_call_id = call_info.get("agent_call_id")
                        speaker = "customer"
                        break

                # Forward audio to partner if connected
                if partner_call_id and partner_call_id in active_connections:
                    try:
                        await active_connections[partner_call_id].send_bytes(audio_chunk)
                        print(f"📤 Forwarded audio from {call_id} to {partner_call_id}")
                    except Exception as e:
                        print(f"Error forwarding audio: {e}")

                # Process audio chunk for transcription (individual chunks for immediate feedback)
                # Transcribe the audio chunk in background to avoid blocking
                asyncio.create_task(
                    transcribe_and_broadcast(
                        call_id, 
                        audio_chunk,  # Process the individual chunk
                        speaker, 
                        websocket, 
                        partner_call_id
                    )
                )
                
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

                elif message["type"] == "agent_availability_update":
                    # In the simplified model, agents don't use availability states
                    # They remain in monitoring mode and manually pick customers
                    print(f"⚠️ Agent availability update received but not used in simplified model: {call_id}")
                    
                    # Send a message back indicating the simplified model
                    await websocket.send_json({
                        "type": "availability_ignored",
                        "message": "In simplified model, agents remain in monitoring mode. Use pickup actions to get customers.",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif message["type"] == "pickup":
                    # Agent requests to pick up a customer. If account_number absent, pick top of queue (FIFO)
                    account_number = message.get("account_number")
                    if not account_number:
                        result = await try_pickup_top(agent_call_id=call_id)
                    else:
                        result = await try_pickup_customer(agent_call_id=call_id, account_number=account_number)
                    print(f"[WS] Pickup requested by {call_id} for {account_number}: {result}")
                    await websocket.send_json({"type": "pickup_result", **result})
                    # If success, notify both ends of conversation start and send customer context to agent
                    if result.get("status") == "success":
                        # Send conversation started to agent
                        await websocket.send_json({
                            "type": "conversation_started",
                            "call_id": call_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "customer_name": result.get("customer_name"),
                            "account_number": result.get("account_number")
                        })
                        
                        # Send customer context to agent for Customer Info panel
                        if result.get("account_number"):
                            try:
                                # Use the existing send_customer_context function
                                await send_customer_context(websocket, account_number=result["account_number"])
                            except Exception as e:
                                print(f"❌ Failed to fetch customer context for {result.get('account_number')}: {e}")
                        
                        # Send immediate queue update to the agent who just picked up customer
                        # This ensures their UI shows the current queue state (likely empty)
                        await send_queue_update(target_ws=websocket)
                        
                        customer_call_id = result.get("customer_call_id")
                        if customer_call_id and customer_call_id in active_connections:
                            try:
                                await active_connections[customer_call_id].send_json({
                                    "type": "conversation_started",
                                    "call_id": customer_call_id,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            except Exception as e:
                                print(f"❌ Failed to send conversation_started to {customer_call_id}: {e}")

                elif message["type"] == "conversation_started":
                    # Conversation started - trigger customer context fetch for agent
                    from .calls import active_conversations as active_calls
                    conversation_info = None
                    for active_call_id, call_info in active_calls.items():
                        if call_info.get("agent_call_id") == call_id or call_info.get("customer_call_id") == call_id:
                            conversation_info = call_info
                            break
                    
                    if conversation_info:
                        # Send conversation_started back to sender
                        await websocket.send_json({
                            "type": "conversation_started",
                            "call_id": call_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            **conversation_info
                        })
                        
                        # Fetch and send customer context to the agent
                        partner_call_id = None
                        for active_call_id, call_info in active_calls.items():
                            if call_id == call_info.get("agent_call_id"):
                                partner_call_id = call_info.get("customer_call_id")
                                await send_customer_context(websocket, conversation_info.get("account_number"), conversation_info.get("customer_name"))
                                break
                            elif call_id == call_info.get("customer_call_id"):
                                partner_call_id = call_info.get("agent_call_id")
                                # Customer doesn't need context, but agent will get it when conversation starts
                                break
                    else:
                        # Send basic conversation_started message
                        await websocket.send_json({
                            "type": "conversation_started",
                            "call_id": call_id,
                            "timestamp": datetime.utcnow().isoformat()
                        })

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
                            suggestion = await generate_suggestion(call_id=call_id, customer_message=message.get("text", ""))
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
        import traceback
        print(f"❌ WebSocket error: {e}")
        traceback.print_exc()
    
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
                print(f"[cleanup] Deleting active conversation with key: {key_to_delete} for call_id: {call_id}")
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
        if call_id in audio_buffers:
            del audio_buffers[call_id]
        # Cleanup conversation context
        from .context_manager import clear_context
        clear_context(call_id)

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
    from .calls import active_conversations as active_calls, available_agents
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
        print(f"[handle_end_call] Deleting active conversation with key: {key_to_delete} for call_id: {call_id}")
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
            pass # No fallback, as in-memory queue is deprecated
        
        # In-memory cleanup for available_agents (legacy)
        try:
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
            except Exception as e:
                print(f"Error in broadcast_queue_update: {e}")
                import traceback
                traceback.print_exc()
    try:
        # After call ends, send the current queue state to the agent so they can see available customers
        print(f"DEBUG: About to send queue update to agent {call_id} after call ended")
        await send_queue_update(target_ws=websocket)
        print(f"DEBUG: Successfully sent queue update to agent {call_id}")
    except Exception as e:
        print(f"Error sending queue update after call end: {e}")
        import traceback
        traceback.print_exc()
        # Don't close connection - continue with the function
    user_type = message.get("user_type")
    if user_type != 'agent':
        await websocket.close()

import asyncio

async def transcribe_audio_buffer(call_id: str, audio_data: bytes, speaker: str) -> str:
    """Transcribe audio buffer using Whisper API with proper format handling"""
    try:
        print(f"🎵 About to transcribe audio for {speaker}, size: {len(audio_data)} bytes")
        
        # Use pydub to handle the WebM format properly
        # Note: concatenated WebM chunks are still not valid WebM files
        # Better approach: try to send as WAV after conversion or send as WebM if Whisper supports it directly
        
        # Try to process directly with Whisper if it supports WebM
        transcript = await transcribe_audio(audio_data, "audio.webm")
        
        if transcript:
            print(f"✅ Transcription successful for {speaker}: {transcript[:50]}...")
            return transcript
        else:
            print(f"⚠️ Whisper API could not transcribe, trying format conversion...")
            
            # If direct processing fails, try to use pydub for format conversion
            try:
                # Create an audio segment from the WebM data
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
                
                # Export as WAV in memory
                wav_io = io.BytesIO()
                audio_segment.export(wav_io, format="wav")
                wav_io.seek(0)
                
                # Now call Whisper API with WAV format
                transcript = await transcribe_audio(wav_io.read(), "audio.wav")
                
                if transcript:
                    print(f"✅ Transcription successful (after conversion) for {speaker}: {transcript[:50]}...")
                    return transcript
                else:
                    print(f"⚠️ Still no transcription after format conversion for {speaker}")
                    return None
            except Exception as format_error:
                print(f"❌ Format conversion failed: {format_error}")
                return None
        
    except Exception as e:
        print(f"❌ Transcription error for {speaker}: {e}")
        import traceback
        traceback.print_exc()
        return None

async def transcribe_and_broadcast(
    call_id: str,
    audio_data: bytes,
    speaker: str,
    sender_ws: WebSocket,
    partner_call_id: str = None
):
    """Transcribe audio and send to both sender and partner"""
    try:
        # Transcribe the audio
        text = await transcribe_audio_buffer(call_id, audio_data, speaker)
        
        if not text:
            print(f"⚠️ No transcription result for {speaker} audio")
            return
        
        print(f"📝 Transcription result for {speaker}: {text[:50]}...")
        
        # Create transcript message
        transcript_msg = {
            "type": "transcript",
            "speaker": speaker,
            "text": text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add transcript to conversation context
        context = get_context(call_id)
        context.add_message(speaker, text)
        
        # Send to sender
        try:
            await sender_ws.send_json(transcript_msg)
            print(f"📤 Sent transcript to sender ({speaker}): {text[:30]}...")
        except Exception as e:
            print(f"❌ Error sending transcript to sender: {e}")

        # Send to partner
        if partner_call_id and partner_call_id in active_connections:
            try:
                await active_connections[partner_call_id].send_json(transcript_msg)
                print(f"📤 Sent transcript to partner: {text[:30]}...")
            except Exception as e:
                print(f"❌ Error sending transcript to partner: {e}")
                # Remove dead connection
                if partner_call_id in active_connections:
                    del active_connections[partner_call_id]

        # Generate AI suggestion for agent when customer speaks
        # (keeping the same pattern from the original code)
        from .ai_service import generate_suggestion
        if speaker == "customer" and partner_call_id and partner_call_id in active_connections:
            print(f"💡 Generating AI suggestion for agent {partner_call_id} based on customer message: {text[:50]}...")
            suggestion = await generate_suggestion(call_id=call_id, customer_message=text)
            print(f"💡 AI suggestion generated: {suggestion}")
            try:
                ai_suggestion_msg = {
                    "type": "ai_suggestion",
                    "suggestion": suggestion.get("suggestion", ""),
                    "confidence": suggestion.get("confidence", 0.0),
                    "timestamp": suggestion.get("timestamp", datetime.utcnow().isoformat())
                }
                await active_connections[partner_call_id].send_json(ai_suggestion_msg)
                print(f"🤖 Sent AI suggestion to agent {partner_call_id}: {suggestion.get('suggestion', '')[:30]}...")
            except Exception as e:
                print(f"❌ Error sending AI suggestion to agent {partner_call_id}: {e}")
                import traceback
                traceback.print_exc()
        else:
            if speaker != "customer":
                print(f"💬 Speaker is '{speaker}', not generating AI suggestion (only generated for customer messages)")
            elif not partner_call_id:
                print(f"💬 No partner found for customer {call_id}, not generating AI suggestion")
            elif partner_call_id not in active_connections:
                print(f"💬 Partner {partner_call_id} not in active connections, not generating AI suggestion")

    except Exception as e:
        print(f"❌ Error in transcribe_and_broadcast: {e}")

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
    
    print(f"📝 Transcript received from {call_id} (speaker: {speaker}): {text[:50]}...")
    
    # Add transcript to conversation context
    context = get_context(call_id)
    context.add_message(speaker, text)
    
    # Echo back to sender (for confirmation)
    await websocket.send_json(transcript_msg)
    
    # Route to partner (agent or customer)
    # Import from calls.py to check active connections
    from .calls import active_conversations as active_calls
    
    print(f"🔍 Looking for partner of {call_id} in {len(active_calls)} active conversations")
    
    # Find partner's call_id - search in both keys and values
    partner_call_id = None
    
    # First, check if this call_id is directly in the keys and has the partner in its value
    if call_id in active_calls:
        call_info = active_calls[call_id]
        if "agent_call_id" in call_info and "customer_call_id" in call_info:
            if call_id == call_info["agent_call_id"]:
                partner_call_id = call_info.get("customer_call_id")
                print(f"👤 Found partner (direct key match): agent {call_id} -> customer {partner_call_id}")
            elif call_id == call_info["customer_call_id"]:
                partner_call_id = call_info.get("agent_call_id")
                print(f"👤 Found partner (direct key match): customer {call_id} -> agent {partner_call_id}")
    
    # If not found yet, search through all conversation values
    if partner_call_id is None:
        for active_call_id, call_info in active_calls.items():
            print(f"  Checking conversation: {active_call_id} -> {call_info}")
            if "agent_call_id" in call_info and "customer_call_id" in call_info:
                # Check if this conversation contains our call_id
                if call_id == call_info["agent_call_id"]:
                    partner_call_id = call_info["customer_call_id"]
                    print(f"👤 Found partner (in conversation value): agent {call_id} -> customer {partner_call_id}")
                    break
                elif call_id == call_info["customer_call_id"]:
                    partner_call_id = call_info["agent_call_id"]
                    print(f"👤 Found partner (in conversation value): customer {call_id} -> agent {partner_call_id}")
                    break

    print(f"🔍 Final partner result: {partner_call_id}")
    
    if partner_call_id:
        print(f"📡 Attempting to route message to {partner_call_id}, connection exists: {partner_call_id in active_connections}")
        # Send to partner if connected
        if partner_call_id and partner_call_id in active_connections:
            try:
                await active_connections[partner_call_id].send_json(transcript_msg)
                print(f"📤 Successfully routed message from {call_id} (speaker: {speaker}) to {partner_call_id}")
            except Exception as e:
                print(f"❌ Error routing message from {call_id} to {partner_call_id}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️ Partner {partner_call_id} not connected in active_connections (available keys: {list(active_connections.keys())})")
    else:
        print(f"⚠️ No partner found for {call_id}")
        print(f"  Active conversations: {active_calls}")
    
    # Generate AI suggestion for agent when customer speaks
    # (keeping the same pattern from the original code)
    from .ai_service import generate_suggestion
    if speaker == "customer" and partner_call_id and partner_call_id in active_connections:
        print(f"💡 Generating AI suggestion for agent {partner_call_id} based on customer message: {text[:50]}...")
        suggestion = await generate_suggestion(call_id=call_id, customer_message=text)
        print(f"💡 AI suggestion generated: {suggestion}")
        try:
            ai_suggestion_msg = {
                "type": "ai_suggestion",
                "suggestion": suggestion.get("suggestion", ""),
                "confidence": suggestion.get("confidence", 0.0),
                "timestamp": suggestion.get("timestamp", datetime.utcnow().isoformat())
            }
            await active_connections[partner_call_id].send_json(ai_suggestion_msg)
            print(f"🤖 Sent AI suggestion to agent {partner_call_id}: {suggestion.get('suggestion', '')[:30]}...")
        except Exception as e:
            print(f"❌ Error sending AI suggestion to agent {partner_call_id}: {e}")
            import traceback
            traceback.print_exc()
    else:
        if speaker != "customer":
            print(f"💬 Speaker is '{speaker}', not generating AI suggestion (only generated for customer messages)")
        elif not partner_call_id:
            print(f"💬 No partner found for customer {call_id}, not generating AI suggestion")
        elif partner_call_id not in active_connections:
            print(f"💬 Partner {partner_call_id} not in active connections, not generating AI suggestion")

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
        return {"status": "not_found", "message": f"No customer found with account number {account_number}. Customer may have been served by another agent or disconnected."}
    
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


async def send_customer_context(websocket: WebSocket, account_number: str = None, customer_name: str = None):
    """
    Send customer context to the agent when a call starts.
    Fetches customer details from the database and sends them via WebSocket.
    """
    try:
        from sqlalchemy import select
        from ..models import Customer, Order, Ticket
        from ..database import async_session_maker
        
        # Search by account number first, then by name
        search_param = account_number or customer_name
        if not search_param:
            return
        
        async with async_session_maker() as session:
            # Query customer by account number or name
            query = select(Customer).where(
                (Customer.account_number == search_param) if account_number 
                else (Customer.name.ilike(f"%{customer_name}%"))
            )
            
            result = await session.execute(query)
            customer = result.scalar_one_or_none()
            
            if not customer:
                # Try a more flexible search if exact match fails
                if account_number:
                    query = select(Customer).where(Customer.account_number.ilike(f"%{account_number}%"))
                else:
                    query = select(Customer).where(Customer.name.ilike(f"%{customer_name}%"))
                
                result = await session.execute(query)
                customer = result.scalar_one_or_none()
            
            if customer:
                # Fetch related data
                orders_query = select(Order).where(Order.customer_id == customer.id).order_by(Order.order_date.desc()).limit(10)
                orders_result = await session.execute(orders_query)
                orders = orders_result.scalars().all()
                
                tickets_query = select(Ticket).where(Ticket.customer_id == customer.id).order_by(Ticket.created_at.desc()).limit(5)
                tickets_result = await session.execute(tickets_query)
                tickets = tickets_result.scalars().all()
                
                # Build customer context response
                customer_context = {
                    "type": "customer_context",
                    "customer": {
                        "id": customer.id,
                        "name": customer.name,
                        "email": customer.email,
                        "phone": customer.phone,
                        "account_number": customer.account_number,
                        "tier": customer.tier,
                        "status": customer.status,
                        "lifetime_value": float(customer.lifetime_value) if customer.lifetime_value else 0.0
                    },
                    "orders": [
                        {
                            "id": order.id,
                            "order_number": order.order_number,
                            "product_name": order.product_name,
                            "amount": float(order.amount) if order.amount else 0.0,
                            "status": order.status,
                            "order_date": order.order_date.isoformat() if order.order_date else ""
                        }
                        for order in orders
                    ],
                    "tickets": [
                        {
                            "id": ticket.id,
                            "ticket_number": ticket.ticket_number,
                            "subject": ticket.subject,
                            "status": ticket.status,
                            "priority": ticket.priority,
                            "created_at": ticket.created_at.isoformat() if ticket.created_at else ""
                        }
                        for ticket in tickets
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Send customer context to agent
                await websocket.send_json(customer_context)
                
    except Exception as e:
        print(f"Error fetching customer context: {e}")
        # Send a minimal response to indicate failure gracefully
        try:
            await websocket.send_json({
                "type": "customer_context",
                "error": "Failed to fetch customer details",
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception:
            pass


async def try_pickup_top(agent_call_id: str) -> dict:
    from .calls import active_conversations as active_calls
    from .queue_service import dequeue_top
    
    customer_info = await dequeue_top()
    if not customer_info:
        return {"status": "not_found", "message": "No customers available in queue. Queue may have been empty or item already processed."}
    
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