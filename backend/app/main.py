"""Asclepius — AI Business Operating System."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import ai_insights, approvals, audit, compat, datasets, hr, kpis
from .db import init_db

app = FastAPI(
    title="Asclepius",
    description="AI Business Operating System — Multi-Module Business Process Automation",
    version="0.2.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()


# Mount all routers at root (original CLI & backend tests)
app.include_router(datasets.router)
app.include_router(approvals.router)
app.include_router(kpis.router)
app.include_router(audit.router)
app.include_router(hr.router)
app.include_router(ai_insights.router)

# Mount compatibility & real routers under /api prefix for React frontend
app.include_router(compat.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(kpis.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(hr.router, prefix="/api")
app.include_router(ai_insights.router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "asclepius"}


@app.get("/modules")
async def list_modules():
    """List available business modules and their status."""
    return {
        "platform": "Asclepius — AI Business Operating System",
        "modules": [
            {
                "id": "inventory",
                "name": "Inventory & Sales Intelligence",
                "status": "active",
                "description": "Upload pharma ERP data → AI analysis → recommendations → approval → report",
                "agents": ["IngestionAgent", "AnalysisAgent", "InsightAgent", "ReportAgent"],
                "endpoints_prefix": "/datasets",
            },
            {
                "id": "hr",
                "name": "HR Automation",
                "status": "active",
                "description": "Resume screening, employee onboarding, AI-driven shortlisting",
                "agents": ["ResumeScreeningAgent", "OnboardingAgent"],
                "endpoints_prefix": "/hr",
            },
            {
                "id": "finance",
                "name": "Finance Automation",
                "status": "planned",
                "description": "Invoice processing, expense auditing, GST reconciliation",
                "agents": [],
                "endpoints_prefix": "/finance",
            },
            {
                "id": "operations",
                "name": "Operations Intelligence",
                "status": "planned",
                "description": "Task automation, workflow optimization, SLA tracking",
                "agents": [],
                "endpoints_prefix": "/operations",
            },
        ],
        "shared_infrastructure": [
            "Approval Center — all modules feed into one approval queue",
            "Audit Trail — decision timeline spans all modules",
            "Report Generator — cross-module executive reports",
        ],
    }


@app.get("/")
async def root():
    """API root with endpoint listing."""
    return {
        "message": "Asclepius — AI Business Operating System",
        "docs": "/docs",
        "modules": "/modules",
        "endpoints": {
            "inventory": {
                "upload": "POST /datasets/upload",
                "analyze": "POST /datasets/{id}/analyze",
                "kpis": "GET /datasets/{id}/kpis",
                "sales": "GET /datasets/{id}/sales",
                "inventory": "GET /datasets/{id}/inventory",
                "customers": "GET /datasets/{id}/customers",
                "priority_queue": "GET /datasets/{id}/priority-queue",
                "generate_report": "POST /datasets/{id}/generate-report",
            },
            "hr": {
                "create_jd": "POST /hr/job-descriptions",
                "list_jds": "GET /hr/job-descriptions",
                "screen_resumes": "POST /hr/screen-resumes?jd_id={id}",
                "screening_results": "GET /hr/screenings/{id}/results",
                "register_employee": "POST /hr/employees",
                "trigger_onboarding": "POST /hr/employees/{id}/onboard",
                "onboarding_status": "GET /hr/employees/{id}/onboarding",
                "complete_task": "POST /hr/onboarding-tasks/{id}/complete",
            },
            "shared": {
                "recommendations": "GET /recommendations/",
                "approve": "POST /recommendations/{id}/approve",
                "reject": "POST /recommendations/{id}/reject",
                "audit_log": "GET /audit-log/",
                "timeline": "GET /audit-log/timeline?dataset_id={id}",
                "modules": "GET /modules",
            },
        },
    }
