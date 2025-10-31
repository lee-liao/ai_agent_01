"""
Manager-Worker agent pattern implementation
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from app.agents.base import BaseAgent, Blackboard
from app.utils.analysis import analyze_risk_with_openai, resolve_clause_texts, build_risk_prompt
from app.utils.logging import get_logger


logger = get_logger(__name__)


def _extract_log_context(blackboard: Blackboard) -> Dict[str, Any]:
    run_id = getattr(blackboard, "run_id", None)
    metadata = getattr(blackboard, "metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    replayed_from = metadata.get("replayed_from")
    context: Dict[str, Any] = {
        "run_id": run_id,
        "agent_path": metadata.get("agent_path") or "manager_worker",
        "mode": "replay" if replayed_from else "initial",
    }

    if replayed_from:
        context["original_run_id"] = replayed_from
    if metadata.get("doc_id"):
        context["doc_id"] = metadata["doc_id"]
    if metadata.get("playbook_id"):
        context["playbook_id"] = metadata["playbook_id"]

    return context


def _build_log_metadata(
    blackboard: Blackboard,
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

                start_time = time.time()
                log_metadata = _build_log_metadata(
                    self.blackboard,
                    task.get("clause_id"),
                    source="manager_worker.ManagerAgent",
                    task=task,
                )
                # Use the existing risk analysis function
                analysis_result = analyze_risk_with_openai(
                    clause_text,
                    policy_rules,
                    log_metadata=log_metadata,
                )
                duration_seconds = round(time.time() - start_time, 6)

                display_prompt = task.get("display_prompt")
                if display_prompt:
                    analysis_result["prompt"] = display_prompt
                elif not analysis_result.get("prompt"):
                    analysis_result["prompt"] = build_risk_prompt(clause_text, policy_rules)
                
                normalized_level = (analysis_result.get("risk_level") or "UNKNOWN").strip().upper()
                analysis_result["risk_level"] = normalized_level
                policy_refs = analysis_result.get("policy_refs")
                if not isinstance(policy_refs, list):
                    policy_refs = [policy_refs] if policy_refs else []
                analysis_result["policy_refs"] = policy_refs

                return {
                    "task_id": task.get("task_id"),
                    "clause_id": task.get("clause_id"),
                    "risk_level": normalized_level,
                    "rationale": analysis_result["rationale"],
                    "policy_refs": policy_refs,
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
            display_text = task.get("display_text") or clause_text

            start_time = time.time()
            log_metadata = _build_log_metadata(
                self.blackboard,
                task.get("clause_id"),
                source="manager_worker.WorkerAgent",
                task=task,
            )
            analysis_result = analyze_risk_with_openai(
                clause_text,
                policy_rules,
                log_metadata=log_metadata,
            )
            duration_seconds = round(time.time() - start_time, 6)

            display_prompt = task.get("display_prompt")
            if display_prompt:
                analysis_result["prompt"] = display_prompt
            elif not analysis_result.get("prompt"):
                analysis_result["prompt"] = build_risk_prompt(clause_text, policy_rules)

            normalized_level = (analysis_result.get("risk_level") or "UNKNOWN").strip().upper()
            analysis_result["risk_level"] = normalized_level
            policy_refs = analysis_result.get("policy_refs")
            if not isinstance(policy_refs, list):
                policy_refs = [policy_refs] if policy_refs else []
            analysis_result["policy_refs"] = policy_refs

            result = {
                "task_id": task.get("task_id"),
                "clause_id": task.get("clause_id"),
                "risk_level": normalized_level,
                "rationale": analysis_result["rationale"],
                "policy_refs": policy_refs,
                "prompt": analysis_result.get("prompt"),
                "duration_seconds": duration_seconds,
                "duration_ms": round(duration_seconds * 1000, 3),
                "status": "completed"
            }

            assessment = {
                "clause_id": task.get("clause_id"),
                "risk_level": normalized_level,
                "rationale": analysis_result["rationale"],
                "policy_refs": policy_refs,
            }
            self.blackboard.add_assessment(assessment)

            self.blackboard.add_history({
                "step": "risk_analysis_clause",
                "step_id": task.get("clause_id") or task.get("task_id"),
                "agent": self.agent_id,
                "status": "completed",
                "timestamp": task.get("timestamp", datetime.utcnow().isoformat()),
                "prompt": analysis_result.get("prompt"),
                "clause_id": task.get("clause_id"),
                "clause_text": display_text,
                "duration_seconds": duration_seconds,
                "duration_ms": round(duration_seconds * 1000, 3) if duration_seconds is not None else None,
                "output": {
                    "risk_level": normalized_level,
                    "rationale": analysis_result["rationale"],
                    "policy_refs": analysis_result["policy_refs"],
                },
            })

            return result
        else:
            return {
                "task_id": task.get("task_id"),
                "status": "unknown_task_type",
                "error": f"Unknown task type: {task_type}"
            }


async def manager_worker_workflow(blackboard: Blackboard) -> Dict[str, Any]:
    """Execute the manager-worker workflow"""
    run_id = getattr(blackboard, "run_id", None)
    start_time = time.time()
    logger.info("Manager-worker workflow started for run_id=%s", run_id or "unknown")

    # Create manager
    manager = ManagerAgent("manager-agent-1", blackboard)

    policy_rules = {}
    if isinstance(blackboard.metadata, dict):
        policy_rules = blackboard.metadata.get("policy_rules", {}) or {}
    document_text = getattr(blackboard, "document_text", "")
    if not document_text and isinstance(blackboard.metadata, dict):
        document_text = blackboard.metadata.get("document_text", "")

    normalized_texts = resolve_clause_texts(list(blackboard.clauses), document_text)
    display_texts: Dict[str, str] = {}
    display_prompts: Dict[str, str] = {}
    timestamp_now = datetime.utcnow().isoformat()
    
    # Prepare tasks from clauses in the blackboard
    tasks = []
    for clause in blackboard.clauses:
        clause_identifier = clause.get("id") or clause.get("clause_id")
        normalized_text = normalized_texts.get(clause_identifier) if clause_identifier else None
        analysis_text = normalized_text or clause.get("body") or clause.get("text", "")
        display_text = normalized_text or clause.get("body") or clause.get("text", "")
        display_prompt = build_risk_prompt(analysis_text, policy_rules)
        if clause_identifier:
            display_texts[clause_identifier] = display_text
            display_prompts[clause_identifier] = display_prompt
        task = {
            "task_id": f"task-{clause.get('id', 'unknown')}",
            "type": "risk_assessment",
            "clause_id": clause_identifier,
            "clause_text": analysis_text,
            "display_text": display_text,
            "display_prompt": display_prompt,
            "policy_rules": policy_rules,
            "timestamp": timestamp_now,
        }
        tasks.append(task)
    
    # Execute the workflow
    result = await manager.execute(tasks)

    assessments_generated: List[Dict[str, Any]] = []
    for entry in result.get("results", []):
        if entry.get("status") != "completed":
            continue

        clause_id = entry.get("clause_id") or entry.get("task_id")
        policy_refs = entry.get("policy_refs")
        if not isinstance(policy_refs, list):
            policy_refs = [policy_refs] if policy_refs else []

        assessment = {
            "clause_id": clause_id,
            "risk_level": entry.get("risk_level"),
            "rationale": entry.get("rationale"),
            "policy_refs": policy_refs,
        }
        assessments_generated.append(assessment)

        blackboard.add_history({
            "step": "risk_analysis_clause",
            "step_id": clause_id,
            "agent": manager.agent_id,
            "status": "completed",
            "timestamp": timestamp_now,
            "prompt": display_prompts.get(clause_id) or entry.get("prompt"),
            "clause_id": clause_id,
            "clause_text": display_texts.get(clause_id),
            "duration_seconds": entry.get("duration_seconds"),
            "duration_ms": (round(entry.get("duration_seconds") * 1000, 3)
                             if isinstance(entry.get("duration_seconds"), (int, float)) else None),
            "output": {
                "risk_level": entry.get("risk_level"),
                "rationale": entry.get("rationale"),
                "policy_refs": policy_refs,
            },
        })

    # Replace assessments with freshly generated set to keep downstream deltas accurate
    blackboard.assessments = assessments_generated

    # Reset proposals before regeneration to avoid stale entries
    blackboard.proposals = []

    # Generate redline proposals for high/medium risk clauses
    from app.agents.redline_generator import generate_redlines_for_run
    await generate_redlines_for_run(blackboard)

    end_time = time.time()
    duration_ms = round((end_time - start_time) * 1000, 3)
    logger.info(
        "Manager-worker workflow finished for run_id=%s in %.3f ms",
        run_id or "unknown",
        duration_ms,
    )

    return result