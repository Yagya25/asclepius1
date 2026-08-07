"""Smoke tests for the full agent pipeline and API endpoints."""
import os

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    """Health endpoint returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root():
    """Root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Asclepius" in response.json()["message"]


def test_list_datasets_empty():
    """List datasets returns empty list initially."""
    response = client.get("/datasets/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_full_pipeline():
    """End-to-end: upload → analyze → approve → report (US-01 through US-08)."""
    # Find sample CSV
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "samples", "pharma_retail_chemist_sales.csv")
    if not os.path.exists(sample_path):
        pytest.skip("Sample data not generated yet")

    # Step 1: Upload
    with open(sample_path, "rb") as f:
        response = client.post("/datasets/upload", files={"file": ("test.csv", f, "text/csv")})
    assert response.status_code == 200
    data = response.json()
    dataset_id = data["dataset_id"]
    assert data["rows"] > 0

    # Step 2: Analyze
    response = client.post(f"/datasets/{dataset_id}/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["recommendations_generated"] > 0

    # Step 3: Get pending recommendations
    response = client.get(f"/recommendations/?dataset_id={dataset_id}&status=pending")
    assert response.status_code == 200
    recs = response.json()
    assert len(recs) > 0

    # Step 4: Try report without approval — should fail
    response = client.post(f"/datasets/{dataset_id}/generate-report")
    assert response.status_code == 400
    assert "No approved" in response.json()["detail"]

    # Step 5: Approve first recommendation
    rec_id = recs[0]["id"]
    response = client.post(
        f"/recommendations/{rec_id}/approve",
        json={"approved_by": "Test Manager"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    # Step 6: Generate report — should work now
    response = client.post(f"/datasets/{dataset_id}/generate-report")
    assert response.status_code == 200
    report = response.json()["report"]
    assert report["summary"]["total_recommendations"] >= 1
    assert len(report["approved_actions"]) >= 1
    assert len(report["audit_trail"]) > 0

    # Step 7: Check audit trail
    response = client.get(f"/audit-log/?dataset_id={dataset_id}")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) > 0
    # Should have human checkpoint entries
    human_entries = [log for log in logs if log["human_checkpoint"]]
    assert len(human_entries) > 0
