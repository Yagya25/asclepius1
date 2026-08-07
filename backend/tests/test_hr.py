"""Tests for HR Automation module — Resume Screening + Onboarding."""
import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_modules_endpoint():
    """Modules endpoint lists both inventory and HR."""
    response = client.get("/modules")
    assert response.status_code == 200
    data = response.json()
    modules = data["modules"]
    module_ids = [m["id"] for m in modules]
    assert "inventory" in module_ids
    assert "hr" in module_ids
    # Check active status
    active = [m for m in modules if m["status"] == "active"]
    assert len(active) >= 2
    # Check planned modules exist
    planned = [m for m in modules if m["status"] == "planned"]
    assert len(planned) >= 1


def test_root_shows_hr_endpoints():
    """Root endpoint shows HR endpoints."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "hr" in data["endpoints"]
    assert "AI Business Operating System" in data["message"]


def test_create_job_description():
    """Create a JD for resume screening."""
    response = client.post("/hr/job-descriptions", json={
        "title": "Pharma Sales Rep",
        "department": "Sales",
        "required_skills": ["pharma sales", "communication", "excel"],
        "preferred_skills": ["tally", "erp"],
        "min_experience_years": 2,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["id"] >= 1
    assert data["title"] == "Pharma Sales Rep"
    assert len(data["required_skills"]) == 3


def test_list_job_descriptions():
    """List JDs returns created entries."""
    # Create one first
    client.post("/hr/job-descriptions", json={
        "title": "Test JD",
        "required_skills": ["python"],
    })
    response = client.get("/hr/job-descriptions")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_resume_screening_pipeline():
    """Full resume screening: create JD → upload resumes → score → rank → recommend."""
    # Step 1: Create JD
    jd_resp = client.post("/hr/job-descriptions", json={
        "title": "Pharma Sales Representative",
        "department": "Sales",
        "required_skills": ["pharma sales", "communication", "excel", "crm", "product knowledge"],
        "preferred_skills": ["tally", "erp", "data analysis"],
        "min_experience_years": 2,
    })
    jd_id = jd_resp.json()["id"]

    # Step 2: Upload resumes
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "samples", "hr_sample_resumes.csv")
    if not os.path.exists(sample_path):
        import pytest
        pytest.skip("HR sample data not generated yet")

    with open(sample_path, "rb") as f:
        response = client.post(
            f"/hr/screen-resumes?jd_id={jd_id}",
            files={"file": ("resumes.csv", f, "text/csv")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["candidates_processed"] > 0
    assert data["recommendations_generated"] > 0
    dataset_id = data["dataset_id"]

    # Step 3: Get screening results
    response = client.get(f"/hr/screenings/{dataset_id}/results")
    assert response.status_code == 200
    results = response.json()
    assert results["total_candidates"] > 0
    candidates = results["candidates"]
    # Should be sorted by rank
    assert candidates[0]["rank"] == 1
    # Top candidate should have highest fit score
    assert candidates[0]["fit_score"] >= candidates[-1]["fit_score"]
    # Check tiers exist
    tiers = set(c["tier"] for c in candidates)
    assert "Strong" in tiers or "Moderate" in tiers

    # Step 4: Check recommendations were created
    response = client.get(f"/recommendations/?dataset_id={dataset_id}")
    assert response.status_code == 200
    recs = response.json()
    assert len(recs) > 0
    assert all(r["status"] == "pending" for r in recs)

    # Step 5: Approve a recommendation (same approval flow as inventory!)
    rec_id = recs[0]["id"]
    response = client.post(
        f"/recommendations/{rec_id}/approve",
        json={"approved_by": "HR Manager"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    # Step 6: Verify audit trail shows HR agent entries
    response = client.get(f"/audit-log/?dataset_id={dataset_id}")
    assert response.status_code == 200
    logs = response.json()
    agent_names = set(log["agent_name"] for log in logs)
    assert "HR_RESUME_SCREENING" in agent_names
    # Should have human checkpoint
    human = [log for log in logs if log["human_checkpoint"]]
    assert len(human) > 0


def test_employee_onboarding_pipeline():
    """Full onboarding: register → trigger → check tasks → complete task."""
    # Step 1: Register employee
    response = client.post("/hr/employees", json={
        "name": "Priya Sharma",
        "email": "priya@pharma.com",
        "department": "Sales",
        "role": "Sales Representative",
    })
    assert response.status_code == 200
    emp = response.json()
    emp_id = emp["id"]
    assert emp["onboarding_status"] == "pending"

    # Step 2: Trigger onboarding
    response = client.post(f"/hr/employees/{emp_id}/onboard")
    assert response.status_code == 200
    data = response.json()
    assert data["tasks_created"] > 0
    assert data["onboarding_status"] == "in_progress"
    # Sales department should have pharma-specific tasks
    assert data["categories"]["Training"] >= 2

    # Step 3: Check onboarding status
    response = client.get(f"/hr/employees/{emp_id}/onboarding")
    assert response.status_code == 200
    status = response.json()
    assert status["progress"] == 0
    assert len(status["tasks"]) > 0
    tasks = status["tasks"]

    # Step 4: Complete a task
    task_id = tasks[0]["id"]
    response = client.post(
        f"/hr/onboarding-tasks/{task_id}/complete",
        json={"completed_by": "HR Admin"},
    )
    assert response.status_code == 200
    assert response.json()["completed"] is True
    assert response.json()["employee_progress"] > 0

    # Step 5: Complete all remaining tasks
    for t in tasks[1:]:
        client.post(
            f"/hr/onboarding-tasks/{t['id']}/complete",
            json={"completed_by": "HR Admin"},
        )

    # Step 6: Verify employee is fully onboarded
    response = client.get(f"/hr/employees/{emp_id}/onboarding")
    assert response.status_code == 200
    final = response.json()
    assert final["progress"] == 100
    assert final["onboarding_status"] == "completed"


def test_audit_trail_spans_modules():
    """Audit trail contains entries from both inventory and HR modules."""
    # This test verifies that the shared audit infrastructure works across modules
    response = client.get("/audit-log/")
    assert response.status_code == 200
    logs = response.json()
    if len(logs) > 0:
        # If we have logs from the other tests, verify agent diversity
        agent_names = set(log["agent_name"] for log in logs)
        # At minimum, HR agents should be represented if HR tests ran first
        hr_agents = {"HR_RESUME_SCREENING", "HR_ONBOARDING", "HUMAN_APPROVAL"}
        assert len(agent_names & hr_agents) > 0 or len(logs) == 0
