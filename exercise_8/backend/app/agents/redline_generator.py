"""
Redline generation functionality for Exercise 8
"""
import asyncio
from typing import Dict, Any, List, Union
from app.agents.base import Blackboard
from app.main import analyze_risk_with_openai


class RedlineGenerator:
    """Generate redline proposals for risky clauses"""
    
    def __init__(self, blackboard: Union[Blackboard, Dict[str, Any]]):
        self.blackboard = blackboard

    def _get_list(self, key: str) -> List[Dict[str, Any]]:
        if isinstance(self.blackboard, dict):
            return self.blackboard.get(key, [])
        return getattr(self.blackboard, key, [])

    def _iter_clauses(self) -> List[Dict[str, Any]]:
        clauses = self._get_list("clauses")
        return clauses if isinstance(clauses, list) else []

    async def generate_redlines(self) -> List[Dict[str, Any]]:
        """Generate redline proposals for high and medium risk clauses"""
        redline_proposals = []
        
        # Process each assessment to generate redline proposals
        for assessment in self._get_list("assessments"):
            risk_level = assessment.get("risk_level", "").lower()
            clause_id = assessment.get("clause_id")
            
            # Only generate redlines for high and medium risk clauses
            if risk_level in ["high", "medium"]:
                proposal = await self._generate_proposal_for_clause(assessment)
                if proposal:
                    redline_proposals.append(proposal)
        
        return redline_proposals
    
    async def _generate_proposal_for_clause(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a redline proposal for a specific clause"""
        clause_id = assessment.get("clause_id")
        
        # Find the original clause text
        original_clause = None
        for clause in self._iter_clauses():
            if clause.get("id") == clause_id or clause.get("clause_id") == clause_id:
                original_clause = clause
                break
        
        if not original_clause:
            return None
        
        # Generate the edited text (in a real implementation, this would use more sophisticated logic)
        original_text = original_clause.get("text", "")
        heading = original_clause.get("heading", f"Clause {clause_id}")
        
        # Create edited version - this is simplified for demo
        # In a real implementation, this would suggest specific changes based on the risk
        edited_text = self._create_edited_text(original_text, assessment)
        
        proposal = {
            "clause_id": clause_id,
            "heading": heading,
            "variant": "conservative",
            "original_text": original_text,
            "edited_text": edited_text,
            "rationale": assessment.get("rationale", "Risk identified"),
            "risk_level": assessment.get("risk_level"),
            "policy_refs": assessment.get("policy_refs", []),
            "status": "proposed"
        }
        
        return proposal
    
    def _create_edited_text(self, original_text: str, assessment: Dict[str, Any]) -> str:
        """Create an edited version of the text based on the risk assessment"""
        risk_level = assessment.get("risk_level", "").lower()
        rationale = assessment.get("rationale", "")
        
        # This is a simplified approach - in reality, this would involve 
        # specific legal language changes based on the risk type
        if risk_level == "high":
            return f"[PROPOSED EDIT: Address high risk identified in assessment - {rationale}] {original_text}"
        elif risk_level == "medium":
            return f"[PROPOSED EDIT: Consider modification for medium risk - {rationale}] {original_text}"
        else:
            return original_text


async def generate_redlines_for_run(blackboard: Blackboard) -> List[Dict[str, Any]]:
    """Generate redline proposals for a run's blackboard"""
    generator = RedlineGenerator(blackboard)
    proposals = await generator.generate_redlines()
    
    # Add proposals to the blackboard
    if hasattr(blackboard, "add_proposal"):
        for proposal in proposals:
            blackboard.add_proposal(proposal)
    elif isinstance(blackboard, dict):
        blackboard.setdefault("proposals", []).extend(proposals)
    
    return proposals