import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import os
from pathlib import Path

@dataclass
class Message:
    id: str
    speaker: str  # 'customer' or 'agent'
    text: str
    timestamp: str
    type: str = "message"  # 'message', 'system', etc.

class ConversationContext:
    def __init__(self, call_id: str):
        self.call_id = call_id
        self.messages: List[Message] = []
        self.start_time = datetime.utcnow().isoformat()
        
    def add_message(self, speaker: str, text: str) -> None:
        """Add a message to the conversation"""
        message = Message(
            id=f"msg_{len(self.messages)}_{datetime.utcnow().timestamp()}",
            speaker=speaker,
            text=text,
            timestamp=datetime.utcnow().isoformat()
        )
        self.messages.append(message)
        
        # Keep only the last 20 messages to prevent memory bloat
        if len(self.messages) > 20:
            self.messages = self.messages[-20:]
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get the most recent messages"""
        return self.messages[-limit:]
    
    def get_full_context(self) -> str:
        """Get formatted conversation context for AI"""
        if not self.messages:
            return "No conversation history yet."
        
        context = "Conversation History (most recent first):\n"
        for msg in self.get_recent_messages():
            context += f"[{msg.timestamp}] {msg.speaker}: {msg.text}\n"
        
        return context

# Global storage for conversation contexts (in production, this would be in Redis or DB)
conversation_states: Dict[str, ConversationContext] = {}

def get_context(call_id: str) -> ConversationContext:
    """Get or create a conversation context for a call"""
    if call_id not in conversation_states:
        conversation_states[call_id] = ConversationContext(call_id)
    return conversation_states[call_id]

def clear_context(call_id: str) -> None:
    """Clear conversation context when call ends"""
    if call_id in conversation_states:
        del conversation_states[call_id]