"""
Planner-Executor agent pattern implementation using the new Agent Framework
"""
import asyncio
import json
from typing import Dict, Any, List
from app.agents.agent import Agent, AgentStatus, AgentResult
from app.agents.redline_generator import generate_redlines_for_run


class PlannerAgent(Agent):
    """Planner agent that creates execution plans using the new Agent Framework"""
    
    def __init__(self):
        super().__init__(
            name="planner-agent",
            role="workflow_planner",
            capabilities=["create_execution_plan", "define_steps", "set_dependencies"],
            description="Creates multi-step execution plans for document review"
        )

    async def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """Create a multi-step plan for execution"""
        self.status = AgentStatus.RUNNING
        
        try:
            # Create the plan based on context
            plan = await self._create_plan(task, blackboard)
            
            # Store the plan in blackboard for executor
            blackboard["execution_plan"] = plan
            
            # Record execution in history
            if "history" not in blackboard:
                blackboard["history"] = []
            
            blackboard["history"].append({
                "step": "planning",
                "agent": self.name,
                "status": "completed",
                "timestamp": task.get("timestamp", "unknown"),
                "output": {"plan_steps": len(plan)}
            })
            
            self.status = AgentStatus.SUCCESS
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output={"plan_steps": len(plan)}
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )

    async def _create_plan(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> List[Dict[str, Any]]:
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
        assessments = blackboard.get("assessments", [])
        high_risk_count = len([a for a in assessments if a.get('risk_level') == 'HIGH'])
        if high_risk_count > 0:
            plan.append({
                "step": "hitl_approval",
                "agent": "hitl_approver",
                "description": "Human approval for high-risk clauses",
                "dependencies": ["review_proposals"]
            })
        
        return plan


class ExecutorAgent(Agent):
    """Executor agent that runs the plan step by step using the new Agent Framework"""
    
    def __init__(self):
        super().__init__(
            name="executor-agent",
            role="plan_executor",
            capabilities=["execute_plan", "manage_dependencies", "track_progress"],
            description="Executes the multi-step plan created by the planner"
        )

    async def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """Execute the plan step by step"""
        self.status = AgentStatus.RUNNING
        
        try:
            plan = blackboard.get("execution_plan", [])
            results = []
            
            for step in plan:
                step_result = await self._execute_step(step, blackboard)
                results.append(step_result)
                
                # Save checkpoint after each step
                step_key = f"step_{step['step']}_result"
                if "checkpoints" not in blackboard:
                    blackboard["checkpoints"] = {}
                blackboard["checkpoints"][step_key] = step_result

            # Record execution in history
            if "history" not in blackboard:
                blackboard["history"] = []
            
            blackboard["history"].append({
                "step": "execution_complete",
                "agent": self.name,
                "status": "completed",
                "timestamp": task.get("timestamp", "unknown"),
                "output": {"results_count": len(results)}
            })
            
            self.status = AgentStatus.SUCCESS
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output={"results_count": len(results)}
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )

    async def _execute_step(self, step: Dict[str, Any], blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step in the plan"""
        step_name = step["step"]
        agent_name = step["agent"]
        
        # Record step start in history
        if "history" not in blackboard:
            blackboard["history"] = []
        
        blackboard["history"].append({
            "step": step_name,
            "agent": agent_name,
            "status": "started",
            "timestamp": blackboard.get("timestamp", "unknown")
        })
        
        try:
            # Execute the step based on agent type
            if agent_name == "clause_parser":
                result = await self._execute_clause_parsing(blackboard)
            elif agent_name == "risk_analyzer":
                result = await self._execute_risk_analysis(blackboard)
            elif agent_name == "proposal_generator":
                result = await self._execute_proposal_generation(blackboard)
            elif agent_name == "proposal_reviewer":
                result = await self._execute_proposal_review(blackboard)
            elif agent_name == "hitl_approver":
                result = await self._execute_hitl_approval(blackboard)
            else:
                result = {
                    "step": step_name,
                    "status": "unknown_agent",
                    "error": f"Unknown agent: {agent_name}"
                }
            
            # Record step completion in history
            blackboard["history"].append({
                "step": step_name,
                "agent": agent_name,
                "status": "completed" if result.get("status") != "error" else "failed",
                "timestamp": blackboard.get("timestamp", "unknown"),
                "output": result
            })
            
            return result
            
        except Exception as e:
            # Record step failure in history
            blackboard["history"].append({
                "step": step_name,
                "agent": agent_name,
                "status": "error",
                "timestamp": blackboard.get("timestamp", "unknown"),
                "error": str(e)
            })
            
            return {
                "step": step_name,
                "status": "error",
                "error": str(e)
            }

    async def _execute_clause_parsing(self, blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Execute clause parsing step"""
        # Clauses should already be in the blackboard from the document
        clause_count = len(blackboard.get("clauses", []))
        
        return {
            "step": "parse",
            "status": "completed",
            "output": {"clauses_parsed": clause_count}
        }

    async def _execute_risk_analysis(self, blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk analysis step"""
        # Risk assessments may be in the blackboard from previous processing
        assessment_count = len(blackboard.get("assessments", []))
        
        return {
            "step": "analyze_risk", 
            "status": "completed",
            "output": {"assessments_performed": assessment_count}
        }

    async def _execute_proposal_generation(self, blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Execute proposal generation step"""
        high_risk_clauses = [
            assessment for assessment in blackboard.get("assessments", []) 
            if assessment.get("risk_level") in ["HIGH", "MEDIUM"]
        ]
        
        # Initialize proposals if not present
        if "proposals" not in blackboard:
            blackboard["proposals"] = []
        
        for assessment in high_risk_clauses:
            clause_id = assessment.get("clause_id")
            
            # Find the clause text from the clauses in blackboard
            clause_text = ""
            for clause in blackboard.get("clauses", []):
                if clause.get("id") == clause_id or clause.get("clause_id") == clause_id:
                    clause_text = clause.get("text", "")
                    break
            
            # Generate a proposal (in real implementation, this would use AI)
            proposal = {
                "clause_id": clause_id,
                "variant": "moderate",
                "original_text": clause_text,
                "edited_text": f"REDACTED: Original content of clause {clause_id} requires review",
                "rationale": assessment.get("rationale", "Risk identified"),
                "diffs": "content_redacted"
            }
            
            blackboard["proposals"].append(proposal)
        
        return {
            "step": "generate_proposals",
            "status": "completed", 
            "output": {"proposals_generated": len(blackboard["proposals"])}
        }

    async def _execute_proposal_review(self, blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Execute proposal review step"""
        # In a real implementation, this would review proposals against policy
        proposal_count = len(blackboard.get("proposals", []))
        
        return {
            "step": "review_proposals",
            "status": "completed",
            "output": {"proposals_reviewed": proposal_count}
        }

    async def _execute_hitl_approval(self, blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HITL approval step"""
        # Mark that HITL approval is required
        return {
            "step": "hitl_approval",
            "status": "pending",
            "output": {"approval_required": True}
        }


async def planner_executor_workflow(blackboard: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the planner-executor workflow using the new Agent Framework
    """
    from app.agents import Team, Coordinator
    from app.agents.team import TeamPattern
    
    # Create a team for planner-executor pattern
    team = Team(
        name="planner_executor_team_runtime",
        pattern=TeamPattern.PIPELINE  # Use pipeline for planner -> executor flow
    )
    
    # Add the planner and executor agents
    planner = PlannerAgent()
    executor = ExecutorAgent()
    
    team.add_agent(planner)
    team.add_agent(executor)
    
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