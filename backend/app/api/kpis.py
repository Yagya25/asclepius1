"""KPI and analysis result APIs."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Dataset, Recommendation

router = APIRouter(prefix="/datasets", tags=["analysis"])


@router.get("/{dataset_id}/kpis")
async def get_kpis(dataset_id: int, db: Session = Depends(get_db)):
    """Get KPIs and Business Health Score for a dataset (US-03)."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.analysis_summary:
        raise HTTPException(status_code=400, detail="Dataset not yet analyzed. Run POST /datasets/{id}/analyze first.")

    return {
        "dataset_id": dataset_id,
        "business_health_score": dataset.business_health_score,
        "kpis": dataset.analysis_summary.get("kpis", {}),
    }


@router.get("/{dataset_id}/sales")
async def get_sales(dataset_id: int, db: Session = Depends(get_db)):
    """Get sales analysis results (US-09)."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.analysis_summary:
        raise HTTPException(status_code=400, detail="Dataset not yet analyzed.")

    return {
        "dataset_id": dataset_id,
        "sales": dataset.analysis_summary.get("sales", {}),
        "anomalies": dataset.analysis_summary.get("anomalies", []),
    }


@router.get("/{dataset_id}/inventory")
async def get_inventory(dataset_id: int, db: Session = Depends(get_db)):
    """Get inventory analysis results (US-04)."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.analysis_summary:
        raise HTTPException(status_code=400, detail="Dataset not yet analyzed.")

    return {
        "dataset_id": dataset_id,
        "inventory": dataset.analysis_summary.get("inventory", {}),
    }


@router.get("/{dataset_id}/customers")
async def get_customers(dataset_id: int, db: Session = Depends(get_db)):
    """Get customer analysis results (US-09)."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.analysis_summary:
        raise HTTPException(status_code=400, detail="Dataset not yet analyzed.")

    return {
        "dataset_id": dataset_id,
        "customers": dataset.analysis_summary.get("customers", {}),
    }


@router.get("/{dataset_id}/priority-queue")
async def get_priority_queue(dataset_id: int, db: Session = Depends(get_db)):
    """Get top actions ranked by severity (US-05). The AI Priority Queue."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    severity_order = {"critical": 0, "warning": 1, "info": 2}
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.dataset_id == dataset_id,
                Recommendation.status == "pending")
        .all()
    )

    items = sorted(
        [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "severity": r.severity,
                "action_type": r.action_type,
                "estimated_impact": r.estimated_impact,
            }
            for r in recs
        ],
        key=lambda x: severity_order.get(x["severity"], 99),
    )

    return {
        "dataset_id": dataset_id,
        "business_health_score": dataset.business_health_score,
        "priority_queue": items,
        "total_pending": len(items),
    }
