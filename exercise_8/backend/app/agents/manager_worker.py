"""
Manager-Worker agent pattern implementation
"""
import asyncio
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from app.agents.base import BaseAgent, Blackboard
from app.utils.analysis import analyze_risk_with_openai


class ManagerAgent(BaseAgent):
    """Manager agent that coordinates workers"""
    
    async def execute(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute tasks in parallel using worker agents"""
        self.blackboard.add_history({
            "step": "manager_execution",
            "agent": self.agent_id,
            "status": "started",
            "output": {"task_count": len(tasks)}
        })
        
        # Execute tasks in parallel
        results = await self._process_tasks_parallel(tasks)
        
        self.blackboard.add_history({
            "step": "manager_execution",
            "agent": self.agent_id,
            "status": "completed",
            "output": {"result_count": len(results)}
        })
        
        return {"results": results, "status": "success"}

    async def _process_tasks_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process tasks in parallel using ThreadPoolExecutor"""
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                loop.run_in_executor(executor, self._process_single_task, task)
                for task in tasks
            ]
            results = await asyncio.gather(*futures, return_exceptions=True)
        
        # Filter out any exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                print(f"Task processing error: {result}")
            else:
                valid_results.append(result)
        
        return valid_results

    def _process_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single task (runs in thread)"""
        try:
            task_type = task.get("type", "risk_assessment")
            
            if task_type == "risk_assessment":
                clause_text = task.get("clause_text", "")
                policy_rules = task.get("policy_rules", {})
                
                # Use the existing risk analysis function
                analysis_result = analyze_risk_with_openai(clause_text, policy_rules)
                
                return {
                    "task_id": task.get("task_id"),
                    "clause_id": task.get("clause_id"),
                    "risk_level": analysis_result["risk_level"],
                    "rationale": analysis_result["rationale"],
                    "policy_refs": analysis_result["policy_refs"],
                    "status": "completed"
                }
            else:
                return {
                    "task_id": task.get("task_id"),
                    "status": "unknown_task_type",
                    "error": f"Unknown task type: {task_type}"
                }
        except Exception as e:
            return {
                "task_id": task.get("task_id"),
                "status": "error",
                "error": str(e)
            }


class WorkerAgent(BaseAgent):
    """Worker agent for specific task execution (acts as a function in parallel execution)"""
    
    def __init__(self, agent_id: str, blackboard: Blackboard):
        super().__init__(agent_id, blackboard)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task"""
        task_type = task.get("type", "risk_assessment")
        
        if task_type == "risk_assessment":
            clause_text = task.get("clause_text", "")
            policy_rules = task.get("policy_rules", {})
            
            # Use the existing risk analysis function
            analysis_result = analyze_risk_with_openai(clause_text, policy_rules)
            
            result = {
                "task_id": task.get("task_id"),
                "clause_id": task.get("clause_id"),
                "risk_level": analysis_result["risk_level"],
                "rationale": analysis_result["rationale"],
                "policy_refs": analysis_result["policy_refs"],
                "status": "completed"
            }
            
            # Update blackboard with the result
            assessment = {
                "clause_id": task.get("clause_id"),
                "risk_level": analysis_result["risk_level"],
                "rationale": analysis_result["rationale"],
                "policy_refs": analysis_result["policy_refs"]
            }
            self.blackboard.add_assessment(assessment)
            
            return result
        else:
            return {
                "task_id": task.get("task_id"),
                "status": "unknown_task_type",
                "error": f"Unknown task type: {task_type}"
            }


async def manager_worker_workflow(blackboard: Blackboard) -> Dict[str, Any]:
    """Execute the manager-worker workflow"""
    # Create manager
    manager = ManagerAgent("manager-agent-1", blackboard)
    
    # Prepare tasks from clauses in the blackboard
    tasks = []
    for clause in blackboard.clauses:
        task = {
            "task_id": f"task-{clause.get('id', 'unknown')}",
            "type": "risk_assessment",
            "clause_id": clause.get("id") or clause.get("clause_id"),
            "clause_text": clause.get("text", ""),
            "policy_rules": {}  # Will be populated from playbook if available
        }
        tasks.append(task)
    
    # Execute the workflow
    result = await manager.execute(tasks)
    
    # Generate redline proposals for high/medium risk clauses
    from app.agents.redline_generator import generate_redlines_for_run
    await generate_redlines_for_run(blackboard)
    
    return result