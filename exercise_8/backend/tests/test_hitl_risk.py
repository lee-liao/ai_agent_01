from datetime import datetime
from types import ModuleType
import sys

from fastapi.testclient import TestClient

# Provide lightweight stubs for optional modules used during import
sys.modules.setdefault("markdown", ModuleType("markdown"))

from app.agents.coordinator import RunStatus
from app.agents.agent import RiskAnalyzerAgent
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


def _seed_final_run(run_id: str = "test_run_final") -> str:
    run_id = _seed_run(run_id)
    blackboard = coordinator.blackboards[run_id]
    blackboard["proposals"] = [
        {
            "clause_id": "clause_1",
            "original_text": blackboard["clauses"][0]["text"],
            "proposed_text": "Liability capped at fees paid in prior 12 months.",
            "rationale": "Mitigates unlimited liability.",
            "policy_refs": ["POL-001"],
            "variant": "conservative",
        },
        {
            "clause_id": "clause_2",
            "original_text": blackboard["clauses"][1]["text"],
            "proposed_text": "Clarify payment remittance timeline.",
            "rationale": "Improves invoicing certainty.",
            "policy_refs": ["POL-004"],
            "variant": "moderate",
        },
    ]

    run = coordinator.runs[run_id]
    run["status"] = RunStatus.AWAITING_FINAL_APPROVAL.value
    run["updated_at"] = datetime.utcnow().isoformat()

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


def test_needs_risk_approval_flags_medium_and_low_levels():
    blackboard = {
        "assessments": [
            {"clause_id": "c1", "risk_level": "MEDIUM"},
            {"clause_id": "c2", "risk_level": "LOW"},
        ]
    }

    assert coordinator._needs_risk_approval(blackboard) is True


def test_risk_decision_progress_is_persisted_and_returned():
    run_id = _seed_run("test_run_progress")
    try:
        save_payload = {
            "items": [
                {"clause_id": "clause_1", "decision": "reject", "comments": "Needs cap"},
                {"clause_id": "clause_2", "decision": "approve"},
            ]
        }
        response = client.post(f"/api/hitl/runs/{run_id}/decisions", json=save_payload)
        assert response.status_code == 200
        saved = coordinator.get_blackboard(run_id).get("risk_gate_progress", {})
        assert saved["clause_1"]["decision"] == "reject"
        assert saved["clause_1"]["comments"] == "Needs cap"
        assert saved["clause_2"]["decision"] == "approve"

        refresh = client.get(f"/api/hitl/runs/{run_id}/assessments")
        assert refresh.status_code == 200
        payload = refresh.json()
        records = {item["clause_id"]: item for item in payload["assessments"]}
        assert records["clause_1"]["decision"] == "reject"
        assert records["clause_1"]["decision_comment"] == "Needs cap"
        assert records["clause_2"]["decision"] == "approve"

        clear_payload = {
            "items": [
                {"clause_id": "clause_1", "decision": "review", "comments": ""},
                {"clause_id": "clause_2", "decision": "review"},
            ]
        }
        clear_resp = client.post(f"/api/hitl/runs/{run_id}/decisions", json=clear_payload)
        assert clear_resp.status_code == 200
        cleared = coordinator.get_blackboard(run_id).get("risk_gate_progress", {})
        assert "clause_2" not in cleared
        assert "clause_1" not in cleared
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


def test_final_runs_endpoint_returns_summary():
    run_id = _seed_final_run()
    try:
        response = client.get("/api/hitl/final-runs")
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, list)
        entry = next(item for item in payload if item["run_id"] == run_id)
        assert entry["total_proposals"] == 2
        assert entry["high_risk_resolved"] >= 0
        assert entry["status"] == RunStatus.AWAITING_FINAL_APPROVAL.value
    finally:
        _cleanup_run(run_id)


def test_redline_details_endpoint_returns_enriched_data():
    run_id = _seed_final_run("test_run_final_details")
    try:
        response = client.get(f"/api/hitl/runs/{run_id}/redlines")
        assert response.status_code == 200
        payload = response.json()
        assert payload["run_id"] == run_id
        assert payload["summary"]["total_clauses"] == 2
        assert len(payload["proposals"]) == 2
        proposal = payload["proposals"][0]
        assert "clause_heading" in proposal
        assert "original_text" in proposal
        assert "proposed_text" in proposal
        assert "memo" in payload
        assert "executive_summary" in payload["memo"]
    finally:
        _cleanup_run(run_id)


def test_final_approve_updates_run_status():
    run_id = _seed_final_run("test_run_final_approve")
    try:
        payload = {
            "run_id": run_id,
            "approved": ["clause_1"],
            "rejected": ["clause_2"],
            "note": "Approved primary edits",
        }

        response = client.post("/api/hitl/final-approve", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "final_approved"
        assert data["approved"] == ["clause_1"]
        assert data["rejected"] == ["clause_2"]

        run_meta = coordinator.get_run(run_id)
        assert run_meta["status"] == RunStatus.COMPLETED.value
        final_record = coordinator.get_blackboard(run_id)["final_approval"]
        assert final_record["approved"] == ["clause_1"]
        assert final_record["rejected"] == ["clause_2"]
        assert final_record["notes"] == "Approved primary edits"
    finally:
        _cleanup_run(run_id)


def test_risk_analysis_prompt_uses_clause_text_only():
    doc_text = (
        "Clause One - Confidentiality\n"
        "Confidentiality obligations remain.\n\n"
        "Clause Two - Liability\n"
        "Unlimited liability for damages.\n"
    )
    clauses = [
        {
            "clause_id": "c1",
            "heading": "Clause One - Confidentiality",
            "text": doc_text,
            "body": "Confidentiality obligations remain.",
            "start_line": 1,
            "level": 1,
        },
        {
            "clause_id": "c2",
            "heading": "Clause Two - Liability",
            "text": doc_text,
            "body": "Unlimited liability for damages.",
            "start_line": 4,
            "level": 1,
        },
    ]

    blackboard = {
        "clauses": clauses,
        "document_text": doc_text,
        "history": [],
        "assessments": [],
    }

    agent = RiskAnalyzerAgent()
    agent.execute({"type": "assess_risk", "policy_rules": {}, "timestamp": "now"}, blackboard)

    prompts = [
        entry["prompt"]
        for entry in blackboard["history"]
        if entry.get("step") == "risk_analysis_clause"
    ]

    assert len(prompts) == 2
    assert "Confidentiality obligations remain." in prompts[0]
    assert "Unlimited liability for damages." not in prompts[0]
    assert "Unlimited liability for damages." in prompts[1]

    assessments = blackboard["assessments"]
    assert {a["clause_id"] for a in assessments} == {"c1", "c2"}
    risk_by_clause = {a["clause_id"]: a["risk_level"] for a in assessments}
    assert risk_by_clause["c1"].upper() == "LOW"
    assert risk_by_clause["c2"].upper() == "HIGH"


def test_run_level_replay_returns_comparison():
    run_id = _seed_run("test_run_replay")
    try:
        response = client.post(
            f"/api/replay/{run_id}",
            json={"agent_path": "manager_worker"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["run_id"] == run_id
        assert "comparison" in payload
        assert "score" in payload["comparison"]
    finally:
        _cleanup_run(run_id)


def test_clause_level_replay_returns_clause_comparison():
    run_id = _seed_run("test_clause_replay")
    try:
        response = client.post(
            f"/api/replay/{run_id}/clauses/clause_1",
            json={"prompt": "Custom prompt"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["run_id"] == run_id
        assert payload["clause_id"] == "clause_1"
        assert "comparison" in payload
        assert "risk_level" in payload["comparison"]
    finally:
        _cleanup_run(run_id)
