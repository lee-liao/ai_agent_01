"""
Safety guardrails for the Child Growth Assistant.
Classifies requests as in-scope or out-of-scope and provides appropriate refusal templates.
"""

import json
import time
from pathlib import Path
from typing import Tuple, Dict, Optional
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
                "therapy_keywords": ["depression", "anxiety", "trauma", "therapist"]
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
            
            # Check in priority order: crisis first (most urgent)
            if any(kw in text_lower for kw in self.policy['crisis_keywords']):
                matched_categories.append('crisis')
                category = 'crisis'
                refusal_data = self.get_refusal_template('crisis')
            elif any(kw in text_lower for kw in self.policy['medical_keywords']):
                matched_categories.append('medical')
                category = 'medical'
                refusal_data = self.get_refusal_template('medical')
            elif any(kw in text_lower for kw in self.policy['therapy_keywords']):
                matched_categories.append('therapy')
                category = 'therapy'
                refusal_data = self.get_refusal_template('therapy')
            elif any(kw in text_lower for kw in self.policy['legal_keywords']):
                matched_categories.append('legal')
                category = 'legal'
                refusal_data = self.get_refusal_template('legal')
            else:
                category = 'ok'
                refusal_data = None
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Set classification (SAFE, BLOCKED, ESCALATE)
            if category == 'ok':
                classification = 'SAFE'
            elif category == 'crisis':
                classification = 'ESCALATE'
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

