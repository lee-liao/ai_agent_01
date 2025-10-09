"""
Reviewer and Referee Agents for the Multi-Agent Framework

Implements the Reviewer/Referee pattern with checklist-driven validation
and contested decision arbitration.
"""

from typing import Dict, Any, List, Optional
from app.agents.agent import Agent, AgentStatus, AgentResult
from enum import Enum


class ReviewStatus(str, Enum):
    """Status for review results"""
    PASSED = "passed"
    FLAGGED = "flagged"
    CONTESTED = "contested"
    ERROR = "error"


class ReviewerAgent(Agent):
    """
    Validates clauses against a checklist using the new Agent Framework.
    
    The Reviewer Agent checks each clause against predefined checklist items
    and flags issues for potential arbitration.
    """
    
    def __init__(self, checklist: Optional[List[Dict[str, Any]]] = None):
        super().__init__(
            name="reviewer-agent",
            role="clause_reviewer",
            capabilities=["checklist_validation", "clause_verification", "policy_compliance"],
            description="Validates clauses against predefined checklists"
        )
        
        # Default checklist items - can be customized
        self.checklist = checklist or [
            {
                "id": "confidentiality_scope",
                "description": "Check for appropriate scope of confidentiality",
                "severity": "high",
                "test": self._test_confidentiality_scope
            },
            {
                "id": "liability_cap",
                "description": "Verify liability is appropriately capped",
                "severity": "high", 
                "test": self._test_liability_cap
            },
            {
                "id": "termination_provisions",
                "description": "Check termination clauses are balanced",
                "severity": "medium",
                "test": self._test_termination_provisions
            },
            {
                "id": "ip_ownership",
                "description": "Verify IP ownership clauses are clear",
                "severity": "high",
                "test": self._test_ip_ownership
            },
            {
                "id": "governing_law",
                "description": "Check governing law and jurisdiction clauses",
                "severity": "medium",
                "test": self._test_governing_law
            },
            {
                "id": "data_protection",
                "description": "Verify data protection compliance",
                "severity": "high", 
                "test": self._test_data_protection
            }
        ]

    async def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """
        Execute checklist-based review of clauses.
        
        Expected task format:
        {
            "type": "review_clauses",
            "checklist_override": [...],  # Optional custom checklist
            "target_clauses": [...]       # Optional specific clauses to review
        }
        """
        self.status = AgentStatus.RUNNING
        
        try:
            # Use override checklist if provided, otherwise use default
            checklist = task.get("checklist_override", self.checklist)
            
            # Get clauses to review - either specific ones or all in blackboard
            target_clauses = task.get("target_clauses")
            if not target_clauses:
                target_clauses = blackboard.get("clauses", [])
            
            # Get existing assessments to review against
            assessments = blackboard.get("assessments", [])
            
            review_results = []
            contested_items = []
            
            # Review each clause against the checklist
            for clause in target_clauses:
                clause_reviews = await self._review_clause(clause, checklist, blackboard)
                review_results.extend(clause_reviews)
                
                # Check for contested items (disagreements between assessment and review)
                for review in clause_reviews:
                    if review["status"] == ReviewStatus.CONTESTED:
                        contested_items.append({
                            "clause": clause,
                            "original_assessment": next(
                                (a for a in assessments if a["clause_id"] == clause["id"]), 
                                None
                            ),
                            "review_result": review
                        })
            
            # Store results in blackboard
            if "review_results" not in blackboard:
                blackboard["review_results"] = []
            blackboard["review_results"].extend(review_results)
            
            # Store contested items for referee arbitration
            if contested_items:
                blackboard["referee_queue"] = blackboard.get("referee_queue", []) + contested_items
            
            # Record execution in history
            if "history" not in blackboard:
                blackboard["history"] = []
            blackboard["history"].append({
                "step": "reviewer_complete",
                "agent": self.name,
                "status": "success",
                "timestamp": task.get("timestamp", "unknown"),
                "output": {
                    "reviewed_clauses": len(target_clauses),
                    "reviews_performed": len(review_results),
                    "contested_items": len(contested_items)
                }
            })
            
            self.status = AgentStatus.SUCCESS
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output={
                    "reviews_performed": len(review_results),
                    "contested_items": len(contested_items),
                    "summary": {
                        "passed": len([r for r in review_results if r["status"] == ReviewStatus.PASSED]),
                        "flagged": len([r for r in review_results if r["status"] == ReviewStatus.FLAGGED]),
                        "contested": len([r for r in review_results if r["status"] == ReviewStatus.CONTESTED])
                    }
                }
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            # Record error in history
            if "history" not in blackboard:
                blackboard["history"] = []
            blackboard["history"].append({
                "step": "reviewer_failed",
                "agent": self.name,
                "status": "error",
                "timestamp": task.get("timestamp", "unknown"),
                "error": str(e)
            })
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )

    async def _review_clause(self, clause: Dict[str, Any], checklist: List[Dict[str, Any]], blackboard: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Review a single clause against the checklist."""
        results = []
        
        for checklist_item in checklist:
            try:
                # Run the checklist test
                result = await checklist_item["test"](clause, blackboard)
                
                review_result = {
                    "clause_id": clause.get("id") or clause.get("clause_id"),
                    "checklist_id": checklist_item["id"],
                    "checklist_description": checklist_item["description"],
                    "severity": checklist_item["severity"],
                    "status": result["status"],
                    "details": result["details"],
                    "rationale": result["rationale"]
                }
                
                results.append(review_result)
                
            except Exception as e:
                results.append({
                    "clause_id": clause.get("id") or clause.get("clause_id"),
                    "checklist_id": checklist_item["id"],
                    "status": ReviewStatus.ERROR,
                    "details": str(e),
                    "rationale": f"Error during review: {str(e)}"
                })
        
        return results

    # Checklist test methods
    async def _test_confidentiality_scope(self, clause: Dict[str, Any], blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Test if confidentiality scope is appropriate."""
        text = clause.get("text", "").lower()
        heading = clause.get("heading", "").lower()
        
        if any(term in text for term in ["all information", "any and all information", "broad scope"]):
            return {
                "status": ReviewStatus.FLAGGED,
                "details": "Confidentiality scope may be overly broad",
                "rationale": "Broad confidentiality definitions could be difficult to enforce"
            }
        elif any(term in text for term in ["specific", "limited", "defined"]):
            return {
                "status": ReviewStatus.PASSED,
                "details": "Confidentiality scope appears appropriately limited",
                "rationale": "Scope is specific and enforceable"
            }
        else:
            return {
                "status": ReviewStatus.PASSED,
                "details": "Confidentiality scope is standard",
                "rationale": "No issues identified with confidentiality scope"
            }

    async def _test_liability_cap(self, clause: Dict[str, Any], blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Test if liability cap is appropriate."""
        text = clause.get("text", "").lower()
        
        if any(term in text for term in ["unlimited", "all damages", "no limitation"]):
            return {
                "status": ReviewStatus.FLAGGED,
                "details": "Unlimited liability identified",
                "rationale": "Liability caps should be specified"
            }
        elif any(term in text for term in ["limited to", "capped at", "maximum"]):
            return {
                "status": ReviewStatus.PASSED,
                "details": "Liability is appropriately capped",
                "rationale": "Liability limits are specified"
            }
        else:
            return {
                "status": ReviewStatus.PASSED,
                "details": "No liability issues identified",
                "rationale": "Standard liability language"
            }

    async def _test_termination_provisions(self, clause: Dict[str, Any], blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Test if termination provisions are balanced."""
        text = clause.get("text", "").lower()
        
        if any(term in text for term in ["sole discretion", "without cause", "immediate"]):
            return {
                "status": ReviewStatus.FLAGGED,
                "details": "Termination may be too one-sided",
                "rationale": "Termination terms should be balanced"
            }
        elif any(term in text for term in ["mutual agreement", "with cause", "notice required"]):
            return {
                "status": ReviewStatus.PASSED,
                "details": "Termination provisions appear balanced",
                "rationale": "Reasonable termination conditions"
            }
        else:
            return {
                "status": ReviewStatus.PASSED,
                "details": "Termination terms are standard",
                "rationale": "No issues identified with termination terms"
            }

    async def _test_ip_ownership(self, clause: Dict[str, Any], blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Test if IP ownership is clearly defined."""
        text = clause.get("text", "").lower()
        
        if "ip ownership" in text or "intellectual property" in text.lower():
            if any(term in text for term in ["clearly defined", "explicitly stated", "defined as"]):
                return {
                    "status": ReviewStatus.PASSED,
                    "details": "IP ownership clearly defined",
                    "rationale": "Intellectual property rights are explicitly assigned"
                }
            else:
                return {
                    "status": ReviewStatus.FLAGGED,
                    "details": "IP ownership may be unclear",
                    "rationale": "Intellectual property rights should be explicitly defined"
                }
        else:
            return {
                "status": ReviewStatus.PASSED,
                "details": "No IP ownership issues",
                "rationale": "Standard clause without IP concerns"
            }

    async def _test_governing_law(self, clause: Dict[str, Any], blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Test if governing law and jurisdiction are appropriate."""
        text = clause.get("text", "").lower()
        
        if any(term in text for term in ["governing law", "jurisdiction", "choice of law"]):
            if "unreasonable" not in text and "clear" in text:
                return {
                    "status": ReviewStatus.PASSED,
                    "details": "Governing law/jurisdiction is reasonable",
                    "rationale": "Appropriate governing law and jurisdiction clauses"
                }
            else:
                return {
                    "status": ReviewStatus.FLAGGED,
                    "details": "Governing law/jurisdiction may be unreasonable",
                    "rationale": "Jurisdiction should be fair and reasonable to both parties"
                }
        else:
            return {
                "status": ReviewStatus.FLAGGED,
                "details": "Missing governing law clause",
                "rationale": "Governing law and jurisdiction should be specified"
            }

    async def _test_data_protection(self, clause: Dict[str, Any], blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Test if data protection clauses comply with regulations."""
        text = clause.get("text", "").lower()
        
        if any(term in text for term in ["personal data", "gdpr", "data protection", "privacy"]):
            if any(term in text for term in ["compliance", "regulation", "lawful"]):
                return {
                    "status": ReviewStatus.PASSED,
                    "details": "Data protection provisions appear compliant",
                    "rationale": "Data protection obligations are addressed"
                }
            else:
                return {
                    "status": ReviewStatus.FLAGGED,
                    "details": "Data protection may be insufficient",
                    "rationale": "Data protection should comply with applicable regulations"
                }
        else:
            # If it's a data-heavy agreement, flag missing data protection
            if any(term in clause.get("heading", "").lower() for term in ["data processing", "privacy", "nda"]):
                return {
                    "status": ReviewStatus.FLAGGED,
                    "details": "Missing data protection provisions",
                    "rationale": "Data processing agreements should include data protection clauses"
                }
            else:
                return {
                    "status": ReviewStatus.PASSED,
                    "details": "No data protection issues",
                    "rationale": "Not a data-heavy agreement"
                }


class RefereeAgent(Agent):
    """
    Arbitrates contested decisions using the new Agent Framework.
    
    The Referee Agent resolves disagreements between different assessments
    and makes final decisions on contested items.
    """
    
    def __init__(self):
        super().__init__(
            name="referee-agent",
            role="decision_arbiter",
            capabilities=["dispute_resolution", "decision_arbitration", "conflict_resolution"],
            description="Arbitrates contested decisions and resolves conflicts"
        )

    async def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """
        Execute arbitration of contested decisions.
        
        Expected task format:
        {
            "type": "arbitrate_contested",
            "arbitration_policy": "strict|balanced|lenient",  # How to weight decisions
            "override_queue": [...]  # Optional specific items to arbitrate
        }
        """
        self.status = AgentStatus.RUNNING
        
        try:
            # Get items to arbitrate - either from override or from blackboard queue
            items_to_arbitrate = task.get("override_queue")
            if not items_to_arbitrate:
                items_to_arbitrate = blackboard.get("referee_queue", [])
            
            arbitration_results = []
            resolved_items = []
            contested_items = []
            
            # Apply arbitration policy
            arbitration_policy = task.get("arbitration_policy", "balanced")
            
            for item in items_to_arbitrate:
                result = await self._arbitrate_item(item, arbitration_policy, blackboard)
                arbitration_results.append(result)
                
                if result["status"] == "resolved":
                    resolved_items.append(result)
                else:
                    contested_items.append(result)
            
            # Update assessments in blackboard with arbitration decisions
            await self._update_assessments_with_arbitration(blackboard, resolved_items)
            
            # If there are still contested items, return them to queue for further review
            if contested_items:
                # Add back to referee queue for another round or escalation
                blackboard["referee_queue"] = contested_items
            else:
                # Clear the queue if all items are resolved
                blackboard.pop("referee_queue", None)
            
            # Record execution in history
            if "history" not in blackboard:
                blackboard["history"] = []
            blackboard["history"].append({
                "step": "referee_complete",
                "agent": self.name,
                "status": "success",
                "timestamp": task.get("timestamp", "unknown"),
                "output": {
                    "items_arbitrated": len(items_to_arbitrate),
                    "items_resolved": len(resolved_items),
                    "items_contested": len(contested_items)
                }
            })
            
            self.status = AgentStatus.SUCCESS
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output={
                    "items_arbitrated": len(items_to_arbitrate),
                    "items_resolved": len(resolved_items),
                    "items_contested": len(contested_items),
                    "policy_applied": arbitration_policy
                }
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            # Record error in history
            if "history" not in blackboard:
                blackboard["history"] = []
            blackboard["history"].append({
                "step": "referee_failed",
                "agent": self.name,
                "status": "error",
                "timestamp": task.get("timestamp", "unknown"),
                "error": str(e)
            })
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )

    async def _arbitrate_item(self, item: Dict[str, Any], policy: str, blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Arbitrate a single contested item."""
        try:
            clause = item.get("clause", {})
            original_assessment = item.get("original_assessment", {})
            review_result = item.get("review_result", {})
            
            # Apply different arbitration logic based on policy
            if policy == "strict":
                # Default to the most conservative/risky assessment
                final_risk = self._determine_strict_risk(original_assessment, review_result)
            elif policy == "lenient":
                # Default to the least conservative assessment
                final_risk = self._determine_lenient_risk(original_assessment, review_result)
            else:  # balanced policy (default)
                # Use weighted analysis
                final_risk = self._determine_balanced_risk(original_assessment, review_result, clause)
            
            # Create arbitration decision
            decision = {
                "clause_id": clause.get("id") or original_assessment.get("clause_id") or review_result.get("clause_id"),
                "original_assessment": original_assessment,
                "review_result": review_result,
                "arbitration_decision": final_risk,
                "policy_applied": policy,
                "status": "resolved",
                "timestamp": blackboard.get("timestamp", "unknown"),
                "arbitrator": self.name
            }
            
            return decision
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "original_item": item
            }

    def _determine_strict_risk(self, original: Dict[str, Any], review: Dict[str, Any]) -> str:
        """Determine risk level using strict/conservative approach."""
        # Return the higher risk level if there's disagreement
        original_risk = original.get("risk_level", "LOW").upper()
        review_risk = review.get("risk_level", "LOW").upper()
        
        risk_hierarchy = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        
        if risk_hierarchy.get(review_risk, 1) > risk_hierarchy.get(original_risk, 1):
            return review_risk
        else:
            return original_risk

    def _determine_lenient_risk(self, original: Dict[str, Any], review: Dict[str, Any]) -> str:
        """Determine risk level using lenient approach."""
        # Return the lower risk level if there's disagreement
        original_risk = original.get("risk_level", "LOW").upper()
        review_risk = review.get("risk_level", "LOW").upper()
        
        risk_hierarchy = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        
        if risk_hierarchy.get(review_risk, 1) < risk_hierarchy.get(original_risk, 1):
            return review_risk
        else:
            return original_risk

    def _determine_balanced_risk(self, original: Dict[str, Any], review: Dict[str, Any], clause: Dict[str, Any]) -> str:
        """Determine risk level using balanced analysis."""
        # Perform weighted analysis considering both assessments
        original_risk = original.get("risk_level", "LOW").upper()
        review_risk = review.get("risk_level", "LOW").upper()
        
        # If both agree, return that level
        if original_risk == review_risk:
            return original_risk
        
        # If they disagree, look more deeply at the clause content
        clause_text = clause.get("text", "").lower()
        
        # Count risk indicators in the clause
        high_risk_indicators = [
            "unlimited", "all damages", "without limitation", "sole discretion", 
            "indemnify hold harmless", "no cap", "irrevocable", "perpetual"
        ]
        
        medium_risk_indicators = [
            "indemnify", "warranty", "terminate.*notice", "non-compete",
            "audit.*rights", "data.*retention", "subprocessor"
        ]
        
        high_matches = sum(1 for indicator in high_risk_indicators if indicator in clause_text)
        medium_matches = sum(1 for indicator in medium_risk_indicators if indicator in clause_text)
        
        if high_matches > 0:
            return "HIGH"
        elif medium_matches > 0:
            return "MEDIUM"
        else:
            # Default to the higher of the two if no clear indicators
            risk_hierarchy = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
            return original_risk if risk_hierarchy.get(original_risk, 1) >= risk_hierarchy.get(review_risk, 1) else review_risk

    async def _update_assessments_with_arbitration(self, blackboard: Dict[str, Any], resolved_items: List[Dict[str, Any]]):
        """Update the main assessments with arbitration decisions."""
        # Get existing assessments
        assessments = blackboard.get("assessments", [])
        
        # Update each resolved item in the assessments
        for resolved_item in resolved_items:
            clause_id = resolved_item["clause_id"]
            
            # Find and update the corresponding assessment
            for assessment in assessments:
                if assessment.get("clause_id") == clause_id:
                    # Update with arbitration decision
                    assessment["arbitration_decision"] = resolved_item["arbitration_decision"]
                    assessment["arbitration_reasoning"] = f"Final decision after resolving disagreement between original assessment ({assessment.get('risk_level')}) and reviewer assessment ({resolved_item.get('review_result', {}).get('status', 'unknown')})"
                    assessment["final_risk_level"] = resolved_item["arbitration_decision"]
                    break
        
        # Update blackboard with modified assessments
        blackboard["assessments"] = assessments