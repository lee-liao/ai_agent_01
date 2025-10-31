"""
Team Class

A Team is a collection of agents that work together on a common goal.
Teams can be organized in different patterns:
- Manager-Worker: One manager delegates to multiple workers
- Pipeline: Agents execute in sequence
- Parallel: Agents execute simultaneously
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from .agent import Agent, AgentStatus, AgentResult


class TeamPattern(str, Enum):
    """Team execution patterns"""
    SEQUENTIAL = "sequential"  # Agents execute one after another
    PARALLEL = "parallel"      # Agents execute simultaneously
    MANAGER_WORKER = "manager_worker"  # Manager delegates to workers
    PIPELINE = "pipeline"      # Output of one agent feeds into next


class Team:
    """
    A Team coordinates multiple agents working together.
    
    Example:
        # Create a document review team
        team = Team(
            name="document_review_team",
            pattern=TeamPattern.SEQUENTIAL
        )
        
        # Add agents
        team.add_agent(ParserAgent())
        team.add_agent(RiskAnalyzerAgent())
        team.add_agent(RedlineGeneratorAgent())
        
        # Execute team
        result = team.execute(task, blackboard)
    """
    
    def __init__(
        self,
        name: str,
        pattern: TeamPattern = TeamPattern.SEQUENTIAL,
        description: Optional[str] = None
    ):
        """
        Initialize a Team.
        
        Args:
            name: Unique identifier for this team
            pattern: Execution pattern (sequential, parallel, etc.)
            description: Optional description of team purpose
        """
        self.name = name
        self.pattern = pattern
        self.description = description or f"Team: {name}"
        self.agents: List[Agent] = []
        self.execution_history: List[Dict[str, Any]] = []
    
    def add_agent(self, agent: Agent) -> None:
        """
        Add an agent to the team.
        
        Args:
            agent: Agent instance to add
        """
        self.agents.append(agent)
    
    def remove_agent(self, agent_name: str) -> bool:
        """
        Remove an agent from the team.
        
        Args:
            agent_name: Name of agent to remove
            
        Returns:
            True if agent was removed, False if not found
        """
        for i, agent in enumerate(self.agents):
            if agent.name == agent_name:
                self.agents.pop(i)
                return True
        return False
    
    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """
        Get an agent by name.
        
        Args:
            agent_name: Name of agent to retrieve
            
        Returns:
            Agent instance or None if not found
        """
        for agent in self.agents:
            if agent.name == agent_name:
                return agent
        return None
    
    def execute(
        self,
        task: Dict[str, Any],
        blackboard: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the team based on its pattern.
        
        Args:
            task: Task specification
            blackboard: Shared state/memory
            
        Returns:
            Execution summary with results from all agents
        """
        if self.pattern == TeamPattern.SEQUENTIAL:
            return self._execute_sequential(task, blackboard)
        elif self.pattern == TeamPattern.PARALLEL:
            return self._execute_parallel(task, blackboard)
        elif self.pattern == TeamPattern.MANAGER_WORKER:
            return self._execute_manager_worker(task, blackboard)
        elif self.pattern == TeamPattern.PIPELINE:
            return self._execute_pipeline(task, blackboard)
        else:
            raise ValueError(f"Unknown team pattern: {self.pattern}")
    
    def _execute_sequential(
        self,
        task: Dict[str, Any],
        blackboard: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute agents one after another in order.
        
        Each agent can read the output of previous agents from the blackboard.
        """
        results = []
        
        for agent in self.agents:
            # Execute agent
            result = agent.execute(task, blackboard)
            results.append(result.dict())
            
            # Record in history
            self.execution_history.append({
                "agent": agent.name,
                "status": result.status.value,
                "output": result.output
            })
            
            # Stop if agent failed
            if result.status == AgentStatus.FAILED:
                break
        
        return {
            "team": self.name,
            "pattern": self.pattern.value,
            "results": results,
            "success": all(r["status"] == AgentStatus.SUCCESS.value for r in results)
        }
    
    def _execute_parallel(
        self,
        task: Dict[str, Any],
        blackboard: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute all agents simultaneously using asyncio.gather.
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        async def _execute_single_agent(agent, task, blackboard):
            """Helper to execute a single agent and return its result"""
            try:
                result = await agent.execute(task, blackboard)
                return result
            except Exception as e:
                from app.agents.agent import AgentResult, AgentStatus
                return AgentResult(
                    agent_name=agent.name,
                    status=AgentStatus.FAILED,
                    error=str(e)
                )
        
        # Execute agents in parallel using asyncio.gather
        agent_coroutines = [
            _execute_single_agent(agent, task, blackboard)
            for agent in self.agents
        ]
        
        # Note: In a real async environment, we would await this directly.
        # For compatibility with sync contexts, we'll use asyncio.run when possible
        # However, since this might be called from sync context, we'll use a different approach
        
        # Using ThreadPoolExecutor approach for compatibility
        import concurrent.futures
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            # Submit all agent execution tasks
            future_to_agent = {
                executor.submit(self._execute_agent_sync, agent, task, blackboard): agent 
                for agent in self.agents
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_agent):
                result = future.result()
                results.append(result)
        
        return {
            "team": self.name,
            "pattern": self.pattern.value,
            "results": [r.dict() if hasattr(r, 'dict') else r for r in results],
            "success": all(
                (r.status.value if hasattr(r, 'status') else r.get('status')) == 'success' 
                for r in results
            )
        }
    
    def _execute_agent_sync(self, agent, task, blackboard):
        """Helper method to execute an agent synchronously for thread pool"""
        import asyncio
        
        # Create a new event loop for each thread if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop exists in this thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async execute method
        if hasattr(agent, 'execute') and asyncio.iscoroutinefunction(agent.execute):
            result = loop.run_until_complete(agent.execute(task, blackboard))
        else:
            # Fallback for non-async agents
            result = agent.execute(task, blackboard)
        
        return result
    
    def _execute_manager_worker(
        self,
        task: Dict[str, Any],
        blackboard: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manager-Worker pattern: First agent (manager) decomposes task into subtasks,
        then workers execute subtasks in parallel, and manager aggregates results.
        """
        if not self.agents:
            return {"error": "No agents in team"}
        
        # First agent is the manager, others are workers
        manager = self.agents[0]
        workers = self.agents[1:] if len(self.agents) > 1 else []
        
        results = []
        
        # Manager plans the work and decomposes task (execute synchronously)
        try:
            manager_result = manager.execute(task, blackboard)
            results.append(manager_result.dict() if hasattr(manager_result, 'dict') else manager_result)
            
            # Check if manager was successful before proceeding with workers
            manager_success = (manager_result.status.value if hasattr(manager_result, 'status') else 
                              manager_result.get('status', 'failed')) == 'success'
            
            if not manager_success:
                return {
                    "team": self.name,
                    "pattern": self.pattern.value,
                    "results": results,
                    "success": False
                }
            
            def _execute_worker_stage(agent_group: List[Agent]) -> List[Dict[str, Any]]:
                if not agent_group:
                    return []

                import concurrent.futures

                stage_results: List[Dict[str, Any]] = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(agent_group)) as executor:
                    future_to_worker = {
                        executor.submit(self._execute_agent_sync, worker, task, blackboard): worker
                        for worker in agent_group
                    }

                    for future in concurrent.futures.as_completed(future_to_worker):
                        worker_result = future.result()
                        stage_results.append(worker_result.dict() if hasattr(worker_result, "dict") else worker_result)

                return stage_results

            risk_workers: List[Agent] = []
            redline_workers: List[Agent] = []
            other_workers: List[Agent] = []

            for worker in workers:
                capabilities = set(getattr(worker, "capabilities", []) or [])
                if {"assess_risk", "policy_check"} & capabilities:
                    risk_workers.append(worker)
                elif {"generate_redlines", "create_proposals"} & capabilities:
                    redline_workers.append(worker)
                else:
                    other_workers.append(worker)

            # Run risk assessment stage before generating redlines so assessments populate the blackboard
            risk_results = _execute_worker_stage(risk_workers)
            results.extend(risk_results)

            def _is_successful(entry: Dict[str, Any]) -> bool:
                status_value = entry.get("status") if isinstance(entry, dict) else None
                if status_value is None and hasattr(entry, "status"):
                    status_value = getattr(entry.status, "value", None)
                if isinstance(status_value, str):
                    return status_value.lower() in {"success", "completed"}
                return False

            risk_stage_success = all(_is_successful(res) for res in risk_results) if risk_results else True

            other_results = _execute_worker_stage(other_workers)
            results.extend(other_results)

            if risk_stage_success:
                results.extend(_execute_worker_stage(redline_workers))
            
            # Finally, manager aggregates results (if manager has aggregation capability)
            if hasattr(manager, 'aggregate_results'):
                try:
                    final_result = manager.aggregate_results(task, blackboard)
                    results.append(final_result.dict() if hasattr(final_result, 'dict') else final_result)
                except Exception:
                    pass  # If aggregation fails, continue with previous results
            
        except Exception as e:
            from app.agents.agent import AgentResult, AgentStatus
            error_result = AgentResult(
                agent_name=manager.name,
                status=AgentStatus.FAILED,
                error=str(e)
            )
            results.append(error_result.dict())
        
        def _extract_status(entry: Dict[str, Any]) -> Optional[str]:
            if isinstance(entry, dict):
                return entry.get("status")
            if hasattr(entry, "status"):
                status_attr = getattr(entry.status, "value", None)
                if status_attr is not None:
                    return status_attr
            return None

        success = all(
            (_extract_status(r) or "failed").lower() in {"success", "completed"}
            for r in results
        )
        
        return {
            "team": self.name,
            "pattern": self.pattern.value,
            "results": results,
            "success": success
        }
    
    def _execute_pipeline(
        self,
        task: Dict[str, Any],
        blackboard: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Pipeline pattern: Output of each agent becomes input for next.
        
        Similar to sequential, but explicitly passes data between agents.
        """
        results = []
        current_input = task
        
        for agent in self.agents:
            # Execute agent with current input
            result = agent.execute(current_input, blackboard)
            results.append(result.dict())
            
            # Use agent output as input for next agent
            if result.output:
                current_input = {**current_input, **result.output}
            
            # Stop if agent failed
            if result.status == AgentStatus.FAILED:
                break
        
        return {
            "team": self.name,
            "pattern": self.pattern.value,
            "results": results,
            "success": all(r["status"] == AgentStatus.SUCCESS.value for r in results)
        }
    
    def get_capabilities(self) -> List[str]:
        """
        Get all capabilities available in this team.
        
        Returns:
            List of all unique capabilities across all agents
        """
        capabilities = set()
        for agent in self.agents:
            capabilities.update(agent.capabilities)
        return list(capabilities)
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get team information for debugging/monitoring.
        
        Returns:
            Dictionary with team metadata
        """
        return {
            "name": self.name,
            "pattern": self.pattern.value,
            "description": self.description,
            "agent_count": len(self.agents),
            "agents": [agent.get_info() for agent in self.agents],
            "capabilities": self.get_capabilities()
        }

