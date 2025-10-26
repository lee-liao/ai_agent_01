from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import asyncio
from .queue_service import (
    enqueue_waiting_customer,
    dequeue_top,
    dequeue_by_account_number,
    remove_from_queue,
    get_waiting_count,
    get_queue_position,
    find_call_id_by_account,
)

router = APIRouter(prefix="/api/calls", tags=["Calls"])

# In-memory storage for active conversations and available agents (queue is Redis-backed)
active_conversations: dict = {}  # agent_call_id -> {agent_call_id, customer_call_id, agent_name, customer_name, account_number, started_at, status}
available_agents: list = []  # [{agent_name, call_id, timestamp}]

# Concurrency lock for queue operations (best-effort; Redis recommended for prod)
queue_lock: asyncio.Lock = asyncio.Lock()

class StartCallRequest(BaseModel):
    user_type: str  # "agent" or "customer"
    user_name: str
    account_number: Optional[str] = None  # provided by customer
    target_account_number: Optional[str] = None  # agent picks specific customer
    available: Optional[bool] = True  # when False, agent monitors queue without becoming available

class CallResponse(BaseModel):
    call_id: str
    status: str
    message: str
    matched: bool = False
    partner_name: Optional[str] = None

@router.post("/start", response_model=CallResponse)
async def start_call(request: StartCallRequest):
    """
    Start a new call session
    Agent or customer requests to start a call
    If match found, return call_id and partner info
    Otherwise, add to waiting queue
    """
    call_id = f"call_{uuid.uuid4().hex[:12]}"
    
    if request.user_type == "customer":
        # Customer wants to connect - check if any agents available
        if available_agents:
            # Match with first available agent
            agent_info = available_agents.pop(0)
            
            # Create active conversation session
            active_conversations[call_id] = {
                "agent_call_id": agent_info["call_id"],
                "customer_call_id": call_id,
                "agent_name": agent_info["agent_name"],
                "customer_name": request.user_name,
                "account_number": request.account_number,
                "started_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            return CallResponse(
                call_id=call_id,
                status="matched",
                message=f"Connected to agent {agent_info['agent_name']}",
                matched=True,
                partner_name=agent_info["agent_name"]
            )
        else:
            # No agents available - ensure single active/queued chat per customer/account
            if request.account_number:
                # Guard 1: active conversation already exists
                for _, conv in active_conversations.items():
                    if conv.get("account_number") == request.account_number or conv.get("customer_name") == request.user_name:
                        return CallResponse(
                            call_id=call_id,
                            status="duplicate",
                            message="You already have an active conversation.",
                            matched=False
                        )
                # Guard 2: queued item already exists in Redis
                existing_cid = await find_call_id_by_account(request.account_number)
                if existing_cid:
                    return CallResponse(
                        call_id=existing_cid,
                        status="duplicate",
                        message="You already have a pending request in the queue.",
                        matched=False
                    )
            # Add to Redis-backed queue
            await enqueue_waiting_customer(request.user_name, request.account_number, call_id)
            # Notify subscribed agents of new waiting customer
            try:
                from .websocket import broadcast_queue_update
                # Fire and forget; if it fails, continue
                import asyncio as _asyncio
                _asyncio.create_task(broadcast_queue_update())
            except Exception:
                pass

            return CallResponse(
                call_id=call_id,
                status="waiting",
                message="Waiting for available agent...",
                matched=False
            )
    
    elif request.user_type == "agent":
        # If agent specified a target account, try to match that first (Redis-backed)
        if request.target_account_number:
            customer_info = await dequeue_by_account_number(request.target_account_number)
            if customer_info:
                active_conversations[call_id] = {
                    "agent_call_id": call_id,
                    "customer_call_id": customer_info["call_id"],
                    "agent_name": request.user_name,
                    "customer_name": customer_info.get("customer_name"),
                    "account_number": customer_info.get("account_number"),
                    "started_at": datetime.utcnow().isoformat(),
                    "status": "active"
                }
                # Update queue and notify customer
                try:
                    from .websocket import broadcast_queue_update, broadcast_to_call
                    import asyncio as _asyncio
                    _asyncio.create_task(broadcast_queue_update())
                    _asyncio.create_task(broadcast_to_call(customer_info["call_id"], {
                        "type": "conversation_started",
                        "call_id": customer_info["call_id"],
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                except Exception:
                    pass
                return CallResponse(
                    call_id=call_id,
                    status="matched",
                    message=f"Connected to customer {customer_info.get('customer_name')}",
                    matched=True,
                    partner_name=customer_info.get("customer_name")
                )

        # If agent is monitoring only, do not auto-match or mark available
        if request.available is False:
            return CallResponse(
                call_id=call_id,
                status="monitoring",
                message="Monitoring waiting queue...",
                matched=False
            )

        # Match with first waiting customer (Redis-backed)
        customer_info = await dequeue_top()
        if customer_info:
            active_conversations[call_id] = {
                "agent_call_id": call_id,
                "customer_call_id": customer_info["call_id"],
                "agent_name": request.user_name,
                "customer_name": customer_info.get("customer_name"),
                "account_number": customer_info.get("account_number"),
                "started_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            try:
                from .websocket import broadcast_queue_update, broadcast_to_call
                import asyncio as _asyncio
                _asyncio.create_task(broadcast_queue_update())
                _asyncio.create_task(broadcast_to_call(customer_info["call_id"], {
                    "type": "conversation_started",
                    "call_id": customer_info["call_id"],
                    "timestamp": datetime.utcnow().isoformat()
                }))
            except Exception:
                pass
            return CallResponse(
                call_id=call_id,
                status="matched",
                message=f"Connected to customer {customer_info.get('customer_name')}",
                matched=True,
                partner_name=customer_info.get("customer_name")
            )
        else:
            # No customers waiting - mark agent as available
            available_agents.append({
                "agent_name": request.user_name,
                "call_id": call_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return CallResponse(
                call_id=call_id,
                status="waiting",
                message="Waiting for customer...",
                matched=False
            )
    
    raise HTTPException(status_code=400, detail="Invalid user_type")

@router.get("/status/{call_id}")
async def get_call_status(call_id: str):
    """Get current status of a call"""
    
    # Check if in active conversations
    for active_conv_id, conv_info in active_conversations.items():
        if call_id in [conv_info.get("agent_call_id"), conv_info.get("customer_call_id")]:
            return {
                "status": "active",
                "conversation": conv_info
            }
    
    # Check if in waiting queue (Redis-backed)
    pos = await get_queue_position(call_id)
    if pos is not None:
        total = await get_waiting_count()
        return {
            "status": "waiting",
            "queue_position": pos,
            "total_waiting": total
        }
    
    for agent in available_agents:
        if agent["call_id"] == call_id:
            total = await get_waiting_count()
            return {
                "status": "available",
                "waiting_customers": total
            }
    
    return {"status": "not_found"}

@router.post("/end/{call_id}")
async def end_call(call_id: str):
    """End a call session"""
    
    # Remove from active conversations
    call_to_remove = None
    for active_conv_id, conv_info in active_conversations.items():
        if call_id in [conv_info.get("agent_call_id"), conv_info.get("customer_call_id")]:
            call_to_remove = active_conv_id
            break
    
    if call_to_remove:
        del active_conversations[call_to_remove]
        return {"status": "ended", "message": "Call ended successfully"}
    
    # Remove from waiting queue (Redis) and available list
    try:
        await remove_from_queue(call_id)
    except Exception:
        pass
    available_agents[:] = [a for a in available_agents if a["call_id"] != call_id]
    
    return {"status": "ended", "message": "Removed from queue"}

@router.get("/stats")
async def get_call_stats():
    """Get current call center statistics"""
    total_waiting = 0
    try:
        total_waiting = await get_waiting_count()
    except Exception:
        total_waiting = 0
    return {
        "active_conversations": len(active_conversations),
        "waiting_customers": total_waiting,
        "available_agents": len(available_agents),
        "active_conversation_details": list(active_conversations.values())
    }

@router.get("/match/{call_id}")
async def get_partner_call_id(call_id: str):
    """Get the partner's call_id for routing messages"""
    for active_conv_id, conv_info in active_conversations.items():
        if call_id == conv_info.get("agent_call_id"):
            return {
                "partner_call_id": conv_info.get("customer_call_id"),
                "partner_name": conv_info.get("customer_name"),
                "partner_type": "customer"
            }
        elif call_id == conv_info.get("customer_call_id"):
            return {
                "partner_call_id": conv_info.get("agent_call_id"),
                "partner_name": conv_info.get("agent_name"),
                "partner_type": "agent"
            }
    
    raise HTTPException(status_code=404, detail="Call not found or not matched")


@router.get("/queue/health")
async def queue_health():
    """Verify Redis queue connectivity and basic stats"""
    try:
        r = get_redis()
        pong = await r.ping()
        count = await get_waiting_count()
        return {
            "connected": True,
            "pong": bool(pong),
            "waiting_customers": count,
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
        }

