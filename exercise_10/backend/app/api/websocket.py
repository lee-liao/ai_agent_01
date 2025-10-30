from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Optional, List
import json
from datetime import datetime
import asyncio

# Import VAD service for smart audio chunking
from .vad_service import (
    calculate_audio_energy,
    is_speech_detected,
    is_silence_detected,
    should_process_audio_chunk,
    accumulate_audio_chunk as vad_accumulate_audio_chunk,
    process_audio_buffer as vad_process_audio_buffer
)

router = APIRouter(tags=["WebSocket"])

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
# Agent queue subscribers (agent call_id -> True)
agent_queue_subscribers: Dict[str, bool] = {}

# Audio buffers for transcription (call_id -> bytearray)
audio_buffers: Dict[str, bytearray] = {}

# Audio energy levels for VAD (call_id -> list of recent energy levels)
audio_energy_levels: Dict[str, List[float]] = {}

# Last processing times for VAD (call_id -> last processing timestamp)
audio_processing_times: Dict[str, float] = {}

# Buffer size: 4 seconds of audio - balancing responsiveness with transcription quality
BUFFER_SIZE_SECONDS = 4

# Services
from ..config import settings
from .whisper_service import transcribe_audio
from .ai_service import generate_suggestion
from .context_manager import get_context

import io
import wave
# No longer need pydub - using Python's wave module instead!

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
    audio_energy_levels[call_id] = []     # Initialize energy levels for VAD
    audio_processing_times[call_id] = 0.0 # Initialize last processing time

    print(f"✅ WebSocket connected: {call_id}")
    
    try:
        while True:
            # Receive data from client
            try:
                data = await websocket.receive()
            except RuntimeError as e:
                if "Cannot call" in str(e) and "disconnect message" in str(e):
                    print(f"ℹ️ WebSocket {call_id} already disconnected: {e}")
                    break
                else:
                    print(f"❌ Unexpected RuntimeError for {call_id}: {e}")
                    raise
            
            if "bytes" in data:
                # Audio data received
                audio_chunk = data["bytes"]
                # print(f"📊 Received audio chunk: {len(audio_chunk)} bytes from {call_id}")
                
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

                # Accumulate audio chunk for smart transcription processing with VAD
                # Instead of processing individual chunks, accumulate them for better accuracy
                should_process = await accumulate_audio_data(call_id, audio_chunk)
                
                # Process accumulated audio buffer if VAD indicates it's time
                if should_process:
                    audio_data = await process_audio_buffer(call_id)
                    if audio_data and len(audio_data) > 0:
                        # Process accumulated audio with timestamp
                        asyncio.create_task(
                            transcribe_and_broadcast(
                                call_id, 
                                audio_data,  # Process the accumulated buffer
                                speaker, 
                                websocket, 
                                partner_call_id
                            )
                        )
                    else:
                        print(f"⚠️ No accumulated audio data to process for {call_id}")
                else:
                    # For immediate feedback, also process small chunks (optional, can be removed for cleaner approach)
                    # This maintains the responsive feel while building up to smarter chunks
                    pass  # Removed debug logging for production
                
            elif "text" in data:
                # Control message received
                message = json.loads(data["text"])
#                 print(f"📡 [WS-{call_id}] Received message type: {message['type']}")

                if message["type"] == "start_call":
                    print(f"▶️ Call started: {call_id}")
                    await handle_start_call(call_id, message, websocket)

                elif message["type"] == "end_call":
                    print(f"⏹️ Call ended: {call_id}, user_type: {message.get('user_type', 'unknown')}")
                    from .calls import active_conversations as active_calls
#                     print(f"📋 [DEBUG] Active conversations before end_call: {dict(active_calls)}")
                    user_type = message.get("user_type")
                    await handle_end_call(call_id, message, websocket)
#                     print(f"📋 [DEBUG] Active conversations after end_call: {dict(active_calls)}")
                    if user_type != 'agent':
                        # Only close WebSocket connection for non-agents (customers)
                        return
                    # For agents, continue listening for more messages (like pickup requests)

                elif message["type"] == "subscribe_queue":
                    # Mark this agent connection as a queue subscriber and send initial snapshot
                    agent_queue_subscribers[call_id] = True
                    try:
                        from .calls import waiting_customers
#                         print(f"[WS] Agent {call_id} subscribed; waiting count={len(waiting_customers)}")
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
#                     print(f"📥 [WS-{call_id}] Pickup requested for account: {account_number}")
                    if not account_number:
                        result = await try_pickup_top(agent_call_id=call_id)
                    else:
                        result = await try_pickup_customer(agent_call_id=call_id, account_number=account_number)
#                     print(f"[WS-{call_id}] Pickup result for {account_number}: {result}")
                    await websocket.send_json({"type": "pickup_result", **result})
                    # If success, notify both ends of conversation start and send customer context to agent
                    if result.get("status") == "success":
#                         print(f"✅ [WS-{call_id}] Successful pickup, sending conversation_started")
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
#                         print(f"📋 [WS-{call_id}] Sending queue update after successful pickup")
                        await send_queue_update(target_ws=websocket)
                        
                        customer_call_id = result.get("customer_call_id")
                        if customer_call_id and customer_call_id in active_connections:
                            try:
                                await active_connections[customer_call_id].send_json({
                                    "type": "conversation_started",
                                    "call_id": customer_call_id,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
#                                 print(f"✅ [WS-{call_id}] Sent conversation_started to customer {customer_call_id}")
                            except Exception as e:
                                print(f"❌ Failed to send conversation_started to {customer_call_id}: {e}")
                    else:
                         print(f"❌ [WS-{call_id}] Pickup failed for {account_number}")

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
#         print(f"🧹 [finally] Starting cleanup for call_id: {call_id}")
        # If an active conversation exists for this call_id, notify partner before cleanup
        try:
            from .calls import active_conversations as active_calls
            partner_call_id = None
            keys_to_delete = []
            
            # Find the conversation that contains this call_id - this might be stored as key or in the data
            # First, find the conversation that has this call_id
            target_conversation = None
            conversation_keys = []
            
            for active_key, call_info in list(active_calls.items()):
                if call_id == active_key or call_id == call_info.get("agent_call_id") or call_id == call_info.get("customer_call_id"):
                    # This call_id is part of this conversation
                    if call_info.get("agent_call_id") and call_info.get("customer_call_id"):
                        # This is a matched conversation with both parties
                        # Find all entries that represent the same logical conversation
                        target_conversation = call_info
                        # Add this key to potential deletions
                        conversation_keys.append(active_key)
                        # Also get the partner if not already set
                        if not partner_call_id:
                            if call_id == call_info.get("agent_call_id"):
                                partner_call_id = call_info.get("customer_call_id")
                            elif call_id == call_info.get("customer_call_id"):
                                partner_call_id = call_info.get("agent_call_id")
                    elif call_info.get("customer_call_id") == active_key and not call_info.get("agent_call_id"):
                        # This looks like a customer-side entry that might be part of the same conversation
                        # Check if it's part of the same logical conversation as others
                        conversation_keys.append(active_key)
            
            # Now identify all keys that belong to the same conversation
            if target_conversation and target_conversation.get("agent_call_id") and target_conversation.get("customer_call_id"):
                # Find all entries that relate to this specific agent-customer pairing
                agent_call_id = target_conversation["agent_call_id"]
                customer_call_id = target_conversation["customer_call_id"]
                
                for active_key, call_info in list(active_calls.items()):
                    # Check if this entry is part of the same conversation
                    if (active_key == agent_call_id or 
                        active_key == customer_call_id or
                        call_info.get("agent_call_id") == agent_call_id or 
                        call_info.get("customer_call_id") == customer_call_id):
                        keys_to_delete.append(active_key)
            else:
                # If we couldn't identify a clear conversation, just remove entries that directly match
                for active_key, call_info in list(active_calls.items()):
                    if call_id == active_key or call_id == call_info.get("agent_call_id") or call_id == call_info.get("customer_call_id"):
                        keys_to_delete.append(active_key)
                        # Set partner if not already set
                        if not partner_call_id:
                            if call_id == call_info.get("agent_call_id"):
                                partner_call_id = call_info.get("customer_call_id")
                            elif call_id == call_info.get("customer_call_id"):
                                partner_call_id = call_info.get("agent_call_id")

            # Remove all related conversation entries
            for key_to_delete in set(keys_to_delete):  # Use set to avoid duplicates
#                 print(f"[cleanup] Deleting active conversation with key: {key_to_delete} for call_id: {call_id}")
                try:
                    del active_calls[key_to_delete]
#                     print(f"🧹 [cleanup] Successfully removed {key_to_delete} from active_conversations")
                except Exception as e:
                     print(f"❌ [cleanup] Error removing active conversation: {e}")
            
            # Notify partner if connected
            if partner_call_id and partner_call_id in active_connections:
                try:
                    await active_connections[partner_call_id].send_json({
                        "type": "conversation_ended",
                        "call_id": partner_call_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
#                     print(f"✅ [cleanup] Sent conversation_ended to partner {partner_call_id}")
                except Exception as e:
                     print(f"❌ [cleanup] Error sending conversation_ended to partner: {e}")
            else:
                 print(f"ℹ️ [cleanup] No partner found for {call_id}, partner_call_id: {partner_call_id}")
                
        except Exception as e:
#             print(f"❌ [cleanup] Exception in main cleanup: {e}")
            import traceback
            traceback.print_exc()
        # Cleanup connection maps
        if call_id in active_connections:
            del active_connections[call_id]
#             print(f"🧹 [cleanup] Removed {call_id} from active_connections")
        if call_id in agent_queue_subscribers:
            del agent_queue_subscribers[call_id]
#             print(f"🧹 [cleanup] Removed {call_id} from agent_queue_subscribers")
        if call_id in audio_buffers:
            del audio_buffers[call_id]
#             print(f"🧹 [cleanup] Removed {call_id} from audio_buffers")
        if call_id in audio_energy_levels:
            del audio_energy_levels[call_id]
#             print(f"🧹 [cleanup] Removed {call_id} from audio_energy_levels")
        if call_id in audio_processing_times:
            del audio_processing_times[call_id]
#             print(f"🧹 [cleanup] Removed {call_id} from audio_processing_times")
        # Cleanup conversation context
        from .context_manager import clear_context
        clear_context(call_id)
#         print(f"🧹 [cleanup] Cleared context for {call_id}")

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
    keys_to_delete = []
    
    # Find the conversation that contains this call_id - this might be stored as key or in the data
    # First, find the conversation that has this call_id
    target_conversation = None
    conversation_keys = []
    
    for active_key, call_info in list(active_calls.items()):
        if call_id == active_key or call_id == call_info.get("agent_call_id") or call_id == call_info.get("customer_call_id"):
            # This call_id is part of this conversation
            if call_info.get("agent_call_id") and call_info.get("customer_call_id"):
                # This is a matched conversation with both parties
                # Find all entries that represent the same logical conversation
                target_conversation = call_info
                # Add this key to potential deletions
                conversation_keys.append(active_key)
                # Also get the partner if not already set
                if not partner_call_id:
                    if call_id == call_info.get("agent_call_id"):
                        partner_call_id = call_info.get("customer_call_id")
                    elif call_id == call_info.get("customer_call_id"):
                        partner_call_id = call_info.get("agent_call_id")
            elif call_info.get("customer_call_id") == active_key and not call_info.get("agent_call_id"):
                # This looks like a customer-side entry that might be part of the same conversation
                # Check if it's part of the same logical conversation as others
                conversation_keys.append(active_key)
    
    # Now identify all keys that belong to the same conversation
    if target_conversation and target_conversation.get("agent_call_id") and target_conversation.get("customer_call_id"):
        # Find all entries that relate to this specific agent-customer pairing
        agent_call_id = target_conversation["agent_call_id"]
        customer_call_id = target_conversation["customer_call_id"]
        
        for active_key, call_info in list(active_calls.items()):
            # Check if this entry is part of the same conversation
            if (active_key == agent_call_id or 
                active_key == customer_call_id or
                call_info.get("agent_call_id") == agent_call_id or 
                call_info.get("customer_call_id") == customer_call_id):
                keys_to_delete.append(active_key)
    else:
        # If we couldn't identify a clear conversation, just remove entries that directly match
        for active_key, call_info in list(active_calls.items()):
            if call_id == active_key or call_id == call_info.get("agent_call_id") or call_id == call_info.get("customer_call_id"):
                keys_to_delete.append(active_key)
                # Set partner if not already set
                if not partner_call_id:
                    if call_id == call_info.get("agent_call_id"):
                        partner_call_id = call_info.get("customer_call_id")
                    elif call_id == call_info.get("customer_call_id"):
                        partner_call_id = call_info.get("agent_call_id")

    # Remove all related conversation entries
    for key_to_delete in set(keys_to_delete):  # Use set to avoid duplicates
#         print(f"[handle_end_call] Deleting active conversation with key: {key_to_delete} for call_id: {call_id}")
        try:
            del active_calls[key_to_delete]
#             print(f"🧹 [handle_end_call] Successfully removed {key_to_delete} from active_conversations")
        except Exception as e:
#             print(f"❌ [handle_end_call] Error removing active conversation: {e}")
            pass
    
    # Notify partner if connected
    if partner_call_id and partner_call_id in active_connections:
        try:
            await active_connections[partner_call_id].send_json({
                "type": "conversation_ended",
                "call_id": partner_call_id,
                "timestamp": datetime.utcnow().isoformat()
            })
#             print(f"✅ [handle_end_call] Sent conversation_ended to partner {partner_call_id}")
        except Exception as e:
#             print(f"❌ [handle_end_call] Error sending conversation_ended to partner {partner_call_id}: {e}")
            pass
    else:
#         print(f"ℹ️ [handle_end_call] No partner found for {call_id}, partner_call_id: {partner_call_id}")
        pass
        
    if not keys_to_delete:
#         print(f"ℹ️ [handle_end_call] Call {call_id} not in active conversations, removing from waiting queue")
        # Not in active conversation: remove from waiting (Redis) and available list
        removed_waiting = False
        removed_agents = False
        # Try Redis removal first
        try:
            from .queue_service import remove_from_queue as _rm
            await _rm(call_id)
            removed_waiting = True
#             print(f"🧹 [handle_end_call] Removed {call_id} from waiting queue")
        except Exception as e:
#             print(f"❌ [handle_end_call] Error removing from waiting queue: {e}")
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
        
        # Strategy 1: Try WebM directly (browser MediaRecorder sends WebM with Opus codec)
        # This works as proven by the test page!
        try:
            print(f"   Trying WebM format first...")
            transcript = await transcribe_audio(audio_data, "audio.webm")
            
            if transcript:
                print(f"✅ Transcription successful (WebM) for {speaker}: {transcript[:50]}...")
                return transcript
            else:
                print(f"   WebM returned no result, trying WAV conversion...")
        except Exception as webm_error:
            print(f"   WebM failed: {webm_error}, trying WAV conversion...")
        
        # Strategy 2: If WebM fails, try converting to WAV
        # (This assumes the data might be raw PCM)
        try:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)      # Mono
                wav_file.setsampwidth(2)      # 16-bit (2 bytes per sample)
                wav_file.setframerate(16000)  # 16kHz sample rate
                wav_file.writeframes(audio_data)
            
            wav_buffer.seek(0)
            
            # Call Whisper API with WAV format
            transcript = await transcribe_audio(wav_buffer.read(), "audio.wav")
            
            if transcript:
                print(f"✅ Transcription successful (WAV) for {speaker}: {transcript[:50]}...")
                return transcript
            else:
                print(f"⚠️ No transcription result for {speaker}")
                return None
                
        except Exception as conversion_error:
            print(f"❌ WAV conversion also failed: {conversion_error}")
            return None
        
    except Exception as e:
        print(f"❌ Transcription error for {speaker}: {e}")
        import traceback
        traceback.print_exc()
        return None


# VAD (Voice Activity Detection) Helper Functions
async def accumulate_audio_data(call_id: str, audio_chunk: bytes) -> bool:
    """
    Accumulate audio chunk in buffer and determine if we should process it.
    Uses VAD to detect natural speech boundaries for smart chunking.
    
    Args:
        call_id: Call identifier
        audio_chunk: Incoming audio data
        
    Returns:
        True if the accumulated buffer should be processed for transcription
    """
    try:
        # Initialize buffers if needed
        if call_id not in audio_buffers:
            audio_buffers[call_id] = bytearray()
        if call_id not in audio_energy_levels:
            audio_energy_levels[call_id] = []
        if call_id not in audio_processing_times:
            audio_processing_times[call_id] = 0.0
            
        # Get current time
        current_time = asyncio.get_event_loop().time()
        
        # Calculate energy level for VAD
        energy_level = calculate_audio_energy(audio_chunk)
        
        # Store energy level for silence detection
        audio_energy_levels[call_id].append(energy_level)
        # Keep only recent energy levels to avoid memory issues
        if len(audio_energy_levels[call_id]) > 100:  # Keep last 100 samples
            audio_energy_levels[call_id] = audio_energy_levels[call_id][-100:]
        
        # Add chunk to buffer
        audio_buffers[call_id].extend(audio_chunk)
        total_buffer = len(audio_buffers[call_id])
        print(f"📊 Audio buffer: {total_buffer:,} bytes ({total_buffer/32000:.2f}s of audio) for {call_id}")
        
        # Check if we should process the accumulated buffer
        # Strategy: Balance between enough audio for accuracy and responsive feedback
        
        # Calculate time since last processing
        time_since_last = (current_time - audio_processing_times.get(call_id, 0.0)) * 1000  # ms
        
        # Minimum buffer requirements (more lenient now)
        min_buffer_size = 32000 * 2  # 2 seconds at 16kHz, 16-bit = 64,000 bytes
        max_wait_time_ms = 8000  # Process after 8 seconds regardless
        
        # Check if we have enough audio accumulated
        if len(audio_buffers[call_id]) < min_buffer_size:
            # Don't process yet - not enough audio accumulated
            print(f"   ⏳ Waiting for more audio... ({total_buffer}/{min_buffer_size} bytes, {total_buffer/min_buffer_size*100:.1f}%)")
            return False
        
        print(f"   ✅ Minimum buffer size reached! Checking VAD...")
        
        # Force processing if we've been waiting too long (prevents stuck buffers)
        if time_since_last >= max_wait_time_ms:
            print(f"   ⏰ Max wait time reached ({time_since_last:.0f}ms), forcing transcription!")
            return True
        
        # Otherwise, check VAD for natural speech boundaries
        should_process = should_process_audio_chunk(
            call_id, 
            current_time, 
            audio_energy_levels[call_id], 
            audio_processing_times.get(call_id, 0.0),
            4000  # 4 second chunks for balance between accuracy and responsiveness
        )
        
        return should_process
        
    except Exception as e:
        print(f"❌ Error accumulating audio chunk for {call_id}: {e}")
        return False


async def process_audio_buffer(call_id: str) -> bytes:
    """
    Process the accumulated audio buffer and return the audio data for transcription.
    Clears the buffer after processing.
    
    Args:
        call_id: Call identifier
        
    Returns:
        Audio data for transcription
    """
    try:
        if call_id not in audio_buffers:
            return b""
        
        # Get the accumulated audio data
        audio_data = bytes(audio_buffers[call_id])
        
        # Clear the buffer
        audio_buffers[call_id].clear()
        
        # Update the last processed timestamp
        audio_processing_times[call_id] = asyncio.get_event_loop().time()
        
        # Clear energy levels for this buffer
        if call_id in audio_energy_levels:
            audio_energy_levels[call_id].clear()
        
        print(f"🎵 Processing accumulated audio buffer: {len(audio_data)} bytes for {call_id}")
        return audio_data
        
    except Exception as e:
        print(f"❌ Error processing audio buffer for {call_id}: {e}")
        return b""


# Audio Buffer Management Functions
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
        
#         print(f"📝 Transcription result for {speaker}: {text[:50]}...")
        
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
#             print(f"📤 Sent transcript to sender ({speaker}): {text[:30]}...")
        except Exception as e:
            print(f"❌ Error sending transcript to sender: {e}")

        # Send to partner
        if partner_call_id and partner_call_id in active_connections:
            try:
                await active_connections[partner_call_id].send_json(transcript_msg)
#                 print(f"📤 Sent transcript to partner: {text[:30]}...")
            except Exception as e:
                print(f"❌ Error sending transcript to partner: {e}")
                # Remove dead connection
                if partner_call_id in active_connections:
                    del active_connections[partner_call_id]

        # Generate AI suggestion for agent when customer speaks
        # (keeping the same pattern from the original code)
        from .ai_service import generate_suggestion
        if speaker == "customer" and partner_call_id and partner_call_id in active_connections:
#             print(f"💡 Generating AI suggestion for agent {partner_call_id} based on customer message: {text[:50]}...")
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
#                 print(f"🤖 Sent AI suggestion to agent {partner_call_id}: {suggestion.get('suggestion', '')[:30]}...")
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
    
#     print(f"📝 Transcript received from {call_id} (speaker: {speaker}): {text[:50]}...")
    
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
#         print(f"💡 Generating AI suggestion for agent {partner_call_id} based on customer message: {text[:50]}...")
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
#             print(f"🤖 Sent AI suggestion to agent {partner_call_id}: {suggestion.get('suggestion', '')[:30]}...")
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