"""
Safety guardrails for the Child Growth Assistant.
Classifies requests as in-scope or out-of-scope and provides appropriate refusal templates.
Includes HITL (Human-In-The-Loop) queue for sensitive cases requiring human oversight.
"""

import json
import time
import uuid
import re
from pathlib import Path
from typing import Tuple, Dict, Optional, List
from datetime import datetime
from app.observability import get_tracer


class SafetyGuard:
    """Guard to check if requests are safe and in-scope."""
    
    def __init__(self, policy_path: str = None):
        """Initialize with safety policy configuration."""
        if policy_path is None:
            # Default: look for config in parent directory (exercise_11/config/)
            backend_dir = Path(__file__).parent.parent.parent
            policy_path = backend_dir / "config" / "safety_policy.json"
        else:
            policy_path = Path(policy_path)
        
        if Path(policy_path).exists():
            with open(policy_path) as f:
                self.policy = json.load(f)
        else:
            # Fallback to default policy if file not found
            self.policy = {
                "medical_keywords": ["diagnose", "adhd", "autism", "fever", "symptoms"],
                "crisis_keywords": ["hurt", "suicide", "abuse", "danger", "afraid"],
                "legal_keywords": ["custody", "divorce", "lawyer", "court"],
                "therapy_keywords": ["depression", "anxiety", "trauma", "therapist"],
                "pii_patterns": {
                    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
                    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
                    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
                }
            }
        
        # Initialize PII detection patterns
        self.pii_patterns = {
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "address": re.compile(r"\b\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd|way|circle|cir)\b", re.IGNORECASE),
            # More strict name pattern: requires explicit "my name is" or proper name format after "I'm"
            # Avoids matching common phrases like "I'm afraid", "I'm going", etc.
            "name_pattern": re.compile(r"\b(?:my name is|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b|\b(?:i'm|i am)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b", re.IGNORECASE)
        }
    
    def classify_request(self, text: str) -> Tuple[str, Optional[Dict]]:
        """
        Classify a request as safe or out-of-scope.
        
        Returns:
            (category, refusal_data) tuple where:
            - category is 'ok', 'medical', 'crisis', 'legal', or 'therapy'
            - refusal_data is None for 'ok' or a dict with refusal template for others
        """
        tracer = get_tracer()
        start_time = time.time()
        
        with tracer.start_as_current_span("guard.check_message") as span:
            text_lower = text.lower()
            message_length = len(text)
            
            # Track attributes
            span.set_attribute("guard.message_length", message_length)
            
            matched_categories = []
            
            # Check in priority order: crisis first (most urgent), then categories
            # PII check happens after category checks to avoid false positives
            if any(kw in text_lower for kw in self.policy.get('crisis_keywords', [])):
                matched_categories.append('crisis')
                category = 'crisis'
                refusal_data = self.get_refusal_template('crisis')
            elif any(kw in text_lower for kw in self.policy.get('medical_keywords', [])):
                matched_categories.append('medical')
                category = 'medical'
                refusal_data = self.get_refusal_template('medical')
            elif any(kw in text_lower for kw in self.policy.get('therapy_keywords', [])):
                matched_categories.append('therapy')
                category = 'therapy'
                refusal_data = self.get_refusal_template('therapy')
            elif any(kw in text_lower for kw in self.policy.get('legal_keywords', [])):
                matched_categories.append('legal')
                category = 'legal'
                refusal_data = self.get_refusal_template('legal')
            else:
                # Check for PII after category checks (to avoid false positives from common phrases)
                pii_detected = self.detect_pii(text)
                if pii_detected:
                    matched_categories.append('pii')
                    category = 'pii'
                    refusal_data = None  # PII goes to HITL, not refusal
                else:
                    category = 'ok'
                    refusal_data = None
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Set classification (SAFE, BLOCKED, ESCALATE)
            # PII and crisis require HITL (ESCALATE), others are BLOCKED
            if category == 'ok':
                classification = 'SAFE'
            elif category in ['crisis', 'pii']:
                classification = 'ESCALATE'  # Requires human intervention
            else:
                classification = 'BLOCKED'
            
            # Set span attributes
            span.set_attribute("guard.classification", classification)
            span.set_attribute("guard.latency_ms", latency_ms)
            span.set_attribute("guard.primary_category", category)
            span.set_attribute("guard.matched_categories_count", len(matched_categories))
            
            if refusal_data:
                template_key = category
                span.set_attribute("guard.template_used", template_key)
            
            return (category, refusal_data)
    
    def detect_pii(self, text: str) -> bool:
        """
        Detect personally identifiable information in text.
        
        Returns:
            True if PII is detected, False otherwise
        """
        # Check for SSN
        if self.pii_patterns["ssn"].search(text):
            return True
        
        # Check for phone numbers
        if self.pii_patterns["phone"].search(text):
            return True
        
        # Check for email addresses
        if self.pii_patterns["email"].search(text):
            return True
        
        # Check for addresses
        if self.pii_patterns["address"].search(text):
            return True
        
        # Check for explicit name patterns (e.g., "My name is John Smith")
        if self.pii_patterns["name_pattern"].search(text):
            return True
        
        return False
    
    def get_refusal_template(self, category: str) -> Dict:
        """
        Get a structured refusal template with empathy, message, and resources.
        
        Returns:
            Dict with keys: empathy, message, resources (list of {text, url})
        """
        templates = {
            'medical': {
                'empathy': "I understand you're concerned about your child's health.",
                'message': "For medical questions, diagnosis, or symptoms, please consult your pediatrician or healthcare provider.",
                'resources': [
                    {
                        'text': 'Find a Pediatrician',
                        'url': 'https://www.healthychildren.org/English/tips-tools/find-pediatrician'
                    }
                ]
            },
            'crisis': {
                'empathy': "I hear you're in a difficult situation and that must be really hard.",
                'message': "Your safety and your child's safety are the top priority. Please reach out for immediate help.",
                'resources': [
                    {
                        'text': 'Call 988 - Suicide & Crisis Lifeline',
                        'url': 'tel:988'
                    },
                    {
                        'text': 'Call 1-800-422-4453 - Childhelp National Child Abuse Hotline',
                        'url': 'tel:18004224453'
                    },
                    {
                        'text': 'Call 911 - Emergency Services',
                        'url': 'tel:911'
                    }
                ]
            },
            'legal': {
                'empathy': "I understand you're dealing with challenging legal matters.",
                'message': "Legal questions require guidance from a qualified attorney who understands family law in your area.",
                'resources': [
                    {
                        'text': 'Find Legal Aid',
                        'url': 'https://www.lsc.gov/what-legal-aid/find-legal-aid'
                    }
                ]
            },
            'therapy': {
                'empathy': "It sounds like you're going through a difficult time.",
                'message': "For deeper emotional support, a licensed therapist can provide professional guidance tailored to your situation.",
                'resources': [
                    {
                        'text': 'Find a Therapist - Psychology Today',
                        'url': 'https://www.psychologytoday.com/us/therapists'
                    }
                ]
            }
        }
        
        return templates.get(category, {
            'empathy': "Thank you for reaching out.",
            'message': "I'm not able to help with that specific question.",
            'resources': []
        })


# Global guard instance
_guard_instance = None

def get_guard() -> SafetyGuard:
    """Get or create the global SafetyGuard instance."""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = SafetyGuard()
    return _guard_instance


# ============================================================================
# HITL Queue Management
# ============================================================================

# In-memory HITL queue (in production, use a database)
HITL_QUEUE: Dict[str, Dict] = {}


def create_hitl_case(
    session_id: str,
    category: str,
    user_message: str,
    conversation_history: Optional[List[Dict]] = None
) -> str:
    """
    Create a new HITL case in the queue.
    
    Args:
        session_id: Parent session ID
        category: Classification category (crisis, pii, medical, etc.)
        user_message: The user message that triggered HITL
        conversation_history: Optional conversation history
    
    Returns:
        HITL case ID
    """
    hitl_id = f"hitl_{uuid.uuid4().hex[:12]}"
    
    # Determine priority based on category
    priority = "high" if category in ["crisis", "pii"] else "medium"
    
    case = {
        "hitl_id": hitl_id,
        "session_id": session_id,
        "category": category,
        "priority": priority,
        "status": "pending",
        "user_message": user_message,
        "conversation_history": conversation_history or [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "mentor_reply": None,
        "resolved_at": None
    }
    
    HITL_QUEUE[hitl_id] = case
    
    # Notify mentor queue via SSE about new case (fire and forget)
    try:
        from app.sse_manager import sse_manager
        import asyncio
        
        # Try to get running event loop
        try:
            loop = asyncio.get_running_loop()
            # Schedule task if loop is running
            asyncio.create_task(sse_manager.send_to_session("mentor_queue", {
                "type": "new_case",
                "case": case
            }))
        except RuntimeError:
            # No running loop, create new one (for sync contexts)
            asyncio.run(sse_manager.send_to_session("mentor_queue", {
                "type": "new_case",
                "case": case
            }))
    except Exception:
        pass  # SSE not critical, fail silently
    
    return hitl_id


def get_hitl_queue(status: Optional[str] = "pending") -> List[Dict]:
    """
    Get HITL queue items filtered by status.
    
    Args:
        status: Filter by status (pending, in_progress, resolved)
    
    Returns:
        List of HITL cases
    """
    if status:
        items = [case for case in HITL_QUEUE.values() if case.get("status") == status]
    else:
        items = list(HITL_QUEUE.values())
    
    # Sort by priority (high first) and then by created_at (oldest first)
    items.sort(key=lambda x: (
        0 if x.get("priority") == "high" else 1,
        x.get("created_at", "")
    ))
    
    return items


def get_hitl_item(hitl_id: str) -> Optional[Dict]:
    """
    Get a specific HITL case by ID.
    
    Args:
        hitl_id: HITL case ID
    
    Returns:
        HITL case dict or None if not found
    """
    return HITL_QUEUE.get(hitl_id)


def update_hitl_item(hitl_id: str, mentor_reply: str) -> bool:
    """
    Update HITL case with mentor reply and mark as resolved.
    
    Args:
        hitl_id: HITL case ID
        mentor_reply: Mentor's response message
    
    Returns:
        True if updated successfully, False if case not found
    """
    if hitl_id not in HITL_QUEUE:
        return False
    
    case = HITL_QUEUE[hitl_id]
    case["mentor_reply"] = mentor_reply
    case["status"] = "resolved"
    case["resolved_at"] = datetime.utcnow().isoformat()
    case["updated_at"] = datetime.utcnow().isoformat()
    
    # Notify mentor queue via SSE about case update (fire and forget)
    try:
        from app.sse_manager import sse_manager
        import asyncio
        
        # Try to get running event loop
        try:
            loop = asyncio.get_running_loop()
            # Schedule task if loop is running
            asyncio.create_task(sse_manager.send_to_session("mentor_queue", {
                "type": "case_updated",
                "case": case
            }))
        except RuntimeError:
            # No running loop, create new one (for sync contexts)
            asyncio.run(sse_manager.send_to_session("mentor_queue", {
                "type": "case_updated",
                "case": case
            }))
    except Exception:
        pass  # SSE not critical, fail silently
    
    return True


def get_session_hitl_replies(session_id: str) -> List[Dict]:
    """
    Get all resolved HITL replies for a session.
    
    Args:
        session_id: Parent session ID
    
    Returns:
        List of resolved HITL cases with mentor replies
    """
    replies = [
        case for case in HITL_QUEUE.values()
        if case.get("session_id") == session_id
        and case.get("status") == "resolved"
        and case.get("mentor_reply")
    ]
    
    # Sort by resolved_at (newest first)
    replies.sort(key=lambda x: x.get("resolved_at", ""), reverse=True)
    
    return replies

