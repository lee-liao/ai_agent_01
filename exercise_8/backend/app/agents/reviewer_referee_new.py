"""
Reviewer-Referee agent pattern implementation using the new Agent Framework
"""
import asyncio
from typing import Dict, Any, List
from app.agents.agent import Agent, AgentStatus, AgentResult
from app.agents.redline_generator import generate_redlines_for_run


class ReviewerAgent(Agent):
    """Reviewer agent that checks against predefined checklist using the new Agent Framework"""
    
    def __init__(self, checklist: List[Dict[str, Any]] = None):
        super().__init__(
            name="reviewer-agent",
            role="checklist_reviewer",
            capabilities=["review_against_checklist", "flag_issues", "check_compliance"],
            description="Reviews clauses against predefined checklists"
        )
        self.checklist = checklist or [
            {"id": "liability_cap", "description": "Check for liability caps", "severity": "high"},
            {"id": "term_length", "description": "Check for appropriate term lengths", "severity": "medium"},
            {"id": "termination_clause", "description": "Check termination clauses", "severity": "medium"},
            {"id": "confidentiality", "description": "Check confidentiality provisions", "severity": "high"},
            {"id": "dispute_resolution", "description": "Check dispute resolution mechanisms", "severity": "medium"}
        ]

    async def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """Execute the review against checklist"""
        self.status = AgentStatus.RUNNING
        
        try:
            # If no specific items provided, review all assessments in blackboard
            items_to_review = blackboard.get("assessments", [])
            
            review_results = []
            contested_items = []
            
            for item in items_to_review:
                for checklist_item in self.checklist:
                    review_result = await self._review_item(item, checklist_item, blackboard)
                    review_results.append(review_result)
                    
                    if review_result.get("status") == "contested":
                        contested_items.append({
                            "item": item,
                            "checklist_item": checklist_item,
                            "review_result": review_result
                        })
            
            # Record contested items for referee arbitration
            if contested_items:
                blackboard["contested_items"] = contested_items
            
            # Record execution in history
            if "history" not in blackboard:
                blackboard["history"] = []
            
            blackboard["history"].append({
                "step": "review_complete",
                "agent": self.name,
                "status": "completed",
                "timestamp": task.get("timestamp", "unknown"),
                "output": {
                    "review_results_count": len(review_results),
                    "contested_count": len(contested_items)
                }
            })
            
            self.status = AgentStatus.SUCCESS
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output={
                    "review_results_count": len(review_results),
                    "contested_count": len(contested_items)
                }
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )

    async def _review_item(self, item: Dict[str, Any], checklist_item: Dict[str, Any], blackboard: Dict[str, Any]) -> Dict[str, Any]:
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


class RefereeAgent(Agent):
    """Referee agent that arbitrate contested decisions using the new Agent Framework"""
    
    def __init__(self):
        super().__init__(
            name="referee-agent",
            role="contested_decision_arbiter",
            capabilities=["arbitrate_contested", "make_final_decision", "resolve_conflicts"],
            description="Arbitrates contested decisions from the reviewer"
        )

    async def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """Arbitrate contested items"""
        self.status = AgentStatus.RUNNING
        
        try:
            # If no contested items provided, check the blackboard
            contested_items = blackboard.get("contested_items", [])
            
            arbitration_results = []
            
            for contested_item in contested_items:
                arbitration_result = await self._arbitrate_item(contested_item, blackboard)
                arbitration_results.append(arbitration_result)
                
                # Update the main assessments with the arbitration result
                await self._update_assessment_with_arbitration(contested_item, arbitration_result, blackboard)
            
            # Record execution in history
            if "history" not in blackboard:
                blackboard["history"] = []
            
            blackboard["history"].append({
                "step": "referee_complete",
                "agent": self.name,
                "status": "completed",
                "timestamp": task.get("timestamp", "unknown"),
                "output": {"arbitration_results_count": len(arbitration_results)}
            })
            
            self.status = AgentStatus.SUCCESS
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output={"arbitration_results_count": len(arbitration_results)}
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )

    async def _arbitrate_item(self, contested_item: Dict[str, Any], blackboard: Dict[str, Any]) -> Dict[str, Any]:
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

    async def _update_assessment_with_arbitration(self, contested_item: Dict[str, Any], arbitration_result: Dict[str, Any], blackboard: Dict[str, Any]):
        """Update the main assessment with arbitration result"""
        # Find and update the original assessment in the blackboard
        clause_id = contested_item["item"].get("clause_id")
        
        for assessment in blackboard.get("assessments", []):
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


async def reviewer_referee_workflow(blackboard: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the reviewer-referee workflow using the new Agent Framework
    """
    from app.agents import Team, Coordinator
    from app.agents.team import TeamPattern
    
    # Create a team for reviewer-referee pattern
    team = Team(
        name="reviewer_referee_team_runtime",
        pattern=TeamPattern.SEQUENTIAL  # Reviewer first, then referee if needed
    )
    
    # Add the reviewer and referee agents
    reviewer = ReviewerAgent()
    referee = RefereeAgent()
    
    team.add_agent(reviewer)
    team.add_agent(referee)
    
    # Execute the team
    task = {
        "type": "review_document",
        "document_text": blackboard.get("document_text", ""),
        "timestamp": blackboard.get("timestamp", "")
    }
    
    result = team.execute(task, blackboard)
    
    # Generate redline proposals for high/medium risk clauses
    await generate_redlines_for_run(blackboard)
    
    return result