"""Dataset upload and pipeline APIs."""
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..agents.analysis_agent import AnalysisAgent
from ..agents.ingestion_agent import IngestionAgent
from ..agents.insight_agent import InsightAgent
from ..agents.report_agent import ReportAgent
from ..db import get_db
from ..models import Dataset

router = APIRouter(prefix="/datasets", tags=["datasets"])

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload Excel/CSV and trigger ingestion agent (US-01)."""
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("xlsx", "xls", "csv"):
        raise HTTPException(status_code=400, detail="Unsupported file format. Upload .xlsx or .csv files.")

    file_id = str(uuid.uuid4())[:8]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Check file size (50MB limit)
    if os.path.getsize(file_path) > 50 * 1024 * 1024:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB.")

    # Create dataset record
    dataset = Dataset(filename=file.filename, status="uploaded")
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # Run ingestion agent
    agent = IngestionAgent(db)
    df, columns = agent.run(dataset.id, file_path)

    return {
        "dataset_id": dataset.id,
        "filename": file.filename,
        "status": dataset.status,
        "rows": dataset.row_count,
        "domain": dataset.detected_domain,
        "columns_detected": columns,
    }


@router.post("/{dataset_id}/analyze")
async def analyze_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Run analysis + insight agents (US-02, US-03, US-04, US-05)."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Re-load the cleaned data
    import glob
    files = glob.glob(f"./uploads/*_{dataset.filename}")
    if not files:
        raise HTTPException(status_code=404, detail="File not found on disk")

    file_path = files[0]
    # Re-run ingestion to get clean data and column mapping
    ingestion = IngestionAgent(db)
    df, columns = ingestion.run(dataset_id, file_path)

    # Run analysis
    analysis_agent = AnalysisAgent(db)
    results = analysis_agent.run(dataset_id, df, columns)

    # Run insight agent (generates recommendations, all pending)
    insight = InsightAgent(db)
    recommendations = insight.run(dataset_id, results)

    return {
        "dataset_id": dataset_id,
        "status": "pending_approval",
        "business_health_score": results.get("kpis", {}).get("business_health_score"),
        "kpis": results.get("kpis", {}),
        "recommendations_generated": len(recommendations),
        "anomalies_found": len(results.get("anomalies", [])),
    }


@router.get("/")
async def list_datasets(db: Session = Depends(get_db)):
    """List all uploaded datasets."""
    datasets = db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "status": d.status,
            "domain": d.detected_domain,
            "rows": d.row_count,
            "business_health_score": d.business_health_score,
            "uploaded_at": d.uploaded_at,
        }
        for d in datasets
    ]


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Get dataset details."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": dataset.id,
        "filename": dataset.filename,
        "status": dataset.status,
        "domain": dataset.detected_domain,
        "rows": dataset.row_count,
        "business_health_score": dataset.business_health_score,
        "uploaded_at": dataset.uploaded_at,
    }


@router.post("/{dataset_id}/generate-report")
async def generate_report(dataset_id: int, db: Session = Depends(get_db)):
    """Generate report from approved recommendations only (US-08)."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    agent = ReportAgent(db)
    report = agent.run(dataset_id)

    if report is None:
        raise HTTPException(
            status_code=400,
            detail="No approved recommendations. Approve at least one recommendation first.",
        )

    return {"dataset_id": dataset_id, "report": report}
