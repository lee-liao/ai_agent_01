from pathlib import Path
from tempfile import TemporaryDirectory

from app.agents.agent import ParserAgent, RiskAnalyzerAgent
from app.agents.coordinator import Coordinator
from app.agents.team import Team, TeamPattern
from app.agents.team_store import TeamStore


def _build_sample_team(name: str = "sample_team") -> Team:
    team = Team(name=name, pattern=TeamPattern.SEQUENTIAL, description="Test team")
    team.add_agent(ParserAgent())
    team.add_agent(RiskAnalyzerAgent())
    return team


def test_team_store_roundtrip() -> None:
    with TemporaryDirectory() as tmp_dir:
        store = TeamStore(directory=Path(tmp_dir))
        team = _build_sample_team()

        store.save_teams({team.name: team})

        assert store.file_path.exists()

        loaded = store.load_teams()

        assert len(loaded) == 1
        restored = loaded[0]
        assert restored.name == team.name
        assert restored.pattern == team.pattern
        assert len(restored.agents) == 2
        assert isinstance(restored.agents[0], ParserAgent)
        assert isinstance(restored.agents[1], RiskAnalyzerAgent)


def test_coordinator_loads_from_store() -> None:
    with TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        store = TeamStore(directory=base_path)
        coordinator = Coordinator(team_store=store)
        team = _build_sample_team()
        coordinator.register_team(team)

        # Ensure teams persisted
        assert store.file_path.exists()

        # New coordinator instance uses same store and loads teams
        restored_store = TeamStore(directory=base_path)
        restored_coordinator = Coordinator(team_store=restored_store)
        loaded = restored_coordinator.load_teams_from_store(replace_existing=True)

        assert loaded is True
        assert team.name in restored_coordinator.teams
        restored_team = restored_coordinator.teams[team.name]
        assert restored_team.pattern == team.pattern
        assert len(restored_team.agents) == 2
