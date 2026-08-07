"""Human-in-the-Loop approval APIs."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuditLog, Recommendation

router = APIRouter(prefix="/recommendations", tags=["approvals"])


class ApprovalRequest(BaseModel):
    approved_by: str
    note: str | None = None


@router.get("/")
async def list_recommendations(
    dataset_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """List recommendations. Filter by dataset and/or status (US-05)."""
    query = db.query(Recommendation)
    if dataset_id:
        query = query.filter(Recommendation.dataset_id == dataset_id)
    if status:
        statuses = status.split(",")
        query = query.filter(Recommendation.status.in_(statuses))

    recs = query.order_by(Recommendation.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "dataset_id": r.dataset_id,
            "agent_name": r.agent_name,
            "title": r.title,
            "description": r.description,
            "action_type": r.action_type,
            "severity": r.severity,
            "estimated_impact": r.estimated_impact,
            "status": r.status,
            "approved_by": r.approved_by,
            "approved_at": r.approved_at,
            "created_at": r.created_at,
        }
        for r in recs
    ]


@router.post("/{rec_id}/approve")
async def approve_recommendation(
    rec_id: int, req: ApprovalRequest, db: Session = Depends(get_db),
):
    """Manager approves a recommendation (US-06)."""
    rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Already {rec.status}")

    rec.status = "approved"
    rec.approved_by = req.approved_by
    rec.approved_at = datetime.utcnow()

    audit = AuditLog(
        dataset_id=rec.dataset_id,
        agent_name="HUMAN_APPROVAL",
        action="APPROVED_RECOMMENDATION",
        input_summary=f"Recommendation: {rec.title}",
        output_summary=f"Approved by {req.approved_by}",
        human_checkpoint=True,
        approved_by=req.approved_by,
    )
    db.add(audit)
    db.commit()

    return {"status": "approved", "rec_id": rec_id, "approved_by": req.approved_by}


@router.post("/{rec_id}/reject")
async def reject_recommendation(
    rec_id: int, req: ApprovalRequest, db: Session = Depends(get_db),
):
    """Manager rejects a recommendation (US-06)."""
    rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Already {rec.status}")

    rec.status = "rejected"
    rec.approved_by = req.approved_by
    rec.modified_note = req.note

    audit = AuditLog(
        dataset_id=rec.dataset_id,
        agent_name="HUMAN_APPROVAL",
        action="REJECTED_RECOMMENDATION",
        input_summary=f"Recommendation: {rec.title}",
        output_summary=f"Rejected by {req.approved_by}. Reason: {req.note}",
        human_checkpoint=True,
        approved_by=req.approved_by,
    )
    db.add(audit)
    db.commit()

    return {"status": "rejected", "rec_id": rec_id}
