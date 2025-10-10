from datetime import datetime
from types import ModuleType
import sys

from fastapi.testclient import TestClient

# Provide lightweight stubs for optional modules used during import
sys.modules.setdefault("markdown", ModuleType("markdown"))

from app.agents.coordinator import RunStatus
from app.main import app, coordinator


client = TestClient(app)


def _seed_run(run_id: str = "test_run_risk") -> str:
    now = datetime.utcnow().isoformat()
    doc_id = "doc_test"

    coordinator.blackboards[run_id] = {
        "run_id": run_id,
        "doc_id": doc_id,
        "agent_path": "manager_worker",
        "document_text": "Sample document",
        "clauses": [
            {
                "clause_id": "clause_1",
                "heading": "Limitation of Liability",
                "text": "Unlimited liability for all damages.",
            },
            {
                "clause_id": "clause_2",
                "heading": "Payment Terms",
                "text": "Net 30 payment terms apply.",
            },
        ],
        "assessments": [
            {
                "clause_id": "clause_1",
                "risk_level": "HIGH",
                "rationale": "Contains unlimited liability language.",
                "policy_refs": ["POL-001"],
            },
            {
                "clause_id": "clause_2",
                "risk_level": "LOW",
                "rationale": "Standard payment wording.",
                "policy_refs": ["POL-004"],
            },
        ],
        "history": [],
    }

    coordinator.runs[run_id] = {
        "run_id": run_id,
        "doc_id": doc_id,
        "agent_path": "manager_worker",
        "status": RunStatus.AWAITING_RISK_APPROVAL.value,
        "created_at": now,
        "updated_at": now,
    }

    return run_id


def _cleanup_run(run_id: str) -> None:
    coordinator.blackboards.pop(run_id, None)
    coordinator.runs.pop(run_id, None)


def test_pending_runs_endpoint_returns_summary():
    run_id = _seed_run()
    try:
        response = client.get("/api/hitl/pending-runs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(item["run_id"] == run_id for item in data)
        summary = next(item for item in data if item["run_id"] == run_id)
        assert summary["high_risk_count"] == 1
        assert summary["medium_risk_count"] == 0
        assert summary["low_risk_count"] == 1
        assert summary["total_assessments"] == 2
    finally:
        _cleanup_run(run_id)


def test_assessments_endpoint_returns_enriched_data():
    run_id = _seed_run()
    try:
        response = client.get(f"/api/hitl/runs/{run_id}/assessments")
        assert response.status_code == 200
        payload = response.json()
        assert payload["run_id"] == run_id
        assert len(payload["assessments"]) == 2
        entry = payload["assessments"][0]
        assert "clause_heading" in entry
        assert "recommended_action" in entry
        assert "impact_assessment" in entry
    finally:
        _cleanup_run(run_id)


def test_risk_approve_updates_run_status():
    run_id = _seed_run()
    try:
        payload = {
            "run_id": run_id,
            "items": [
                {"clause_id": "clause_1", "decision": "reject", "comments": "Needs cap."},
                {"clause_id": "clause_2", "decision": "approve"},
            ],
        }

        response = client.post("/api/hitl/risk-approve", json=payload)
        assert response.status_code == 200
        meta = coordinator.get_run(run_id)
        assert meta["status"] == RunStatus.AWAITING_FINAL_APPROVAL.value
        blackboard = coordinator.get_blackboard(run_id)
        assert blackboard["risk_approval"]["approved"] == ["clause_2"]
        assert blackboard["risk_approval"]["rejected"] == ["clause_1"]
        assert blackboard["risk_approval"]["comments"]["clause_1"] == "Needs cap."
    finally:
        _cleanup_run(run_id)
