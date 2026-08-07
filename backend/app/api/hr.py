"""HR Automation API endpoints — Resume Screening + Employee Onboarding."""
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import (
    Dataset,
    Employee,
    JobDescription,
    OnboardingTask,
    ResumeScreening,
)
from ..modules.hr.onboarding_agent import OnboardingAgent
from ..modules.hr.resume_agent import ResumeScreeningAgent

router = APIRouter(prefix="/hr", tags=["hr"])

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic request models
# ──────────────────────────────────────────────────────────────────────────────

class JDCreate(BaseModel):
    title: str
    department: str | None = None
    required_skills: list[str]
    preferred_skills: list[str] | None = None
    min_experience_years: int = 0
    description: str | None = None


class EmployeeCreate(BaseModel):
    name: str
    email: str | None = None
    department: str
    role: str
    join_date: str | None = None  # ISO format


class TaskComplete(BaseModel):
    completed_by: str


# ──────────────────────────────────────────────────────────────────────────────
# Job Description endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/job-descriptions")
async def create_job_description(jd: JDCreate, db: Session = Depends(get_db)):
    """Create a Job Description for resume screening."""
    record = JobDescription(
        title=jd.title,
        department=jd.department,
        required_skills=jd.required_skills,
        preferred_skills=jd.preferred_skills or [],
        min_experience_years=jd.min_experience_years,
        description=jd.description,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "title": record.title,
        "department": record.department,
        "required_skills": record.required_skills,
        "preferred_skills": record.preferred_skills,
        "min_experience_years": record.min_experience_years,
    }


@router.get("/job-descriptions")
async def list_job_descriptions(db: Session = Depends(get_db)):
    """List all Job Descriptions."""
    jds = db.query(JobDescription).order_by(JobDescription.created_at.desc()).all()
    return [
        {
            "id": j.id,
            "title": j.title,
            "department": j.department,
            "required_skills": j.required_skills,
            "min_experience_years": j.min_experience_years,
            "created_at": j.created_at,
        }
        for j in jds
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Resume Screening endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/screen-resumes")
async def screen_resumes(
    jd_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload resumes CSV and screen against a Job Description (US-11)."""
    # Validate file
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a CSV file with resume data.")

    # Verify JD exists
    jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job Description not found")

    # Save file
    file_id = str(uuid.uuid4())[:8]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create dataset record (module = "hr")
    dataset = Dataset(filename=file.filename, module="hr", status="uploaded")
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # Run screening agent
    agent = ResumeScreeningAgent(db)
    recs = agent.run(dataset.id, file_path, jd_id)

    return {
        "dataset_id": dataset.id,
        "jd_id": jd_id,
        "jd_title": jd.title,
        "candidates_processed": dataset.row_count,
        "analysis": dataset.analysis_summary,
        "recommendations_generated": len(recs),
        "status": "pending_approval",
    }


@router.get("/screenings/{dataset_id}/results")
async def get_screening_results(dataset_id: int, db: Session = Depends(get_db)):
    """Get scored and ranked candidates for a screening run."""
    screenings = (
        db.query(ResumeScreening)
        .filter(ResumeScreening.dataset_id == dataset_id)
        .order_by(ResumeScreening.rank.asc())
        .all()
    )

    if not screenings:
        raise HTTPException(status_code=404, detail="No screening results found for this dataset")

    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    return {
        "dataset_id": dataset_id,
        "total_candidates": len(screenings),
        "summary": dataset.analysis_summary if dataset else {},
        "candidates": [
            {
                "rank": s.rank,
                "name": s.candidate_name,
                "email": s.email,
                "fit_score": s.fit_score,
                "tier": s.tier,
                "extracted_skills": s.extracted_skills,
                "experience_years": s.experience_years,
                "education": s.education,
                "status": s.status,
            }
            for s in screenings
        ],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Employee & Onboarding endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/employees")
async def register_employee(emp: EmployeeCreate, db: Session = Depends(get_db)):
    """Register a new employee (US-12)."""
    from datetime import datetime

    join_date = None
    if emp.join_date:
        try:
            join_date = datetime.fromisoformat(emp.join_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid join_date format. Use ISO format.")

    employee = Employee(
        name=emp.name,
        email=emp.email,
        department=emp.department,
        role=emp.role,
        join_date=join_date or datetime.utcnow(),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)

    return {
        "id": employee.id,
        "name": employee.name,
        "department": employee.department,
        "role": employee.role,
        "onboarding_status": employee.onboarding_status,
    }


@router.get("/employees")
async def list_employees(db: Session = Depends(get_db)):
    """List all employees."""
    employees = db.query(Employee).order_by(Employee.created_at.desc()).all()
    return [
        {
            "id": e.id,
            "name": e.name,
            "department": e.department,
            "role": e.role,
            "onboarding_status": e.onboarding_status,
            "onboarding_progress": e.onboarding_progress,
            "join_date": e.join_date,
        }
        for e in employees
    ]


@router.post("/employees/{employee_id}/onboard")
async def trigger_onboarding(employee_id: int, db: Session = Depends(get_db)):
    """Trigger onboarding agent for an employee (US-12)."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee.onboarding_status == "completed":
        raise HTTPException(status_code=400, detail="Onboarding already completed")

    agent = OnboardingAgent(db)
    tasks = agent.run(employee_id)

    return {
        "employee_id": employee_id,
        "employee_name": employee.name,
        "department": employee.department,
        "tasks_created": len(tasks),
        "categories": {
            "HR": sum(1 for t in tasks if t.category == "HR"),
            "IT": sum(1 for t in tasks if t.category == "IT"),
            "Training": sum(1 for t in tasks if t.category == "Training"),
            "Team": sum(1 for t in tasks if t.category == "Team"),
        },
        "onboarding_status": "in_progress",
    }


@router.get("/employees/{employee_id}/onboarding")
async def get_onboarding_status(employee_id: int, db: Session = Depends(get_db)):
    """Get onboarding checklist and progress for an employee."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    tasks = (
        db.query(OnboardingTask)
        .filter(OnboardingTask.employee_id == employee_id)
        .order_by(OnboardingTask.due_days.asc())
        .all()
    )

    completed = sum(1 for t in tasks if t.is_completed)
    total = len(tasks)
    progress = round((completed / total) * 100, 1) if total > 0 else 0

    return {
        "employee_id": employee_id,
        "employee_name": employee.name,
        "department": employee.department,
        "onboarding_status": employee.onboarding_status,
        "progress": progress,
        "completed": completed,
        "total": total,
        "tasks": [
            {
                "id": t.id,
                "category": t.category,
                "title": t.title,
                "due_days": t.due_days,
                "is_completed": t.is_completed,
                "completed_at": t.completed_at,
            }
            for t in tasks
        ],
    }


@router.post("/onboarding-tasks/{task_id}/complete")
async def complete_onboarding_task(
    task_id: int, body: TaskComplete, db: Session = Depends(get_db),
):
    """Mark an onboarding task as completed."""
    from datetime import datetime

    task = db.query(OnboardingTask).filter(OnboardingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.is_completed:
        raise HTTPException(status_code=400, detail="Task already completed")

    task.is_completed = True
    task.completed_at = datetime.utcnow()

    # Update employee progress
    employee = db.query(Employee).filter(Employee.id == task.employee_id).first()
    all_tasks = db.query(OnboardingTask).filter(OnboardingTask.employee_id == employee.id).all()
    completed = sum(1 for t in all_tasks if t.is_completed)
    total = len(all_tasks)
    employee.onboarding_progress = round((completed / total) * 100, 1) if total > 0 else 0

    if completed == total:
        employee.onboarding_status = "completed"

    db.commit()

    return {
        "task_id": task_id,
        "completed": True,
        "completed_by": body.completed_by,
        "employee_progress": employee.onboarding_progress,
        "onboarding_status": employee.onboarding_status,
    }
