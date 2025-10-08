"""
Base classes and interfaces for multi-agent orchestration
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
import asyncio
from pydantic import BaseModel


class AgentMessage(BaseModel):
    """Message structure for agent communication"""
    agent_id: str
    message_type: str  # e.g., "request", "response", "update", "decision"
    content: Dict[str, Any]
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


class Blackboard(BaseModel):
    """Shared memory for agent coordination"""
    run_id: str
    clauses: List[Dict[str, Any]] = []
    assessments: List[Dict[str, Any]] = []
    proposals: List[Dict[str, Any]] = []
    decisions: List[Dict[str, Any]] = []
    artifacts: Dict[str, Any] = {}
    history: List[Dict[str, Any]] = []
    checkpoints: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

    def update_clauses(self, clauses: List[Dict[str, Any]]):
        self.clauses = clauses

    def add_assessment(self, assessment: Dict[str, Any]):
        self.assessments.append(assessment)

    def add_proposal(self, proposal: Dict[str, Any]):
        self.proposals.append(proposal)

    def add_decision(self, decision: Dict[str, Any]):
        self.decisions.append(decision)

    def add_artifact(self, key: str, value: Any):
        self.artifacts[key] = value

    def add_history(self, entry: Dict[str, Any]):
        self.history.append(entry)

    def set_checkpoint(self, key: str, value: Any):
        self.checkpoints[key] = value


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_id: str, blackboard: Blackboard):
        self.agent_id = agent_id
        self.blackboard = blackboard

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the agent's main function"""
        pass


class Tool(BaseModel):
    """Base class for tools that agents can use"""
    name: str
    description: str
    execute: Callable