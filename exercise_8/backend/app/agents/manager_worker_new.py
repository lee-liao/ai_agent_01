"""
Manager-Worker agent pattern implementation using the new Agent Framework
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from app.agents.agent import Agent, AgentStatus, AgentResult
from app.utils.analysis import analyze_risk_with_openai, resolve_clause_texts, build_risk_prompt
from app.agents.redline_generator import generate_redlines_for_run


def _extract_log_context(blackboard: Dict[str, Any]) -> Dict[str, Any]:
    run_id = blackboard.get("run_id")
    metadata = blackboard.get("metadata") if isinstance(blackboard.get("metadata"), dict) else {}
    replayed_from = metadata.get("replayed_from") if metadata else None
    context: Dict[str, Any] = {
        "run_id": run_id,
        "agent_path": metadata.get("agent_path") or blackboard.get("agent_path") or "manager_worker",
        "mode": "replay" if (replayed_from or blackboard.get("replayed_from")) else "initial",
    }
    doc_id = metadata.get("doc_id") if metadata else None
    if not doc_id:
        doc_id = blackboard.get("doc_id")
    if doc_id:
        context["doc_id"] = doc_id

    playbook_id = metadata.get("playbook_id") if metadata else None
    if not playbook_id:
        playbook_id = blackboard.get("playbook_id")
    if playbook_id:
        context["playbook_id"] = playbook_id

    original_run_id = replayed_from or blackboard.get("replayed_from")
    if original_run_id:
        context["original_run_id"] = original_run_id
    return context


def _build_log_metadata(
    blackboard: Dict[str, Any],
    clause_id: Optional[str],
    source: str,
    task: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    metadata = _extract_log_context(blackboard)
    payload = {
        **metadata,
        "source": source,
        "clause_id": clause_id,
    }
    if task:
        payload["task_id"] = task.get("task_id")
    return {k: v for k, v in payload.items() if v is not None}


class ManagerAgent(Agent):
    """Manager agent that coordinates workers using the new Agent Framework"""
    
    def __init__(self):
        super().__init__(
            name="manager-agent",
            role="task_coordinator",
            capabilities=["task_decomposition", "parallel_execution", "result_aggregation"],
            description="Coordinates worker agents in parallel execution"
        )
    
    async def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """Execute tasks in parallel using worker agents"""
        self.status = AgentStatus.RUNNING
        
        try:
            # Extract tasks from the blackboard
            clauses = blackboard.get("clauses", [])
            document_text = blackboard.get("document_text")
            if not document_text and isinstance(blackboard.get("metadata"), dict):
                document_text = blackboard["metadata"].get("document_text")
            normalized_texts = resolve_clause_texts(clauses, document_text)
            tasks = []
            display_texts: Dict[str, str] = {}
            display_prompts: Dict[str, str] = {}
            
            for clause in clauses:
                clause_id = clause.get("id") or clause.get("clause_id")
                normalized_text = normalized_texts.get(clause_id) if clause_id else None
                analysis_text = normalized_text or clause.get("body") or clause.get("text", "")
                display_text = normalized_text or clause.get("body") or clause.get("text", "")
                display_prompt = build_risk_prompt(analysis_text, blackboard.get("policy_rules", {}))
                if clause_id:
                    display_texts[clause_id] = display_text
                    display_prompts[clause_id] = display_prompt
                task_item = {
                    "task_id": f"task-{clause_id or 'unknown'}",
                    "type": "risk_assessment",
                    "clause_id": clause_id,
                    "clause_text": analysis_text,
                    "display_text": display_text,
                    "display_prompt": display_prompt,
                    "policy_rules": blackboard.get("policy_rules", {})
                }
                tasks.append(task_item)
            
            # Execute tasks in parallel
            results = await self._process_tasks_parallel(tasks, blackboard)
            
            # Record in blackboard
            if "assessments" not in blackboard:
                blackboard["assessments"] = []
            
            for result in results:
                if result.get("status") == "completed":
                    clause_id = result.get("clause_id")
                    blackboard["assessments"].append({
                        "clause_id": clause_id,
                        "risk_level": result.get("risk_level"),
                        "rationale": result.get("rationale"),
                        "policy_refs": result.get("policy_refs")
                    })

                    duration_seconds = result.get("duration_seconds")
                    blackboard.setdefault("history", []).append({
                        "step": "risk_analysis_clause",
                        "step_id": clause_id or result.get("task_id"),
                        "agent": self.name,
                        "status": "completed",
                        "timestamp": task.get("timestamp", datetime.utcnow().isoformat()),
                        "prompt": display_prompts.get(clause_id) or result.get("prompt"),
                        "clause_id": clause_id,
                        "clause_text": display_texts.get(clause_id),
                        "duration_seconds": duration_seconds,
                        "duration_ms": round(duration_seconds * 1000, 3) if isinstance(duration_seconds, (int, float)) else None,
                        "output": {
                            "risk_level": result.get("risk_level"),
                            "rationale": result.get("rationale"),
                            "policy_refs": result.get("policy_refs"),
                        },
                    })
            
            # Record execution in history
            if "history" not in blackboard:
                blackboard["history"] = []

            blackboard["history"].append({
                "step": "manager_execution",
                "agent": self.name,
                "status": "completed",
                "timestamp": task.get("timestamp", "unknown"),
                "output": {"assessments_count": len(results)}
            })
            
            self.status = AgentStatus.SUCCESS
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output={"assessments_count": len(results)}
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )

    async def _process_tasks_parallel(self, tasks: List[Dict[str, Any]], blackboard: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process tasks in parallel using ThreadPoolExecutor"""
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                loop.run_in_executor(executor, self._process_single_task, task, blackboard)
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

    def _process_single_task(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single task (runs in thread)"""
        try:
            task_type = task.get("type", "risk_assessment")
            
            if task_type == "risk_assessment":
                clause_text = task.get("clause_text", "")
                policy_rules = task.get("policy_rules", {})
                display_text = task.get("display_text") or clause_text

                start_time = time.time()
                # Use the existing risk analysis function
                log_metadata = _build_log_metadata(
                    blackboard,
                    task.get("clause_id"),
                    source="manager_worker_new.WorkerAgent",
                    task=task,
                )
                analysis_result = analyze_risk_with_openai(
                    clause_text,
                    policy_rules,
                    log_metadata=log_metadata,
                )
                normalized_level = (analysis_result.get("risk_level") or "UNKNOWN").strip().upper()
                analysis_result["risk_level"] = normalized_level
                duration_seconds = round(time.time() - start_time, 6)

                display_prompt = task.get("display_prompt")
                if display_prompt:
                    analysis_result["prompt"] = display_prompt
                elif not analysis_result.get("prompt"):
                    analysis_result["prompt"] = build_risk_prompt(clause_text, policy_rules)
                
                return {
                    "task_id": task.get("task_id"),
                    "clause_id": task.get("clause_id"),
                    "risk_level": normalized_level,
                    "rationale": analysis_result["rationale"],
                    "policy_refs": analysis_result["policy_refs"],
                    "prompt": analysis_result.get("prompt"),
                    "duration_seconds": duration_seconds,
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


class WorkerAgent(Agent):
    """Worker agent for specific task execution using the new Agent Framework"""
    
    def __init__(self):
        super().__init__(
            name="worker-agent",
            role="task_executor",
            capabilities=["execute_specific_task", "process_clause", "assess_risk"],
            description="Executes specific tasks assigned by the manager"
        )
    
    async def execute(self, task: Dict[str, Any], blackboard: Dict[str, Any]) -> AgentResult:
        """Execute a specific task"""
        self.status = AgentStatus.RUNNING
        
        try:
            task_type = task.get("type", "risk_assessment")
            
            if task_type == "risk_assessment":
                clause_text = task.get("clause_text", "")
                policy_rules = task.get("policy_rules", {})
                display_text = task.get("display_text") or clause_text

                start_time = time.time()
                # Use the existing risk analysis function
                log_metadata = _build_log_metadata(
                    blackboard,
                    task.get("clause_id"),
                    source="manager_worker_new.ManagerAgent",
                    task=task,
                )
                analysis_result = analyze_risk_with_openai(
                    clause_text,
                    policy_rules,
                    log_metadata=log_metadata,
                )
                normalized_level = (analysis_result.get("risk_level") or "UNKNOWN").strip().upper()
                analysis_result["risk_level"] = normalized_level
                duration_seconds = round(time.time() - start_time, 6)

                display_prompt = task.get("display_prompt")
                if display_prompt:
                    analysis_result["prompt"] = display_prompt
                elif not analysis_result.get("prompt"):
                    analysis_result["prompt"] = build_risk_prompt(clause_text, policy_rules)
                
                result = {
                    "task_id": task.get("task_id"),
                    "clause_id": task.get("clause_id"),
                    "risk_level": normalized_level,
                    "rationale": analysis_result["rationale"],
                    "policy_refs": analysis_result["policy_refs"],
                    "prompt": analysis_result.get("prompt"),
                    "duration_seconds": duration_seconds,
                    "status": "completed"
                }
                
                # Update blackboard with the result
                if "assessments" not in blackboard:
                    blackboard["assessments"] = []
                
                blackboard["assessments"].append({
                    "clause_id": task.get("clause_id"),
                    "risk_level": analysis_result["risk_level"],
                    "rationale": analysis_result["rationale"],
                    "policy_refs": analysis_result["policy_refs"]
                })

                blackboard.setdefault("history", []).append({
                    "step": "risk_analysis_clause",
                    "step_id": task.get("clause_id") or task.get("task_id"),
                    "agent": self.name,
                    "status": "completed",
                    "timestamp": task.get("timestamp", datetime.utcnow().isoformat()),
                    "prompt": analysis_result.get("prompt"),
                    "clause_id": task.get("clause_id"),
                    "clause_text": display_text,
                    "duration_seconds": duration_seconds,
                    "duration_ms": round(duration_seconds * 1000, 3) if duration_seconds is not None else None,
                    "output": {
                        "risk_level": analysis_result["risk_level"],
                        "rationale": analysis_result["rationale"],
                        "policy_refs": analysis_result["policy_refs"],
                    },
                })

                self.status = AgentStatus.SUCCESS
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.SUCCESS,
                    output=result
                )
                
            else:
                self.status = AgentStatus.FAILED
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.FAILED,
                    error=f"Unknown task type: {task_type}"
                )
                
        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )


async def manager_worker_workflow(blackboard: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the manager-worker workflow using the new Agent Framework
    """
    from app.agents import Team, Coordinator
    from app.agents.team import TeamPattern
    
    # Create a team for manager-worker pattern
    team = Team(
        name="manager_worker_team_runtime",
        pattern=TeamPattern.MANAGER_WORKER
    )
    
    # Add the manager agent and multiple worker agents
    manager = ManagerAgent()
    team.add_agent(manager)
    
    # Add multiple worker agents
    for i in range(3):  # 3 workers
        worker = WorkerAgent()
        worker.name = f"worker-agent-{i}"
        team.add_agent(worker)
    
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