"""
Coordinator Class

The Coordinator orchestrates multi-agent workflows and manages the Blackboard (shared memory).
It handles:
- Task routing to appropriate teams/agents
- Blackboard state management
- Execution history tracking
- HITL (Human-in-the-Loop) gate coordination
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from .team import Team
from .agent import Agent
from .team_store import TeamStore


class RunStatus(str, Enum):
    """Status of a run"""
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_RISK_APPROVAL = "awaiting_risk_approval"
    AWAITING_FINAL_APPROVAL = "awaiting_final_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class Coordinator:
    """
    Orchestrates multi-agent workflows with Blackboard pattern.
    
    The Coordinator:
    1. Manages the Blackboard (shared memory)
    2. Routes tasks to appropriate teams
    3. Tracks execution history
    4. Handles HITL gates
    5. Maintains run state
    
    Example:
        # Create coordinator
        coordinator = Coordinator()
        
        # Register a team
        team = Team("review_team", TeamPattern.SEQUENTIAL)
        team.add_agent(ParserAgent())
        team.add_agent(RiskAnalyzerAgent())
        coordinator.register_team(team)
        
        # Start a run
        run_id = coordinator.start_run(
            doc_id="doc_001",
            document_text="...",
            agent_path="sequential"
        )
        
        # Get blackboard state
        state = coordinator.get_blackboard(run_id)
    """
    
    def __init__(self, team_store: Optional[TeamStore] = None):
        """Initialize the Coordinator."""
        # Blackboard storage (in-memory for classroom, use DB in production)
        self.blackboards: Dict[str, Dict[str, Any]] = {}
        
        # Registered teams
        self.teams: Dict[str, Team] = {}

        # Persistence for team definitions
        self.team_store = team_store
        
        # Run metadata
        self.runs: Dict[str, Dict[str, Any]] = {}
    
    def register_team(self, team: Team, *, persist: bool = True) -> None:
        """
        Register a team with the coordinator.
        
        Args:
            team: Team instance to register
        """
        self.teams[team.name] = team
        if persist:
            self.persist_teams()

    def persist_teams(self) -> None:
        """Persist registered teams using the configured team store."""
        if self.team_store:
            self.team_store.save_teams(self.teams)

    def load_teams_from_store(self, replace_existing: bool = False) -> bool:
        """Load teams from the persistence store."""
        if not self.team_store:
            return False

        teams = self.team_store.load_teams()
        if not teams:
            return False

        if replace_existing:
            self.teams.clear()

        for team in teams:
            # Avoid re-persisting while loading
            self.register_team(team, persist=False)

        return True
    
    def get_team(self, team_name: str) -> Optional[Team]:
        """
        Get a registered team by name.
        
        Args:
            team_name: Name of team to retrieve
            
        Returns:
            Team instance or None if not found
        """
        return self.teams.get(team_name)
    
    def start_run(
        self,
        doc_id: str,
        document_text: str,
        agent_path: str,
        playbook_id: Optional[str] = None,
        policy_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new document review run.
        
        Args:
            doc_id: Document identifier
            document_text: Full text of the document
            agent_path: Which team/pattern to use (e.g., "manager_worker")
            playbook_id: Optional playbook identifier
            policy_rules: Optional policy rules to apply
            
        Returns:
            run_id: Unique identifier for this run
        """
        # Generate run ID
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{doc_id}"
        
        # Initialize blackboard for this run
        self.blackboards[run_id] = {
            "run_id": run_id,
            "doc_id": doc_id,
            "document_text": document_text,
            "agent_path": agent_path,
            "playbook_id": playbook_id,
            "policy_rules": policy_rules or {},
            "clauses": [],
            "assessments": [],
            "proposals": [],
            "history": [],
            "checkpoints": [],  # Initialize checkpoints
            "created_at": datetime.now().isoformat()
        }
        
        # Initialize run metadata
        self.runs[run_id] = {
            "run_id": run_id,
            "doc_id": doc_id,
            "agent_path": agent_path,
            "status": RunStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Save initial checkpoint
        self.save_checkpoint(run_id, "initial", self.blackboards[run_id])
        
        # Execute the team asynchronously (in production, use background task)
        self._execute_run(run_id, agent_path)
        
        return run_id
    
    def save_checkpoint(self, run_id: str, step: str, state: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save a checkpoint of the blackboard state.
        
        Args:
            run_id: Run identifier
            step: Step name for the checkpoint
            state: Optional state to save (if None, saves current blackboard state)
            
        Returns:
            True if checkpoint was saved successfully
        """
        blackboard = self.blackboards.get(run_id)
        if not blackboard:
            return False
        
        # Use provided state or current blackboard state
        checkpoint_state = state if state is not None else blackboard.copy()
        
        # Create checkpoint entry
        checkpoint = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "state": checkpoint_state
        }
        
        # Initialize checkpoints list if not exists
        if "checkpoints" not in blackboard:
            blackboard["checkpoints"] = []
        
        # Add checkpoint
        blackboard["checkpoints"].append(checkpoint)
        
        # Also update runs metadata
        if "checkpoints" not in self.runs[run_id]:
            self.runs[run_id]["checkpoints"] = []
        self.runs[run_id]["checkpoints"].append({
            "step": step,
            "timestamp": checkpoint["timestamp"]
        })
        
        return True
    
    def restore_checkpoint(self, run_id: str, checkpoint_index: int) -> bool:
        """
        Restore blackboard to a previous checkpoint.
        
        Args:
            run_id: Run identifier
            checkpoint_index: Index of checkpoint to restore (0 is oldest)
            
        Returns:
            True if restoration was successful
        """
        blackboard = self.blackboards.get(run_id)
        if not blackboard or "checkpoints" not in blackboard or checkpoint_index < 0:
            return False
        
        checkpoints = blackboard["checkpoints"]
        if checkpoint_index >= len(checkpoints):
            return False
        
        # Restore the blackboard state
        checkpoint = checkpoints[checkpoint_index]
        state_to_restore = checkpoint["state"]
        
        # Update the blackboard with checkpointed state
        self.blackboards[run_id] = state_to_restore
        # Also update the run status to reflect restoration
        self.runs[run_id]["status"] = RunStatus.RUNNING.value
        self.runs[run_id]["updated_at"] = datetime.now().isoformat()
        
        # Add history entry for restoration
        restored_state = self.blackboards[run_id]
        if "history" not in restored_state:
            restored_state["history"] = []
        restored_state["history"].append({
            "step": "checkpoint_restoration",
            "status": "success",
            "restored_from_step": checkpoint["step"],
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    def _execute_run(self, run_id: str, agent_path: str) -> None:
        """
        Execute a run using the specified agent path.
        
        Args:
            run_id: Run identifier
            agent_path: Team/pattern to use
        """
        blackboard = self.blackboards[run_id]
        
        # Update status
        self.runs[run_id]["status"] = RunStatus.RUNNING.value
        self.runs[run_id]["updated_at"] = datetime.now().isoformat()
        
        try:
            # Get the appropriate team
            team = self._get_team_for_path(agent_path)
            
            if not team:
                raise ValueError(f"No team found for agent path: {agent_path}")
            
            # Create task
            task = {
                "type": "review_document",
                "document_text": blackboard["document_text"],
                "document_id": blackboard["doc_id"],
                "policy_rules": blackboard["policy_rules"],
                "timestamp": datetime.now().isoformat()
            }
            
            # Execute team
            result = team.execute(task, blackboard)
            
            # Record execution in history
            blackboard["history"].append({
                "step": "team_execution",
                "team": team.name,
                "status": "success" if result["success"] else "failed",
                "timestamp": datetime.now().isoformat(),
                "details": result
            })
            
            # Check if we need HITL approval
            if self._needs_risk_approval(blackboard):
                self.runs[run_id]["status"] = RunStatus.AWAITING_RISK_APPROVAL.value
            else:
                self.runs[run_id]["status"] = RunStatus.AWAITING_FINAL_APPROVAL.value
            
        except Exception as e:
            # Record error
            blackboard["history"].append({
                "step": "execution_error",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            self.runs[run_id]["status"] = RunStatus.FAILED.value
        
        self.runs[run_id]["updated_at"] = datetime.now().isoformat()
    
    def _get_team_for_path(self, agent_path: str) -> Optional[Team]:
        """
        Get the team corresponding to an agent path.
        
        Args:
            agent_path: Path identifier (e.g., "manager_worker", "sequential")
            
        Returns:
            Team instance or None
        """
        # Map agent paths to team names
        path_mapping = {
            "manager_worker": "manager_worker_team",
            "planner_executor": "planner_executor_team",
            "reviewer_referee": "reviewer_referee_team",
            "sequential": "sequential_team"
        }
        
        team_name = path_mapping.get(agent_path)
        return self.teams.get(team_name) if team_name else None
    
    def _needs_risk_approval(self, blackboard: Dict[str, Any]) -> bool:
        """Check if the run needs human approval at the risk gate."""
        assessments = blackboard.get("assessments", [])

        if not assessments:
            return False

        for assessment in assessments:
            level = (assessment.get("risk_level") or "").upper()
            if level in {"HIGH", "MEDIUM", "LOW"}:
                return True

        return False
    
    def get_blackboard(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the blackboard state for a run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            Blackboard dictionary or None if not found
        """
        return self.blackboards.get(run_id)
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get run metadata.
        
        Args:
            run_id: Run identifier
            
        Returns:
            Run metadata dictionary or None if not found
        """
        return self.runs.get(run_id)
    
    def list_runs(self) -> List[Dict[str, Any]]:
        """
        List all runs.
        
        Returns:
            List of run metadata dictionaries
        """
        return list(self.runs.values())
    
    def save_risk_decisions(
        self,
        run_id: str,
        decisions: List[Dict[str, Any]]
    ) -> bool:
        blackboard = self.blackboards.get(run_id)
        run = self.runs.get(run_id)

        if not blackboard or not run:
            return False

        progress = blackboard.setdefault("risk_gate_progress", {})
        timestamp = datetime.now().isoformat()

        for item in decisions:
            clause_id = item.get("clause_id")
            if not clause_id:
                continue

            decision = (item.get("decision") or "review").lower()
            comments = item.get("comments")

            if decision not in {"approve", "reject", "review"}:
                continue

            if decision == "review" and (comments is None or comments == ""):
                progress.pop(clause_id, None)
                continue

            entry = progress.setdefault(clause_id, {})
            entry["decision"] = decision
            entry["updated_at"] = timestamp
            if comments is None:
                entry.pop("comments", None)
            else:
                entry["comments"] = comments

        run["updated_at"] = datetime.now().isoformat()
        return True

    def get_risk_decisions(self, run_id: str) -> Dict[str, Any]:
        blackboard = self.blackboards.get(run_id)
        if not blackboard:
            return {}
        return blackboard.get("risk_gate_progress", {})

    def approve_risk(
        self,
        run_id: str,
        approved_clauses: List[str],
        rejected_clauses: List[str],
        comments: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Approve/reject clauses at the risk gate (HITL).
        
        Args:
            run_id: Run identifier
            approved_clauses: List of approved clause IDs
            rejected_clauses: List of rejected clause IDs
            comments: Optional comments per clause
            
        Returns:
            True if approval was recorded successfully
        """
        blackboard = self.blackboards.get(run_id)
        run = self.runs.get(run_id)
        
        if not blackboard or not run:
            return False
        
        # Record approval decision
        blackboard["risk_approval"] = {
            "approved": approved_clauses,
            "rejected": rejected_clauses,
            "comments": comments or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Update history
        blackboard["history"].append({
            "step": "risk_gate_approval",
            "status": "approved",
            "approved_count": len(approved_clauses),
            "rejected_count": len(rejected_clauses),
            "timestamp": datetime.now().isoformat()
        })
        
        # Update run status
        run["status"] = RunStatus.AWAITING_FINAL_APPROVAL.value
        run["updated_at"] = datetime.now().isoformat()
        
        return True
    
    def approve_final(
        self,
        run_id: str,
        approved_proposals: List[str],
        rejected_proposals: List[str],
        notes: Optional[str] = None
    ) -> bool:
        """
        Final approval of redline proposals (HITL).
        
        Args:
            run_id: Run identifier
            approved_proposals: List of approved proposal IDs
            rejected_proposals: List of rejected proposal IDs
            notes: Optional approval notes
            
        Returns:
            True if approval was recorded successfully
        """
        blackboard = self.blackboards.get(run_id)
        run = self.runs.get(run_id)
        
        if not blackboard or not run:
            return False
        
        # Record approval decision
        blackboard["final_approval"] = {
            "approved": approved_proposals,
            "rejected": rejected_proposals,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update history
        blackboard["history"].append({
            "step": "final_gate_approval",
            "status": "approved",
            "approved_count": len(approved_proposals),
            "rejected_count": len(rejected_proposals),
            "timestamp": datetime.now().isoformat()
        })
        
        # Update run status
        run["status"] = RunStatus.COMPLETED.value
        run["updated_at"] = datetime.now().isoformat()
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get coordinator statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_runs": len(self.runs),
            "registered_teams": len(self.teams),
            "active_blackboards": len(self.blackboards),
            "runs_by_status": self._count_runs_by_status()
        }
    
    def _count_runs_by_status(self) -> Dict[str, int]:
        """Count runs by status."""
        counts = {}
        for run in self.runs.values():
            status = run["status"]
            counts[status] = counts.get(status, 0) + 1
        return counts
