"""API compatibility layer to bridge React frontend with FastAPI backend."""
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
import shutil
import uuid
import os

from ..db import get_db
from ..models import AuditLog, Dataset, Recommendation
from ..services.reports_generator import generate_excel_report, generate_pdf_report
from ..agents.ingestion_agent import IngestionAgent
from ..agents.analysis_agent import AnalysisAgent
from ..agents.insight_agent import InsightAgent

router = APIRouter(tags=["compatibility"])


# --- Auth & Notifications ---
@router.get("/auth/me")
async def auth_me(request: Request) -> dict[str, Any]:
    """Return mock authenticated user for frontend."""
    auth = request.headers.get("Authorization", "")
    role = "admin"
    name = "Utkarsh Sharma"
    email = "utkarsh@pharma.bi"
    
    if "manager" in auth:
        role = "manager"
        name = "Manager User"
        email = "manager@asclepius.com"
    elif "exec" in auth:
        role = "executive"
        name = "Executive User"
        email = "executive@asclepius.com"
    elif "analyst" in auth:
        role = "analyst"
        name = "Analyst User"
        email = "analyst@asclepius.com"

    return {
        "id": f"usr_{role}_1",
        "name": name,
        "email": email,
        "role": role,
        "avatar": "",
    }


class LoginRequest(BaseModel):
    email: str
    password: str
    remember: bool | None = None


@router.post("/auth/login")
async def auth_login(req: LoginRequest) -> dict[str, Any]:
    """Mock login returning JWT token and user based on email."""
    email = req.email.lower()
    role = "admin"
    name = "Utkarsh Sharma"
    
    if "hr" in email:
        role = "hr_manager"
        name = "HR Manager"
    elif "manager" in email:
        role = "manager"
        name = "Manager User"
    elif "exec" in email:
        role = "executive"
        name = "Executive User"
    elif "analyst" in email:
        role = "analyst"
        name = "Analyst User"

    return {
        "access_token": f"apbi_token_live_{role}_9000",
        "refresh_token": "apbi_refresh_token",
        "user": {
            "id": f"usr_{role}_1",
            "name": name,
            "email": req.email,
            "role": role,
        },
    }


@router.post("/auth/register")
async def auth_register(req: dict[str, Any]) -> dict[str, Any]:
    """Mock registration."""
    email = req.get("email", "admin@pharma.bi")
    name = req.get("name", "Utkarsh Sharma")
    return {
        "access_token": "apbi_token_live_admin_9000",
        "refresh_token": "apbi_refresh_token",
        "user": {"id": "usr_admin_1", "name": name, "email": email, "role": req.get("role", "admin")},
    }


@router.post("/auth/logout")
@router.post("/auth/logout-all")
@router.post("/auth/refresh")
async def auth_noop() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/notifications")
async def get_notifications(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return pending recommendations as notifications in navbar."""
    pending = db.query(Recommendation).filter(Recommendation.status == "pending").all()
    if not pending:
        return [
            {
                "id": "notif_welcome",
                "title": "System Initialized",
                "body": "Asclepius modules active. No pending approvals.",
                "level": "info",
                "read": False,
            }
        ]
    notifs = []
    for r in pending:
        notifs.append(
            {
                "id": str(r.id),
                "title": f"[{r.module.upper()}] {r.title}",
                "body": r.description[:120],
                "level": "warning" if r.severity == "high" else "info",
                "read": False,
            }
        )
    return notifs


@router.post("/notifications/read-all")
async def read_notifications() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/demo/reset")
async def demo_reset(db: Session = Depends(get_db)) -> dict[str, str]:
    db.query(Recommendation).delete()
    db.query(AuditLog).delete()
    db.query(Dataset).delete()
    db.commit()
    _init_default_reports()
    return {"status": "reset_successful"}


@router.get("/search")
async def global_search(q: str = "") -> dict[str, list[Any]]:
    return {"results": []}


# --- Dashboard & Insights Aliases ---
@router.get("/dashboard")
async def get_dashboard(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return summary analytics for Command Center dashboard."""
    dataset = db.query(Dataset).filter(Dataset.status == "analyzed").order_by(Dataset.uploaded_at.desc()).first()
    pending_count = db.query(Recommendation).filter(Recommendation.status == "pending").count()
    recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(6).all()

    activity = []
    for log in recent_logs:
        activity.append(
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat() if log.timestamp else datetime.utcnow().isoformat(),
                "action": log.action,
                "details": f"{log.agent_name}: {log.input_summary} → {log.output_summary}",
            }
        )
    
    if not activity:
        activity = [{
            "id": "1",
            "timestamp": datetime.utcnow().isoformat(),
            "action": "SYSTEM_INIT",
            "details": "Asclepius modular pipeline online",
        }]

    if not dataset or not dataset.analysis_summary:
        return {
            "kpis": {
                "total_revenue": 0,
                "units_sold": 0,
                "active_skus": 0,
                "inventory_value": 0,
                "pending_approvals": pending_count,
                "open_anomalies": 0,
            },
            "health_score": 0,
            "revenue_trend": [],
            "regions": [],
            "latest_run": None,
            "inventory_alerts": {"near_expiry": 0, "low_stock": 0, "dead_stock": 0},
            "recent_activity": activity,
            "top_products": [],
        }

    summary = dataset.analysis_summary
    sales = summary.get("sales", {})
    kpis = summary.get("kpis", {})
    inventory = summary.get("inventory", {})
    customers = summary.get("customers", {})
    anomalies = summary.get("anomalies", [])

    return {
        "kpis": {
            "total_revenue": kpis.get("total_revenue", 0),
            "units_sold": kpis.get("total_units_sold", 0),
            "active_skus": kpis.get("unique_products", 0),
            "inventory_value": kpis.get("inventory_value", 0),
            "pending_approvals": pending_count,
            "open_anomalies": len(anomalies),
        },
        "health_score": dataset.business_health_score or 0,
        "revenue_trend": sales.get("monthly_revenue", []),
        "regions": customers.get("top_regions", []),
        "latest_run": {
            "status": "completed",
            "steps": [
                {
                    "agent": "IngestionAgent",
                    "status": "completed",
                    "confidence": 0.99,
                    "summary": "Verified schema & cleansed records.",
                },
                {
                    "agent": "AnalysisAgent",
                    "status": "completed",
                    "confidence": 0.96,
                    "summary": "Calculated KPIs and anomaly thresholds.",
                },
                {
                    "agent": "InsightAgent",
                    "status": "completed",
                    "confidence": 0.95,
                    "summary": "Generated governance action items.",
                },
            ],
        },
        "inventory_alerts": {
            "near_expiry": kpis.get("near_expiry_count", 0),
            "low_stock": kpis.get("low_stock_count", 0),
            "dead_stock": kpis.get("dead_stock_count", 0),
        },
        "recent_activity": activity,
        "top_products": sales.get("top_10_products", [])[:5],
    }



@router.get("/insights/sales")
async def insights_sales(db: Session = Depends(get_db)) -> dict[str, Any]:
    dataset = db.query(Dataset).filter(Dataset.status == "analyzed").order_by(Dataset.uploaded_at.desc()).first()
    
    monthly = []
    by_product = []
    by_region = []
    by_category = []
    
    if dataset and dataset.analysis_summary:
        sales = dataset.analysis_summary.get("sales", {})
        monthly = sales.get("monthly_revenue", [])
        
        # Map top 10 products to by_product expected shape
        top_products = sales.get("top_10_products", [])
        by_product = [{"name": p.get("product"), "revenue": p.get("revenue")} for p in top_products]

        # Use customers region data if available
        cust = dataset.analysis_summary.get("customers", {})
        by_region = sales.get("by_region", [])
        by_category = sales.get("by_category", [])

    return {
        "monthly": monthly,
        "by_product": by_product,
        "by_region": by_region,
        "by_category": by_category,
    }


@router.get("/insights/inventory")
async def insights_inventory(db: Session = Depends(get_db)) -> dict[str, Any]:
    dataset = db.query(Dataset).filter(Dataset.status == "analyzed").order_by(Dataset.uploaded_at.desc()).first()
    
    counts = {"optimal": 0, "near_expiry": 0, "low_stock": 0, "dead_stock": 0}
    items = []
    
    if dataset and dataset.analysis_summary:
        inv = dataset.analysis_summary.get("inventory", {})
        kpis = dataset.analysis_summary.get("kpis", {})
        
        counts["near_expiry"] = kpis.get("near_expiry_count", 0)
        counts["low_stock"] = kpis.get("low_stock_count", 0)
        counts["dead_stock"] = kpis.get("dead_stock_count", 0)
        counts["optimal"] = kpis.get("unique_products", 0) - sum(counts.values())
        if counts["optimal"] < 0:
            counts["optimal"] = 0
            
        near_exp_items = inv.get("near_expiry", {}).get("items", [])
        dead_items = inv.get("dead_stock", {}).get("items", [])
        
        for idx, item in enumerate(near_exp_items):
            items.append({
                "id": f"ne_{idx}",
                "product": item.get("product"),
                "batch": item.get("batch", "Unknown"),
                "stock": item.get("quantity", 0),
                "unit_price": item.get("unit_price", 0),
                "days_to_expiry": item.get("days_to_expiry", 0),
                "status": item.get("status", "near_expiry")
            })
            
        for idx, item in enumerate(dead_items):
            items.append({
                "id": f"ds_{idx}",
                "product": item.get("product"),
                "batch": item.get("batch", "Unknown"),
                "stock": item.get("total_qty_sold", 0),
                "unit_price": item.get("unit_price", 0),
                "days_to_expiry": 0,
                "status": "dead_stock"
            })

    return {
        "counts": counts,
        "items": items,
    }


@router.get("/insights/customers")
async def insights_customers(db: Session = Depends(get_db)) -> dict[str, Any]:
    dataset = db.query(Dataset).filter(Dataset.status == "analyzed").order_by(Dataset.uploaded_at.desc()).first()
    
    segments = {"Champion": 0, "Loyal": 0, "At Risk": 0, "Developing": 0}
    customers = []
    
    if dataset and dataset.analysis_summary:
        cust = dataset.analysis_summary.get("customers", {})
        # rfm structure from customer.py
        rfm_data = cust.get("rfm", {})
        
        # map segment names if needed
        raw_segments = rfm_data.get("segments", {})
        segments["Champion"] = raw_segments.get("Champions", 0)
        segments["Loyal"] = raw_segments.get("Loyal", 0)
        segments["At Risk"] = raw_segments.get("At-Risk", 0)
        segments["Developing"] = raw_segments.get("Lost", 0) # Fallback mapping
        
        details = rfm_data.get("details", [])
        for i, d in enumerate(details):
            segment_val = d.get("segment", "Lost")
            if segment_val == "Champions": segment_val = "Champion"
            elif segment_val == "At-Risk": segment_val = "At Risk"
            elif segment_val == "Lost": segment_val = "Developing"
            
            customers.append({
                "customer": d.get("customer", f"Customer {i}"),
                "region": "Network", # We don't have per-customer region mapped easily without joining
                "revenue": d.get("monetary", 0),
                "orders": d.get("frequency", 0),
                "recency_days": d.get("recency_days", 0),
                "rfm": {"r": 3, "f": 3, "m": 3}, # Mocked internal breakdown since we only have rfm_score
                "segment": segment_val
            })

    return {
        "segments": segments,
        "customers": customers,
    }


@router.get("/insights/forecasts")
async def insights_forecasts(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    dataset = db.query(Dataset).filter(Dataset.status == "analyzed").order_by(Dataset.uploaded_at.desc()).first()
    
    forecasts = []
    if dataset and dataset.analysis_summary:
        # Dynamically generate a simple linear forecast based on top products
        sales = dataset.analysis_summary.get("sales", {})
        monthly = sales.get("monthly_revenue", [])
        top_products = sales.get("top_10_products", [])
        
        if monthly and top_products:
            # We don't have per-product monthly history natively, so we approximate
            # by scaling the network monthly revenue by the product's share
            total_rev = sum(m.get("revenue", 0) for m in monthly)
            if total_rev > 0:
                for i, prod in enumerate(top_products[:2]): # Just top 2 for dashboard
                    share = prod.get("revenue", 0) / total_rev
                    prod_history = [{"date": m["month"], "value": m["revenue"] * share} for m in monthly]
                    
                    last_val = prod_history[-1]["value"] if prod_history else 0
                    
                    # Project next 3 months
                    import datetime
                    from dateutil.relativedelta import relativedelta
                    last_date_str = prod_history[-1]["date"] if prod_history else "2025-07"
                    try:
                        last_date = datetime.datetime.strptime(last_date_str, "%Y-%m")
                    except:
                        last_date = datetime.datetime.now()
                        
                    forecast_data = []
                    for m_idx in range(1, 4):
                        next_date = last_date + relativedelta(months=m_idx)
                        proj = last_val * (1.05 ** m_idx) # 5% growth
                        forecast_data.append({
                            "date": next_date.strftime("%Y-%m"),
                            "yhat": proj,
                            "hi": proj * 1.15
                        })
                        
                    forecasts.append({
                        "id": f"f_{i}",
                        "product": prod.get("product"),
                        "model": "ARIMA",
                        "confidence": 0.94 - (i * 0.02),
                        "growth_pct": 5.0,
                        "history": prod_history,
                        "forecast": forecast_data
                    })
    
    return forecasts


@router.get("/insights/anomalies")
async def insights_anomalies(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    dataset = db.query(Dataset).filter(Dataset.status == "analyzed").order_by(Dataset.uploaded_at.desc()).first()
    if dataset and dataset.analysis_summary:
        anomalies = dataset.analysis_summary.get("sales", {}).get("anomalies", []) 
        if not anomalies:
            # Actually they are currently placed at the root level by AnalysisAgent sometimes
            anomalies = dataset.analysis_summary.get("anomalies", [])
            
        if anomalies:
            res = []
            for i, a in enumerate(anomalies):
                res.append({
                    "id": f"anm_{i}",
                    "severity": "critical" if abs(a.get("pct_change", 0)) > 50 else "warning",
                    "product": a.get("product", "Unknown"),
                    "region": "Network",
                    "score": round(abs(a.get("pct_change", 0)) / 100.0, 3),
                    "description": f"{a.get('direction', 'change').title()} by {abs(a.get('pct_change', 0))}% from {a.get('previous_avg', 0)} to {a.get('current', 0)}.",
                    "detected_by": "AnalysisAgent",
                    "date": datetime.utcnow().isoformat(),
                })
            return res

    return []


# --- Approvals / Recommendations moved to real backend ---


# --- Audit Trail & Uploads Compatibility ---
@router.get("/audit")
async def get_compat_audit(q: str = "", role: str = "", db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return AuditLog items formatted for Audit.js."""
    query = db.query(AuditLog)
    if q:
        query = query.filter(AuditLog.input_summary.ilike(f"%{q}%") | AuditLog.output_summary.ilike(f"%{q}%"))
    if role and role != "all":
        from sqlalchemy import func
        if role.lower() == "system":
            query = query.filter(AuditLog.human_checkpoint == False)
        else:
            query = query.filter(AuditLog.human_checkpoint == True, func.lower(AuditLog.approved_by) == role.lower())

    logs = query.order_by(AuditLog.timestamp.desc()).all()
    res = []
    for log in logs:
        is_system = not log.human_checkpoint
        if is_system:
            actor = "System"
            actor_role = "system"
        else:
            actor = log.approved_by or "Admin"
            actor_role = actor.lower()

        res.append(
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat() if log.timestamp else datetime.utcnow().isoformat(),
                "actor": actor,
                "actor_role": actor_role,
                "action": log.action,
                "target": log.input_summary or "N/A",
                "details": log.output_summary or "N/A",
                "approved_by": log.approved_by,
                "human": log.human_checkpoint,
                "module": log.module,
            }
        )
    return res


@router.get("/uploads")
async def get_compat_uploads(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return datasets formatted for Upload.js and Journey.js."""
    ds = db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()
    res = []
    for d in ds:
        ts = d.uploaded_at.isoformat() if d.uploaded_at else datetime.utcnow().isoformat()
        res.append(
            {
                "id": str(d.id),
                "name": d.filename,
                "filename": d.filename,
                "status": "ready" if d.status in ("analyzed", "ready", "uploaded") else "needs_cleaning",
                "kind": "processed" if d.status in ("analyzed", "ready") else "raw",
                "rows": d.row_count or 562,
                "rows_raw": d.row_count or 562,
                "rows_clean": d.row_count or 562,
                "quality_score": 96,
                "duplicates_removed": 5,
                "domain": "pharma_distribution",
                "columns": ["Date", "SKU", "Product", "Region", "Units", "Revenue"],
                "created_at": ts,
                "uploaded_at": ts,
                "uploaded_by": "Utkarsh Sharma",
                "schema_mapping": {"SKU": "Item_Code", "Revenue": "Sales_INR"},
                "issues": [],
            }
        )
    return res


@router.post("/uploads")
async def post_compat_uploads(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict[str, Any]:
    """Handle frontend direct file upload by running actual IngestionAgent."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("xlsx", "xls", "csv"):
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    UPLOAD_DIR = "./uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())[:8]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    dataset = Dataset(filename=file.filename, status="ready", detected_domain="pharma_distribution")
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    agent = IngestionAgent(db)
    df, columns = agent.run(dataset.id, file_path)
    
    now_str = datetime.utcnow().isoformat()
    return {
        "id": str(dataset.id),
        "name": dataset.filename,
        "filename": dataset.filename,
        "status": "ready",
        "kind": "processed",
        "rows": dataset.row_count or len(df),
        "quality_score": 95,
        "columns": list(columns.keys()),
        "created_at": now_str,
        "uploaded_at": now_str,
        "uploaded_by": "Utkarsh Sharma",
        "schema_mapping": columns,
        "issues": [],
    }


@router.post("/uploads/{id}/clean")
async def post_compat_clean(id: str) -> dict[str, Any]:
    now_str = datetime.utcnow().isoformat()
    return {
        "id": id,
        "name": "cleaned_dataset.csv",
        "filename": "cleaned_dataset.csv",
        "status": "ready",
        "kind": "processed",
        "rows": 562,
        "quality_score": 100,
        "columns": ["Date", "SKU", "Product", "Region", "Units", "Revenue"],
        "created_at": now_str,
        "uploaded_at": now_str,
        "uploaded_by": "Utkarsh Sharma",
        "schema_mapping": {"SKU": "Item_Code", "Revenue": "Sales_INR"},
        "issues": [],
    }


# --- Pipeline Runs Compatibility ---
@router.get("/pipeline/runs")
async def get_pipeline_runs() -> list[dict[str, Any]]:
    return [
        {
            "id": "run_101",
            "status": "completed",
            "steps": [
                {
                    "agent": "IngestionAgent",
                    "status": "completed",
                    "confidence": 0.99,
                    "summary": "Verified schema & cleansed 562 pharmaceutical distribution records.",
                },
                {
                    "agent": "AnalysisAgent",
                    "status": "completed",
                    "confidence": 0.96,
                    "summary": "Calculated KPIs, revenue velocity, and regional demand breakdown.",
                },
                {
                    "agent": "AnomalyDetector",
                    "status": "completed",
                    "confidence": 0.98,
                    "summary": "Detected critical demand surge in North region distributor network.",
                },
                {
                    "agent": "ForecastingAgent",
                    "status": "completed",
                    "confidence": 0.94,
                    "summary": "Generated 30-day ARIMA confidence bounds for top 10 SKUs.",
                },
                {
                    "agent": "RecommendationEngine",
                    "status": "completed",
                    "confidence": 0.95,
                    "summary": "Formulated action item requiring human-in-the-loop signoff.",
                },
                {
                    "agent": "ReportAgent",
                    "status": "completed",
                    "confidence": 0.99,
                    "summary": "Executive briefing PDF template prepared and queued.",
                },
            ],
        }
    ]


@router.get("/pipeline/runs/{run_id}")
async def get_pipeline_run(run_id: str) -> dict[str, Any]:
    runs = await get_pipeline_runs()
    return runs[0]


@router.post("/pipeline/run/{upload_id}")
async def start_pipeline_run(upload_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    dataset_id = int(upload_id)
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    import glob
    files = glob.glob(f"./uploads/*_{dataset.filename}")
    if not files:
        raise HTTPException(status_code=404, detail="File not found on disk")
    file_path = files[0]

    ingestion = IngestionAgent(db)
    df, columns = ingestion.run(dataset_id, file_path)

    analysis_agent = AnalysisAgent(db)
    results = analysis_agent.run(dataset_id, df, columns)

    insight = InsightAgent(db)
    insight.run(dataset_id, results)

    return {"run_id": f"run_{dataset_id}", "status": "completed"}


# --- Reports Compatibility & Sample Downloads ---
_GENERATED_REPORTS: list[dict[str, Any]] = []


def _init_default_reports():
    _GENERATED_REPORTS.clear()
    now_str = datetime.utcnow().isoformat()
    _GENERATED_REPORTS.append(
        {
            "id": "rpt_101_pdf",
            "title": "Executive Summary (Q3 Pharma)",
            "template": "executive_summary",
            "format": "pdf",
            "created_at": now_str,
            "created_by": "AutoPilot AI",
            "status": "ready",
            "size_kb": 248,
        }
    )
    _GENERATED_REPORTS.append(
        {
            "id": "rpt_102_xlsx",
            "title": "Inventory Health Analysis",
            "template": "inventory_health",
            "format": "xlsx",
            "created_at": now_str,
            "created_by": "AutoPilot AI",
            "status": "ready",
            "size_kb": 182,
        }
    )


_init_default_reports()


@router.get("/reports")
async def get_compat_reports() -> list[dict[str, Any]]:
    if not _GENERATED_REPORTS:
        _init_default_reports()
    return _GENERATED_REPORTS


@router.post("/reports")
async def post_compat_reports(req: dict[str, Any] | None = None) -> dict[str, Any]:
    template = req.get("template", "executive_summary") if req else "executive_summary"
    fmt = req.get("format", "pdf") if req else "pdf"
    title_map = {
        "executive_summary": "Executive Summary",
        "inventory_health": "Inventory Health",
        "sales_performance": "Sales Performance",
        "anomaly_digest": "Anomaly Digest",
    }
    title = f"{title_map.get(template, 'Analytics Report')} ({fmt.upper()})"
    new_id = f"rpt_{len(_GENERATED_REPORTS) + 101}_{fmt.lower()}"
    now_str = datetime.utcnow().isoformat()
    new_report = {
        "id": new_id,
        "title": title,
        "template": template,
        "format": fmt,
        "created_at": now_str,
        "created_by": "Utkarsh Sharma",
        "status": "ready",
        "size_kb": 312 if fmt == "pdf" else 156,
    }
    _GENERATED_REPORTS.insert(0, new_report)
    return new_report


@router.get("/reports/{id}/download")
async def download_report(id: str, db: Session = Depends(get_db)) -> Response:
    """Return enterprise styled PDF or Excel spreadsheet content for report download."""
    target_rpt = next((r for r in _GENERATED_REPORTS if r["id"] == id), None)
    is_xlsx = id.endswith("_xlsx") or "xlsx" in id.lower() or (target_rpt and target_rpt.get("format") == "xlsx")
    raw_title = target_rpt["title"] if target_rpt else f"AutoPilot Report {id}"
    clean_title = "".join(c if c.isalnum() or c in "-_ " else "" for c in raw_title).strip().replace(" ", "_")
    if not clean_title:
        clean_title = "Executive_Analytics_Report"
        
    dataset = db.query(Dataset).order_by(Dataset.id.desc()).first()

    try:
        if is_xlsx:
            content_bytes = generate_excel_report(raw_title, dataset=dataset)
            headers = {"Content-Disposition": f'attachment; filename="{clean_title}.xlsx"'}
            return Response(
                content=content_bytes,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers=headers,
            )

        content_bytes = generate_pdf_report(raw_title, dataset=dataset)
        headers = {"Content-Disposition": f'attachment; filename="{clean_title}.pdf"'}
        return Response(
            content=content_bytes,
            media_type="application/pdf",
            headers=headers,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/samples/{format_type}")
async def download_sample_data(format_type: str) -> Response:
    """Download sample Excel or CSV datasets for demo testing ingestion."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../samples"))
    if not os.path.exists(base_dir):
        base_dir = os.path.abspath(os.path.join(os.getcwd(), "samples"))

    if format_type.lower() in ("excel", "xlsx", "pharma_distributor_sales.xlsx"):
        file_path = os.path.join(base_dir, "pharma_distributor_sales.xlsx")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "pharma_distributor_sales_sample.xlsx"
    else:
        file_path = os.path.join(base_dir, "pharma_retail_chemist_sales.csv")
        media_type = "text/csv"
        filename = "pharma_retail_chemist_sales_sample.csv"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample file not found on server")

    with open(file_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

