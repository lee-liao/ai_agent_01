"""Utilities for persisting and restoring team definitions."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Type

from app.agents.agent import (
    Agent,
    ParserAgent,
    RedlineGeneratorAgent,
    RiskAnalyzerAgent,
)
from app.agents.reviewer_referee_agents import RefereeAgent, ReviewerAgent
from app.agents.team import Team, TeamPattern


logger = logging.getLogger(__name__)


_DEFAULT_STORE_DIR = Path(__file__).resolve().parents[3] / "data" / "team"


@dataclass(frozen=True)
class SerializedAgent:
    """Representation of an agent for persistence purposes."""

    type: str
    module: str
    init_params: Optional[Dict[str, object]] = None


class TeamStore:
    """Persist teams to disk and restore them on startup."""

    def __init__(self, directory: Optional[Path] = None, filename: str = "teams.json") -> None:
        self._directory = Path(directory or _DEFAULT_STORE_DIR)
        self._directory.mkdir(parents=True, exist_ok=True)
        self._file_path = self._directory / filename

        self._agent_factories: Dict[str, Type[Agent]] = {
            "ParserAgent": ParserAgent,
            "RiskAnalyzerAgent": RiskAnalyzerAgent,
            "RedlineGeneratorAgent": RedlineGeneratorAgent,
            "ReviewerAgent": ReviewerAgent,
            "RefereeAgent": RefereeAgent,
        }

    @property
    def file_path(self) -> Path:
        return self._file_path

    def save_teams(self, teams: Dict[str, Team]) -> None:
        """Persist the supplied teams to disk."""
        payload = {
            "teams": [self._serialize_team(team) for team in sorted(teams.values(), key=lambda t: t.name)]
        }

        tmp_path = self._file_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        tmp_path.replace(self._file_path)

    def load_teams(self) -> List[Team]:
        """Load teams from disk, returning empty list when file missing."""
        if not self._file_path.exists():
            return []

        try:
            with self._file_path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode team store JSON: %s", exc)
            return []

        raw_teams = raw.get("teams", [])
        teams: List[Team] = []
        for entry in raw_teams:
            team = self._deserialize_team(entry)
            if team:
                teams.append(team)
        return teams

    def _serialize_team(self, team: Team) -> Dict[str, object]:
        return {
            "name": team.name,
            "pattern": team.pattern.value,
            "description": team.description,
            "agents": [self._serialize_agent(agent).__dict__ for agent in team.agents],
        }

    def _serialize_agent(self, agent: Agent) -> SerializedAgent:
        return SerializedAgent(
            type=agent.__class__.__name__,
            module=agent.__class__.__module__,
            init_params=getattr(agent, "init_params", None),
        )

    def _deserialize_team(self, data: Dict[str, object]) -> Optional[Team]:
        try:
            pattern = TeamPattern(data.get("pattern", TeamPattern.SEQUENTIAL.value))
            team = Team(
                name=data["name"],
                pattern=pattern,
                description=data.get("description"),
            )

            agent_entries = data.get("agents", [])
            for agent_data in agent_entries:
                agent = self._instantiate_agent(agent_data)
                if agent:
                    team.add_agent(agent)

            return team
        except KeyError as exc:
            logger.error("Invalid team entry missing keys: %s", exc)
        except ValueError as exc:
            logger.error("Failed to deserialize team pattern: %s", exc)
        return None

    def _instantiate_agent(self, data: Dict[str, object]) -> Optional[Agent]:
        agent_type = data.get("type")
        if not agent_type:
            logger.warning("Encountered agent entry without type: %s", data)
            return None

        factory = self._agent_factories.get(agent_type)
        if factory:
            try:
                params = data.get("init_params") if isinstance(data, dict) else None
                return factory(**params) if isinstance(params, dict) else factory()
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to instantiate agent %s via registry: %s", agent_type, exc)

        module_path = data.get("module")
        if module_path:
            try:
                module = __import__(module_path, fromlist=[agent_type])
                cls = getattr(module, agent_type)
                params = data.get("init_params") if isinstance(data, dict) else None
                return cls(**params) if isinstance(params, dict) else cls()
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed dynamic import for agent %s.%s: %s", module_path, agent_type, exc)

        logger.warning("Unknown agent type '%s' encountered in team store", agent_type)
        return None


def serialize_teams(teams: Iterable[Team], store: TeamStore) -> None:
    """Helper to persist an iterable of teams using the provided store."""

    team_map = {team.name: team for team in teams}
    store.save_teams(team_map)
