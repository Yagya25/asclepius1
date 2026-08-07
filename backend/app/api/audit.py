"""Audit trail API — the Decision Timeline."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuditLog

router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("/")
async def get_audit_log(
    dataset_id: int | None = Query(None),
    agent_name: str | None = Query(None),
    human_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Get audit trail entries. The Decision Timeline (US-07).

    Filter by dataset_id, agent_name, or human checkpoints only.
    Returns entries in chronological order.
    """
    query = db.query(AuditLog)

    if dataset_id:
        query = query.filter(AuditLog.dataset_id == dataset_id)
    if agent_name:
        query = query.filter(AuditLog.agent_name == agent_name)
    if human_only:
        query = query.filter(AuditLog.human_checkpoint)

    entries = query.order_by(AuditLog.timestamp.asc()).all()

    return [
        {
            "id": e.id,
            "dataset_id": e.dataset_id,
            "agent_name": e.agent_name,
            "action": e.action,
            "input_summary": e.input_summary,
            "output_summary": e.output_summary,
            "human_checkpoint": e.human_checkpoint,
            "approved_by": e.approved_by,
            "timestamp": e.timestamp,
        }
        for e in entries
    ]


@router.get("/timeline")
async def get_timeline(dataset_id: int, db: Session = Depends(get_db)):
    """Get formatted decision timeline for a dataset.

    Returns a simplified timeline suitable for display.
    """
    entries = (
        db.query(AuditLog)
        .filter(AuditLog.dataset_id == dataset_id)
        .order_by(AuditLog.timestamp.asc())
        .all()
    )

    timeline = []
    for e in entries:
        icon = "🔵"
        if e.agent_name == "INGESTION":
            icon = "📥"
        elif e.agent_name == "ANALYSIS":
            icon = "📊"
        elif e.agent_name == "INSIGHT":
            icon = "💡"
        elif e.agent_name == "HUMAN_APPROVAL":
            icon = "👤"
        elif e.agent_name == "REPORT":
            icon = "📄"

        timeline.append({
            "icon": icon,
            "timestamp": e.timestamp.strftime("%H:%M:%S") if e.timestamp else "",
            "agent": e.agent_name,
            "action": e.action,
            "summary": e.output_summary,
            "is_human": e.human_checkpoint,
            "approved_by": e.approved_by,
        })

    return {"dataset_id": dataset_id, "timeline": timeline, "total_steps": len(timeline)}
