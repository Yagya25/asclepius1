"""Tests for React Frontend API Compatibility Layer & Modular Integration."""
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Recommendation


def test_auth_endpoints(client: TestClient):
    """Test auth endpoints used by React AuthContext."""
    # Test GET /api/auth/me
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "utkarsh@pharma.bi"
    assert data["role"] == "admin"

    # Test POST /api/auth/login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "utkarsh@pharma.bi", "password": "any", "remember": True},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["role"] == "admin"


def test_notifications_inbox(client: TestClient, db_session: Session):
    """Test notifications dropdown and read-all toggle."""
    # Add a sample recommendation to DB
    rec = Recommendation(
        dataset_id=1,
        module="inventory",
        agent_name="InventoryAgent",
        title="Restock Amoxicillin",
        description="Low stock detected in West region warehouse.",
        severity="high",
        status="pending",
        created_at=datetime.utcnow(),
    )
    db_session.add(rec)
    db_session.commit()

    # Get notifications
    res = client.get("/api/notifications")
    assert res.status_code == 200
    notifs = res.json()
    assert len(notifs) >= 1
    assert any("Restock Amoxicillin" in n["title"] for n in notifs)
    assert any(n["level"] == "warning" for n in notifs)

    # Mark all read
    read_res = client.post("/api/notifications/read-all")
    assert read_res.status_code == 200
    assert read_res.json()["status"] == "ok"


def test_dashboard_and_insights_data(client: TestClient):
    """Test data formatting for Dashboard and all Insights tabs."""
    # Dashboard
    dash_res = client.get("/api/dashboard")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "kpis" in dash_data
    assert dash_data["kpis"]["active_skus"] > 0
    assert "health_score" in dash_data
    assert "revenue_trend" in dash_data

    # Insights tabs
    for tab in ["sales", "inventory", "customers", "forecasts", "anomalies"]:
        tab_res = client.get(f"/api/insights/{tab}")
        assert tab_res.status_code == 200, f"/api/insights/{tab} failed"


def test_recommendations_and_decision_checkpoint(client: TestClient, db_session: Session):
    """Test fetching recommendations formatted for UI and processing human approval."""
    rec = Recommendation(
        dataset_id=1,
        module="hr",
        agent_name="ScreeningAgent",
        title="Shortlist Candidate #42",
        description="Fit score 95% against Senior Sales JD.",
        severity="medium",
        status="pending",
        created_at=datetime.utcnow(),
    )
    db_session.add(rec)
    db_session.commit()
    rec_id = rec.id

    # Get list
    recs_res = client.get("/api/recommendations")
    assert recs_res.status_code == 200
    recs_data = recs_res.json()
    matched = next((r for r in recs_data if r["id"] == str(rec_id)), None)
    assert matched is not None
    assert matched["priority"] == "warning"
    assert "source_agent" in matched

    # Make decision via compat layer
    dec_res = client.post(
        f"/api/recommendations/{rec_id}/decision",
        json={"action": "approve", "comment": "Verified background check."},
    )
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["status"] == "approved"
    assert dec_data["decided_by"] == "Utkarsh Sharma"

    # Verify action logged in audit trail
    audit_res = client.get("/api/audit")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert any("RECOMMENDATION_APPROVE" in log["action"] for log in audit_data)


def test_hr_endpoints_via_api_prefix(client: TestClient):
    """Verify all HR module endpoints are accessible via /api prefix for the React frontend."""
    # Create job description
    jd_res = client.post(
        "/api/hr/job-descriptions",
        json={
            "title": "Pharma Retail Analyst",
            "department": "Analytics",
            "required_skills": ["sql", "pharma data", "python"],
            "min_experience_years": 2,
        },
    )
    assert jd_res.status_code == 200
    assert "id" in jd_res.json()

    # List JDs
    list_jd = client.get("/api/hr/job-descriptions")
    assert list_jd.status_code == 200
    assert len(list_jd.json()) >= 1

    # Employee onboarding
    emp_res = client.post(
        "/api/hr/employees",
        json={"name": "Rohit Verma", "email": "rohit@pharma.bi", "role": "Analyst", "department": "Finance"},
    )
    assert emp_res.status_code == 200
    emp_id = emp_res.json()["id"]

    onboard_res = client.post(f"/api/hr/employees/{emp_id}/onboard")
    assert onboard_res.status_code == 200
    assert onboard_res.json()["tasks_created"] > 0

    status_res = client.get(f"/api/hr/employees/{emp_id}/onboarding")
    assert status_res.status_code == 200
    plan = status_res.json()
    assert "tasks" in plan
    assert len(plan["tasks"]) > 0

    # Complete a task
    task_id = plan["tasks"][0]["id"]
    comp_res = client.post(
        f"/api/hr/onboarding-tasks/{task_id}/complete",
        json={"completed_by": "Utkarsh Sharma"},
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["completed"] is True
