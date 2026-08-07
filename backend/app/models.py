"""SQLAlchemy models for Asclepius — Multi-Module AI Business Operating System."""
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ──────────────────────────────────────────────────────────────────────────────
# Core Models (shared across all modules)
# ──────────────────────────────────────────────────────────────────────────────

class Dataset(Base):
    """One row per uploaded file. Tracks lifecycle: uploaded → validated → analyzed → completed."""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    module = Column(String(50), default="inventory")  # inventory | hr | finance
    detected_domain = Column(String(50), default="unknown")
    status = Column(String(50), default="uploaded")
    row_count = Column(Integer, default=0)
    business_health_score = Column(Float, nullable=True)
    analysis_summary = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    recommendations = relationship("Recommendation", back_populates="dataset")
    audit_logs = relationship("AuditLog", back_populates="dataset")


class SchemaCache(Base):
    """Caches LLM-detected file schemas based on file structure signatures."""
    __tablename__ = "schema_cache"

    id = Column(Integer, primary_key=True, index=True)
    file_signature = Column(String(255), unique=True, index=True)
    schema_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    """AI-generated action items. All start as pending until human approves.
    Used by ALL modules — inventory, HR, finance.
    """
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    module = Column(String(50), default="inventory")  # which module generated this
    agent_name = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    action_type = Column(String(50))
    severity = Column(String(20))
    estimated_impact = Column(String(100))
    status = Column(String(20), default="pending")
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    modified_note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="recommendations")


class AuditLog(Base):
    """Append-only log of every agent action and human decision. Shared across ALL modules."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    module = Column(String(50), default="inventory")
    agent_name = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    input_summary = Column(Text)
    output_summary = Column(Text)
    human_checkpoint = Column(Boolean, default=False)
    approved_by = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="audit_logs")


# ──────────────────────────────────────────────────────────────────────────────
# HR Module Models
# ──────────────────────────────────────────────────────────────────────────────

class JobDescription(Base):
    """A job description that resumes are screened against."""
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    department = Column(String(100))
    required_skills = Column(JSON)       # ["Python", "SQL", "Pandas"]
    preferred_skills = Column(JSON)      # ["FastAPI", "Docker"]
    min_experience_years = Column(Integer, default=0)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    screenings = relationship("ResumeScreening", back_populates="job_description")


class ResumeScreening(Base):
    """One row per uploaded resume, scored against a JD."""
    __tablename__ = "resume_screenings"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    jd_id = Column(Integer, ForeignKey("job_descriptions.id"))
    candidate_name = Column(String(255), nullable=False)
    email = Column(String(255))
    extracted_skills = Column(JSON)      # ["Python", "SQL", "Excel"]
    experience_years = Column(Float, default=0)
    education = Column(String(255))
    fit_score = Column(Float, default=0)  # 0-100
    tier = Column(String(20))            # Strong | Moderate | Weak
    rank = Column(Integer)
    status = Column(String(20), default="pending")  # pending | shortlisted | rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    job_description = relationship("JobDescription", back_populates="screenings")


class Employee(Base):
    """Employee record for onboarding tracking."""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    department = Column(String(100))
    role = Column(String(100))
    join_date = Column(DateTime)
    onboarding_status = Column(String(20), default="pending")  # pending | in_progress | completed
    onboarding_progress = Column(Float, default=0)  # 0-100%
    created_at = Column(DateTime, default=datetime.utcnow)

    onboarding_tasks = relationship("OnboardingTask", back_populates="employee")


class OnboardingTask(Base):
    """Auto-generated onboarding checklist item."""
    __tablename__ = "onboarding_tasks"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    category = Column(String(50))        # IT | HR | Training | Team
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_days = Column(Integer, default=7)  # days from join_date
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="onboarding_tasks")
