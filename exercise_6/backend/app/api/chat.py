"""
Exercise 6: Chat API Routes
Handles chat interactions and conversation management
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from app.services.rag.rag_service import rag_service

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

# Mock conversation storage
mock_conversations = {}
mock_messages = []

@router.post("/")
async def send_message(chat_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send a message and get AI response"""
    message = chat_data.get("message", "")
    session_id = chat_data.get("session_id") # Can be None for new sessions
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # For now, we are not handling conversation history.
    # A real implementation would fetch history from the database based on session_id.
    conversation_history = []

    # Get the RAG response
    rag_response = await rag_service.chat_with_rag(
        query=message,
        conversation_history=conversation_history
    )

    # If no session_id is provided, create a new one
    if not session_id:
        session_id = str(uuid.uuid4())

    # In a real app, you would store the user message and the AI response in the database
    # For this exercise, we are focusing on the RAG response generation.
    
    # The rag_response already has a structure that is very close to what we need.
    # We can adapt it slightly for the final API response.
    return {
        "status": "success",
        "data": {
            "id": rag_response.get("id"),
            "message": message,
            "response": rag_response.get("response"),
            "sources": rag_response.get("sources", []),
            "qa_matches": rag_response.get("qa_matches", []),
            "timestamp": rag_response.get("timestamp"),
            "processing_time_ms": rag_response.get("processing_time_ms"),
            "model_used": rag_response.get("model_used"),
            "session_id": session_id
        }
    }

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
) -> Dict[str, Any]:
    """Get chat history for a session"""
    if session_id not in mock_conversations:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages for this session
    session_messages = [
        msg for msg in mock_messages 
        if msg.get("session_id") == session_id
    ]
    
    # Apply pagination
    paginated_messages = session_messages[offset:offset + limit]
    
    return {
        "status": "success",
        "data": {
            "session_id": session_id,
            "messages": paginated_messages,
            "total_messages": len(session_messages),
            "conversation": mock_conversations[session_id]
        }
    }

@router.get("/sessions")
async def list_chat_sessions(
    limit: Optional[int] = 20,
    offset: Optional[int] = 0
) -> Dict[str, Any]:
    """List all chat sessions"""
    sessions = list(mock_conversations.values())
    
    # Sort by updated_at descending
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    
    # Apply pagination
    paginated_sessions = sessions[offset:offset + limit]
    
    return {
        "status": "success",
        "data": paginated_sessions,
        "total": len(sessions),
        "limit": limit,
        "offset": offset
    }

@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str) -> Dict[str, Any]:
    """Delete a chat session and all its messages"""
    if session_id not in mock_conversations:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Remove session
    del mock_conversations[session_id]
    
    # Remove all messages for this session
    global mock_messages
    mock_messages = [
        msg for msg in mock_messages 
        if msg.get("session_id") != session_id
    ]
    
    return {
        "status": "success",
        "message": f"Session {session_id} deleted successfully"
    }

@router.post("/feedback")
async def submit_chat_feedback(feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """Submit feedback for a chat response"""
    message_id = feedback_data.get("message_id")
    rating = feedback_data.get("rating")  # 1-5 stars
    comment = feedback_data.get("comment", "")
    
    if not message_id or not rating:
        raise HTTPException(status_code=400, detail="Message ID and rating are required")
    
    # In a real implementation, this would be stored in a database
    feedback = {
        "id": str(uuid.uuid4()),
        "message_id": message_id,
        "rating": rating,
        "comment": comment,
        "submitted_at": datetime.utcnow().isoformat()
    }
    
    return {
        "status": "success",
        "message": "Feedback submitted successfully",
        "data": feedback
    }