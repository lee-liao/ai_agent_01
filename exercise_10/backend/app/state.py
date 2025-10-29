from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, List, Any

# In-memory conversation state and suggestion queues
_conversations: Dict[str, List[dict]] = {}
_suggestion_queues: Dict[str, asyncio.Queue] = {}


def append_transcript(call_id: str, speaker: str, text: str, timestamp: str | None = None) -> None:
    if call_id not in _conversations:
        _conversations[call_id] = []
    _conversations[call_id].append({
        "speaker": speaker,
        "text": text,
        "timestamp": timestamp or datetime.utcnow().isoformat()
    })


def get_conversation(call_id: str) -> List[dict]:
    return _conversations.get(call_id, [])


def get_or_create_queue(call_id: str) -> asyncio.Queue:
    if call_id not in _suggestion_queues:
        _suggestion_queues[call_id] = asyncio.Queue()
    return _suggestion_queues[call_id]


async def enqueue_suggestion(call_id: str, payload: Dict[str, Any]) -> None:
    queue = get_or_create_queue(call_id)
    await queue.put(payload)


def _basic_rule_suggestion(last_user_text: str, history: List[dict]) -> str:
    text = last_user_text.lower()
    if "refund" in text:
        return "Apologize for the inconvenience and explain the refund process. Ask for the order number."
    if "order" in text or "tracking" in text:
        return "Ask for the order number and check recent order status. Offer expedited support if delayed."
    if "billing" in text or "charge" in text or "invoice" in text:
        return "Clarify the billing issue, verify recent charges, and offer to send a detailed invoice."
    if "account" in text or "login" in text or "locked" in text:
        return "Guide the customer through account recovery and verify identity. Offer password reset."
    if "upgrade" in text or "plan" in text or "pricing" in text:
        return "Explain plan differences and recommend an upgrade based on stated needs."
    # Fallback using brief empathy + probe
    return "Acknowledge the concern, ask a clarifying question, and offer the next best action."


async def generate_and_enqueue_suggestion(call_id: str, trigger_speaker: str) -> None:
    # Only generate suggestions for agent when customer speaks
    if trigger_speaker != "customer":
        return
    history = get_conversation(call_id)
    if not history:
        return
    # Find last customer message
    last_msg = next((m for m in reversed(history) if m.get("speaker") == "customer" and m.get("text")), None)
    if not last_msg:
        return
    suggestion_text = _basic_rule_suggestion(last_msg["text"], history)
    await enqueue_suggestion(call_id, {
        "type": "text",
        "content": suggestion_text,
        "timestamp": datetime.utcnow().isoformat()
    })


