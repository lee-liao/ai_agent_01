"""
Planner-Executor agent pattern implementation
"""
import asyncio
import json
from typing import Dict, Any, List
from app.agents.base import BaseAgent, Blackboard


class PlannerAgent(BaseAgent):
    """Planner agent that creates execution plans"""
    
    async def execute(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a multi-step plan for execution"""
        self.blackboard.add_history({
            "step": "planning",
            "agent": self.agent_id,
            "status": "started",
            "context": context or {}
        })
        
        # Create the plan based on context
        plan = await self._create_plan(context)
        
        # Store the plan in blackboard for executor
        self.blackboard.set_checkpoint("execution_plan", plan)
        
        self.blackboard.add_history({
            "step": "planning", 
            "agent": self.agent_id,
            "status": "completed",
            "output": {"plan_steps": len(plan)}
        })
        
        return {"plan": plan, "status": "success"}

    async def _create_plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create execution plan based on context"""
        # Default plan for contract analysis
        plan = [
            {
                "step": "parse",
                "agent": "clause_parser",
                "description": "Parse clauses from document",
                "dependencies": []
            },
            {
                "step": "analyze_risk",
                "agent": "risk_analyzer", 
                "description": "Analyze risks for each clause",
                "dependencies": ["parse"]
            },
            {
                "step": "generate_proposals",
                "agent": "proposal_generator",
                "description": "Generate redline proposals for risky clauses",
                "dependencies": ["analyze_risk"]
            },
            {
                "step": "review_proposals",
                "agent": "proposal_reviewer",
                "description": "Review generated proposals",
                "dependencies": ["generate_proposals"]
            }
        ]
        
        # Add conditional steps if context indicates need for HITL
        high_risk_count = len([a for a in self.blackboard.assessments if a.get('risk_level') == 'High'])
        if high_risk_count > 0:
            plan.append({
                "step": "hitl_approval",
                "agent": "hitl_approver",
                "description": "Human approval for high-risk clauses",
                "dependencies": ["review_proposals"]
            })
        
        return plan


class ExecutorAgent(BaseAgent):
    """Executor agent that runs the plan step by step"""
    
    async def execute(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the plan step by step"""
        self.blackboard.add_history({
            "step": "execution_start",
            "agent": self.agent_id,
            "status": "started",
            "plan_steps": len(plan)
        })
        
        results = []
        
        for step in plan:
            step_result = await self._execute_step(step)
            results.append(step_result)
            
            # Save checkpoint after each step
            step_key = f"step_{step['step']}_result"
            self.blackboard.set_checkpoint(step_key, step_result)
        
        self.blackboard.add_history({
            "step": "execution_complete",
            "agent": self.agent_id,
            "status": "completed",
            "results_count": len(results)
        })
        
        return {"results": results, "status": "success"}

    async def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step in the plan"""
        step_name = step["step"]
        agent_name = step["agent"]
        
        self.blackboard.add_history({
            "step": step_name,
            "agent": agent_name,
            "status": "started"
        })
        
        try:
            # Execute the step based on agent type
            if agent_name == "clause_parser":
                result = await self._execute_clause_parsing()
            elif agent_name == "risk_analyzer":
                result = await self._execute_risk_analysis()
            elif agent_name == "proposal_generator":
                result = await self._execute_proposal_generation()
            elif agent_name == "proposal_reviewer":
                result = await self._execute_proposal_review()
            elif agent_name == "hitl_approver":
                result = await self._execute_hitl_approval()
            else:
                result = {
                    "step": step_name,
                    "status": "unknown_agent",
                    "error": f"Unknown agent: {agent_name}"
                }
            
            # Update history with completion status
            self.blackboard.add_history({
                "step": step_name,
                "agent": agent_name,
                "status": "completed" if result.get("status") != "error" else "failed",
                "output": result
            })
            
            return result
            
        except Exception as e:
            error_result = {
                "step": step_name,
                "status": "error",
                "error": str(e)
            }
            
            self.blackboard.add_history({
                "step": step_name,
                "agent": agent_name,
                "status": "error",
                "error": str(e)
            })
            
            return error_result

    async def _execute_clause_parsing(self) -> Dict[str, Any]:
        """Execute clause parsing step"""
        # Clauses should already be in the blackboard from the document
        clause_count = len(self.blackboard.clauses)
        
        return {
            "step": "parse",
            "status": "completed",
            "output": {"clauses_parsed": clause_count}
        }

    async def _execute_risk_analysis(self) -> Dict[str, Any]:
        """Execute risk analysis step"""
        # Risk assessments should already be in the blackboard from previous processing
        assessment_count = len(self.blackboard.assessments)
        
        return {
            "step": "analyze_risk", 
            "status": "completed",
            "output": {"assessments_performed": assessment_count}
        }

    async def _execute_proposal_generation(self) -> Dict[str, Any]:
        """Execute proposal generation step"""
        # Generate redline proposals for high/medium risk clauses
        high_risk_clauses = [
            assessment for assessment in self.blackboard.assessments 
            if assessment.get("risk_level") in ["High", "Medium"]
        ]
        
        for assessment in high_risk_clauses:
            clause_id = assessment.get("clause_id")
            
            # Find the clause text from the clauses in blackboard
            clause_text = ""
            for clause in self.blackboard.clauses:
                if clause.get("id") == clause_id or clause.get("clause_id") == clause_id:
                    clause_text = clause.get("text", "")
                    break
            
            # Generate a simple proposal (in real implementation, this would use AI)
            proposal = {
                "clause_id": clause_id,
                "variant": "moderate",
                "original_text": clause_text,
                "edited_text": f"REDACTED: Original content of clause {clause_id} requires review",
                "rationale": assessment.get("rationale", "Risk identified"),
                "diffs": "content_redacted"
            }
            
            self.blackboard.add_proposal(proposal)
        
        return {
            "step": "generate_proposals",
            "status": "completed", 
            "output": {"proposals_generated": len(self.blackboard.proposals)}
        }

    async def _execute_proposal_review(self) -> Dict[str, Any]:
        """Execute proposal review step"""
        # In a real implementation, this would review proposals against policy
        proposal_count = len(self.blackboard.proposals)
        
        return {
            "step": "review_proposals",
            "status": "completed",
            "output": {"proposals_reviewed": proposal_count}
        }

    async def _execute_hitl_approval(self) -> Dict[str, Any]:
        """Execute HITL approval step"""
        # Mark that HITL approval is required
        return {
            "step": "hitl_approval",
            "status": "pending",
            "output": {"approval_required": True}
        }


async def planner_executor_workflow(blackboard: Blackboard) -> Dict[str, Any]:
    """Execute the planner-executor workflow"""
    # Create planner and executor
    planner = PlannerAgent("planner-agent-1", blackboard)
    executor = ExecutorAgent("executor-agent-1", blackboard)
    
    # Generate plan
    plan_result = await planner.execute()
    plan = plan_result.get("plan", [])
    
    # Execute the plan
    execution_result = await executor.execute(plan)
    
    # Generate redline proposals for high/medium risk clauses
    from app.agents.redline_generator import generate_redlines_for_run
    await generate_redlines_for_run(blackboard)
    
    return {
        "plan_result": plan_result,
        "execution_result": execution_result,
        "status": "completed"
    }