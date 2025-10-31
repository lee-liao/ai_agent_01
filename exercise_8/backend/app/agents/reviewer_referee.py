"""
Reviewer-Referee agent pattern implementation
"""
import asyncio
from typing import Dict, Any, List
from app.agents.base import BaseAgent, Blackboard


class ReviewerAgent(BaseAgent):
    """Reviewer agent that checks against predefined checklist"""
    
    def __init__(self, agent_id: str, blackboard: Blackboard, checklist: List[Dict[str, Any]] = None):
        super().__init__(agent_id, blackboard)
        self.checklist = checklist or [
            {"id": "liability_cap", "description": "Check for liability caps", "severity": "high"},
            {"id": "term_length", "description": "Check for appropriate term lengths", "severity": "medium"},
            {"id": "termination_clause", "description": "Check termination clauses", "severity": "medium"},
            {"id": "confidentiality", "description": "Check confidentiality provisions", "severity": "high"},
            {"id": "dispute_resolution", "description": "Check dispute resolution mechanisms", "severity": "medium"}
        ]

    async def execute(self, items_to_review: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the review against checklist"""
        self.blackboard.add_history({
            "step": "review_start",
            "agent": self.agent_id,
            "status": "started",
            "checklist_items": len(self.checklist)
        })
        
        # If no specific items provided, review all assessments in blackboard
        if items_to_review is None:
            items_to_review = self.blackboard.assessments
            
        review_results = []
        contested_items = []
        
        for item in items_to_review:
            for checklist_item in self.checklist:
                review_result = await self._review_item(item, checklist_item)
                review_results.append(review_result)
                
                if review_result.get("status") == "contested":
                    contested_items.append({
                        "item": item,
                        "checklist_item": checklist_item,
                        "review_result": review_result
                    })
        
        self.blackboard.add_history({
            "step": "review_complete",
            "agent": self.agent_id,
            "status": "completed",
            "review_results_count": len(review_results),
            "contested_count": len(contested_items)
        })
        
        # Store contested items for referee arbitration
        if contested_items:
            self.blackboard.set_checkpoint("contested_items", contested_items)
        
        return {
            "review_results": review_results,
            "contested_items": contested_items,
            "status": "completed"
        }

    async def _review_item(self, item: Dict[str, Any], checklist_item: Dict[str, Any]) -> Dict[str, Any]:
        """Review a single item against a checklist item"""
        try:
            item_id = item.get("clause_id", "unknown")
            checklist_id = checklist_item["id"]
            
            # Basic keyword matching for demo purposes
            item_text = item.get("text", item.get("rationale", "")).lower()
            keywords = self._get_keywords_for_checklist(checklist_id)
            
            # Check if any keywords exist in the item text
            matches = []
            for keyword in keywords:
                if keyword in item_text:
                    matches.append(keyword)
            
            if matches:
                # Potential issue detected, mark for further review
                status = "flagged"  # This could be contested in more complex scenarios
                
                result = {
                    "item_id": item_id,
                    "checklist_id": checklist_id,
                    "status": status,
                    "matches": matches,
                    "rationale": f"Found keywords: {', '.join(matches)}"
                }
                
                # In a more complex implementation, we might flag this as contested
                # if there are conflicting interpretations
                if checklist_item["severity"] == "high" and len(matches) > 1:
                    result["status"] = "contested"
            else:
                result = {
                    "item_id": item_id,
                    "checklist_id": checklist_id,
                    "status": "passed",
                    "matches": [],
                    "rationale": "No matching keywords found"
                }
            
            return result
            
        except Exception as e:
            return {
                "item_id": item.get("clause_id", "unknown"),
                "checklist_id": checklist_item.get("id", "unknown"),
                "status": "error",
                "error": str(e)
            }

    def _get_keywords_for_checklist(self, checklist_id: str) -> List[str]:
        """Get relevant keywords for a checklist item"""
        keyword_map = {
            "liability_cap": ["liability", "limit", "cap", "exceed", "responsibility"],
            "term_length": ["term", "duration", "period", "renewal", "expiration"],
            "termination_clause": ["terminate", "terminate", "end", "cancellation", "notice"],
            "confidentiality": ["confidential", "secret", "non-disclosure", "disclose", "private"],
            "dispute_resolution": ["dispute", "arbitration", "mediation", "court", "litigation"]
        }
        return keyword_map.get(checklist_id, [])


class RefereeAgent(BaseAgent):
    """Referee agent that arbitrate contested decisions"""
    
    async def execute(self, contested_items: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Arbitrate contested items"""
        self.blackboard.add_history({
            "step": "referee_start",
            "agent": self.agent_id,
            "status": "started"
        })
        
        # If no contested items provided, check the blackboard
        if contested_items is None:
            contested_items = self.blackboard.checkpoints.get("contested_items", [])
        
        arbitration_results = []
        
        for contested_item in contested_items:
            arbitration_result = await self._arbitrate_item(contested_item)
            arbitration_results.append(arbitration_result)
            
            # Update the main assessments with the arbitration result
            await self._update_assessment_with_arbitration(contested_item, arbitration_result)
        
        self.blackboard.add_history({
            "step": "referee_complete",
            "agent": self.agent_id,
            "status": "completed",
            "arbitration_results_count": len(arbitration_results)
        })
        
        return {
            "arbitration_results": arbitration_results,
            "status": "completed"
        }

    async def _arbitrate_item(self, contested_item: Dict[str, Any]) -> Dict[str, Any]:
        """Arbitrate a single contested item"""
        try:
            item = contested_item["item"]
            checklist_item = contested_item["checklist_item"]
            
            # Simple arbitration logic for demo purposes
            # In real implementation, this would use more sophisticated logic or human input
            item_text = item.get("text", item.get("rationale", "")).lower()
            keywords = self._get_keywords_for_checklist(checklist_item["id"])
            
            # Count keyword matches
            match_count = sum(1 for keyword in keywords if keyword in item_text)
            
            # Make arbitration decision based on match count and severity
            if match_count > 0:
                decision = "confirmed"  # Confirms the risk/issue
                confidence = min(0.8 + (match_count * 0.05), 0.95)  # Confidence between 0.8-0.95
            else:
                decision = "rejected"  # Rejects the concern
                confidence = 0.7  # Default confidence for rejection
            
            result = {
                "item_id": item.get("clause_id", "unknown"),
                "checklist_id": checklist_item["id"],
                "decision": decision,
                "confidence": confidence,
                "rationale": f"Arbitrated based on keyword matches ({match_count}) and severity ({checklist_item['severity']})",
                "status": "completed"
            }
            
            return result
            
        except Exception as e:
            return {
                "item_id": contested_item.get("item", {}).get("clause_id", "unknown"),
                "status": "error",
                "error": str(e)
            }

    async def _update_assessment_with_arbitration(self, contested_item: Dict[str, Any], arbitration_result: Dict[str, Any]):
        """Update the main assessment with arbitration result"""
        # Find and update the original assessment in the blackboard
        clause_id = contested_item["item"].get("clause_id")
        
        for assessment in self.blackboard.assessments:
            if assessment.get("clause_id") == clause_id:
                assessment["arbitration"] = arbitration_result
                assessment["final_status"] = arbitration_result.get("decision", assessment.get("risk_level"))
                break

    def _get_keywords_for_checklist(self, checklist_id: str) -> List[str]:
        """Get relevant keywords for a checklist item"""
        keyword_map = {
            "liability_cap": ["liability", "limit", "cap", "exceed", "responsibility"],
            "term_length": ["term", "duration", "period", "renewal", "expiration"],
            "termination_clause": ["terminate", "terminate", "end", "cancellation", "notice"],
            "confidentiality": ["confidential", "secret", "non-disclosure", "disclose", "private"],
            "dispute_resolution": ["dispute", "arbitration", "mediation", "court", "litigation"]
        }
        return keyword_map.get(checklist_id, [])


async def reviewer_referee_workflow(blackboard: Blackboard) -> Dict[str, Any]:
    """Execute the reviewer-referee workflow"""
    # Create reviewer and referee
    reviewer = ReviewerAgent("reviewer-agent-1", blackboard)
    referee = RefereeAgent("referee-agent-1", blackboard)
    
    # Execute the review
    review_result = await reviewer.execute()
    
    # If there are contested items, execute the referee
    contested_items = review_result.get("contested_items", [])
    if contested_items:
        referee_result = await referee.execute(contested_items)
        result = {
            "review_result": review_result,
            "referee_result": referee_result,
            "status": "completed_with_arbitration"
        }
    else:
        result = {
            "review_result": review_result,
            "status": "completed_no_arbitration_needed"
        }
    
    # Generate redline proposals for high/medium risk clauses
    from app.agents.redline_generator import generate_redlines_for_run
    await generate_redlines_for_run(blackboard)
    
    return result