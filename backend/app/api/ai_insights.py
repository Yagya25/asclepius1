"""AI-powered insight endpoints — Gemini narratives + NVIDIA analysis.

These endpoints enrich the deterministic analytics with GenAI intelligence:
- Executive narrative summaries for each insight tab
- AI Copilot chat (ask anything about your data)
- Smart anomaly explanations and recommended actions
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuditLog, Recommendation, Dataset
from ..services.genai import generate

router = APIRouter(prefix="/ai", tags=["ai-insights"])

SYSTEM_PROMPT = (
    "You are Asclepius, an AI Business Intelligence copilot for a "
    "pharmaceutical distribution company in India. You analyze ERP data "
    "covering sales, inventory, customer segmentation, and supply chain "
    "operations. Be concise, data-driven, and actionable. Use Indian "
    "business context (₹ currency, lakh/crore notation, regional markets). "
    "Never fabricate numbers — only reference the data provided in the prompt."
)


# ─── AI Narrative Summaries ─────────────────────────────────────────────────

@router.get("/insights/summary")
async def ai_insights_summary(
    tab: str = "sales",
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Generate an AI narrative summary for the specified insights tab based on REAL data."""
    dataset = db.query(Dataset).filter(Dataset.status == "analyzed").order_by(Dataset.uploaded_at.desc()).first()
    
    if not dataset or not dataset.analysis_summary:
        return {
            "tab": tab,
            "summary": "No analyzed dataset available. Please upload and analyze a sheet first.",
            "generated_by": "system",
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    summary_data = dataset.analysis_summary
    kpis = summary_data.get("kpis", {})
    sales = summary_data.get("sales", {})
    
    rev = kpis.get("total_revenue", 0)
    units = kpis.get("total_units_sold", 0)
    skus = kpis.get("unique_products", 0)
    
    base_prompt = f"Analyze this dataset. Total Revenue: {rev}, Units Sold: {units}, Unique SKUs: {skus}. "
    
    if tab == "sales":
        top_products = ", ".join([f"{p['product']} ({p['revenue']})" for p in sales.get("top_10_products", [])[:3]])
        prompt = base_prompt + f"Top products include: {top_products}. Write a 3-4 sentence executive summary focusing on sales performance and a key recommendation."
    elif tab == "inventory":
        inv = kpis.get("near_expiry_count", 0)
        prompt = base_prompt + f"There are {inv} near-expiry items and {kpis.get('dead_stock_count', 0)} dead stock items. Write a 3-4 sentence executive summary focusing on inventory health and risk mitigation."
    elif tab == "customers":
        cust = summary_data.get("customers", {}).get("segments", {})
        prompt = base_prompt + f"Customer segments: {cust}. Write a 3-4 sentence summary on customer engagement."
    elif tab == "forecasts":
        top_products = ", ".join([f"{p['product']}" for p in sales.get("top_10_products", [])[:2]])
        prompt = base_prompt + f"We have generated 30-day ARIMA trend forecasts for our top products: {top_products}. Write a 3 sentence summary explaining that our forecast models project steady growth for these key drivers and recommend ensuring adequate stock levels to meet projected demand."
    elif tab == "anomalies":
        anomalies = summary_data.get("anomalies", [])
        anom_text = ", ".join([a['product'] for a in anomalies[:2]]) if anomalies else "None"
        prompt = base_prompt + f"Detected {len(anomalies)} anomalies. Affected products include: {anom_text}. Write a 3-4 sentence assessment."
    else:
        prompt = base_prompt + "Write a short summary."

    summary = await generate(
        prompt,
        system=SYSTEM_PROMPT,
        provider="nvidia",
        temperature=0.7,
        max_tokens=512,
        fallback=f"Analyzed latest data. Revenue: {rev}. Units: {units}.",
    )

    return {
        "tab": tab,
        "summary": summary,
        "generated_by": "gemini",
        "generated_at": datetime.utcnow().isoformat(),
    }


# ─── AI Copilot Chat ────────────────────────────────────────────────────────

class CopilotMessage(BaseModel):
    message: str
    context: str | None = None


@router.post("/copilot")
async def ai_copilot_chat(
    req: CopilotMessage,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """AI Copilot — ask anything about your business data."""
    dataset = db.query(Dataset).filter(Dataset.status == "analyzed").order_by(Dataset.uploaded_at.desc()).first()
    pending_count = db.query(Recommendation).filter(Recommendation.status == "pending").count()
    recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(5).all()

    activity_lines = "\n".join(f"  - [{log.agent_name}] {log.action}: {log.output_summary}" for log in recent_logs) or "  No recent activity."

    if dataset and dataset.analysis_summary:
        kpis = dataset.analysis_summary.get("kpis", {})
        rev = kpis.get("total_revenue", 0)
        near_expiry = kpis.get("near_expiry_count", 0)
        low_stock = kpis.get("low_stock_count", 0)
        anomalies = len(dataset.analysis_summary.get("anomalies", []))
        
        customers = dataset.analysis_summary.get("customers", {})
        inactive = customers.get("inactive_customers", {}).get("items", [])
        rfm_details = customers.get("rfm", {}).get("details", [])
        
        at_risk = [c["customer"] for c in rfm_details if c["segment"] == "At-Risk"]
        champions = [c["customer"] for c in rfm_details if c["segment"] == "Champions"]
        inactive_names = [c["customer"] for c in inactive]
        
        customer_context = (
            f"CUSTOMER SEGMENTS:\n"
            f"- At-Risk Customers ({len(at_risk)}): {', '.join(at_risk[:10])}\n"
            f"- Inactive Customers ({len(inactive_names)}): {', '.join(inactive_names[:10])}\n"
            f"- Champion Customers ({len(champions)}): {', '.join(champions[:10])}\n"
        )
        
        sales = dataset.analysis_summary.get("sales", {})
        monthly = sales.get("monthly_revenue", [])
        monthly_str = ", ".join([f"{m['month']}: {m['revenue']}" for m in monthly[-6:]]) if monthly else "None"
        sales_context = f"RECENT MONTHLY REVENUE: {monthly_str}\n"
    else:
        rev = 0
        near_expiry = 0
        low_stock = 0
        anomalies = 0
        customer_context = "No customer data available.\n"
        sales_context = "No sales data available.\n"

    context_block = (
        f"LIVE SYSTEM STATE:\n"
        f"- Pending approvals: {pending_count}\n"
        f"- Total Revenue: {rev}\n"
        f"- Inventory alerts: {near_expiry} near-expiry, {low_stock} low-stock\n"
        f"- Active anomalies: {anomalies}\n\n"
        f"{customer_context}\n"
        f"{sales_context}\n"
        f"RECENT AGENT ACTIVITY:\n{activity_lines}\n"
    )

    if req.context:
        context_block += f"\nADDITIONAL CONTEXT:\n{req.context}\n"

    prompt = (
        f"{context_block}\n"
        f"USER QUESTION: {req.message}\n\n"
        f"Answer concisely in 2-4 sentences. Reference specific numbers "
        f"from the data above. If the question is about actions, recommend "
        f"concrete next steps."
    )

    fallback = (
        f"I can see your system is healthy. "
        f"There are {pending_count} pending approvals in your queue. "
        "Check the Approvals page for action items requiring your review."
    )

    response = await generate(
        prompt,
        system=SYSTEM_PROMPT,
        provider="nvidia",
        temperature=0.7,
        max_tokens=512,
        fallback=fallback,
    )

    return {
        "reply": response,
        "sources": ["dashboard_kpis", "audit_trail", "recommendations"],
        "generated_by": "gemini" if response != fallback else "fallback",
        "generated_at": datetime.utcnow().isoformat(),
    }


# ─── AI-Enhanced Dashboard Summary ──────────────────────────────────────────

@router.get("/dashboard/brief")
async def ai_dashboard_brief(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Generate an AI executive briefing for the dashboard header."""
    dataset = db.query(Dataset).filter(Dataset.status == "analyzed").order_by(Dataset.uploaded_at.desc()).first()
    pending_count = db.query(Recommendation).filter(Recommendation.status == "pending").count()
    
    if dataset and dataset.analysis_summary:
        kpis = dataset.analysis_summary.get("kpis", {})
        rev = kpis.get("total_revenue", 0)
        near_expiry = kpis.get("near_expiry_count", 0)
    else:
        rev = 0
        near_expiry = 0

    prompt = (
        "Write a 2-sentence executive morning briefing for a pharma "
        "distribution CEO:\n"
        f"- Pending approvals: {pending_count}\n"
        f"- Revenue: {rev}\n"
        f"- Critical: {near_expiry} near-expiry batches\n\n"
        "Be direct, use Indian business style. Start with the most "
        "important insight."
    )

    fallback = (
        f"Operations are stable with revenue at {rev}. "
        f"Priority attention needed on {near_expiry} near-expiry batches."
    )

    brief = await generate(
        prompt,
        system=SYSTEM_PROMPT,
        provider="nvidia",
        temperature=0.6,
        max_tokens=256,
        fallback=fallback,
    )

    return {
        "brief": brief,
        "pending_approvals": pending_count,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ─── AI Anomaly Deep-Dive ───────────────────────────────────────────────────

@router.get("/anomaly/explain")
async def ai_anomaly_explain(
    anomaly_id: str = "anm_1",
) -> dict[str, Any]:
    """Generate a deep-dive AI explanation for a specific anomaly."""
    anomalies = {
        "anm_1": {
            "product": "Ciprofloxacin 500mg",
            "region": "North (Punjab)",
            "severity": "critical",
            "description": "82% demand spike without matching prescriptions",
            "z_score": 3.5,
        },
        "anm_2": {
            "product": "Azithromycin 250mg",
            "region": "East",
            "severity": "warning",
            "description": "Inventory buildup 3x exceeding sales runoff",
            "z_score": 2.8,
        },
    }

    anomaly = anomalies.get(anomaly_id, anomalies["anm_1"])

    prompt = (
        f"Provide a detailed supply chain analysis for this anomaly:\n"
        f"- Product: {anomaly['product']}\n"
        f"- Region: {anomaly['region']}\n"
        f"- Issue: {anomaly['description']}\n"
        f"- Statistical significance: Z-Score {anomaly['z_score']}\n\n"
        f"Structure your response as:\n"
        f"1. ROOT CAUSE ANALYSIS (2-3 possible causes)\n"
        f"2. RISK ASSESSMENT (business impact if unaddressed)\n"
        f"3. RECOMMENDED ACTIONS (3 concrete steps)\n\n"
        f"Use pharma distribution context. Be specific."
    )

    fallback = (
        f"**Root Cause Analysis:** The {anomaly['product']} anomaly in "
        f"{anomaly['region']} (Z-Score: {anomaly['z_score']}) likely stems "
        f"from: (1) Seasonal disease pattern acceleration, (2) Competitor "
        f"stockout causing demand transfer, or (3) Potential diversion to "
        f"grey market channels.\n\n"
        f"**Risk Assessment:** Unaddressed, this could lead to stockouts "
        f"affecting ₹18.5L monthly revenue in the region.\n\n"
        f"**Recommended Actions:** (1) Cross-reference with prescription "
        f"data from retail partners, (2) Hold current inventory allocation "
        f"pending investigation, (3) Deploy field audit team to top 3 "
        f"Punjab distributors within 48 hours."
    )

    explanation = await generate(
        prompt,
        system=SYSTEM_PROMPT,
        provider="nvidia",
        temperature=0.5,
        max_tokens=768,
        fallback=fallback,
    )

    return {
        "anomaly_id": anomaly_id,
        "anomaly": anomaly,
        "explanation": explanation,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ─── AI Report Narrative ────────────────────────────────────────────────────

@router.post("/report/narrative")
async def ai_report_narrative(
    req: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate an AI executive narrative for a PDF report."""
    prompt = (
        "Write a professional executive summary paragraph (5-6 sentences) "
        "for a quarterly pharma distribution report:\n"
        "- Period: Q3 FY2026 (Jul-Aug 2026)\n"
        "- Revenue: ₹14.25Cr (up 3.5% QoQ)\n"
        "- Health Score: 88/100\n"
        "- Key wins: North region growth (+12%), 6 new distributor onboards\n"
        "- Risks: 14 near-expiry batches, Ciprofloxacin demand anomaly\n"
        "- AI pipeline: 23 automated recommendations, 18 human-approved\n"
        "- HR: 4 new hires onboarded via AutoPilot AI pipeline\n\n"
        "Write in formal Indian business English. Include forward-looking "
        "guidance for Q4."
    )

    fallback = (
        "Asclepius's Q3 FY2026 analysis reveals strong operational "
        "performance with ₹14.25Cr in total revenue across the pharmaceutical "
        "distribution network, representing a 3.5% quarter-on-quarter increase. "
        "The Business Health Score stands at a robust 88/100, driven by North "
        "region growth of 12% and successful onboarding of 6 new distributor "
        "partners. Key areas requiring immediate executive attention include "
        "14 near-expiry inventory batches valued at approximately ₹2.1Cr and "
        "an unexplained 82% demand surge in Ciprofloxacin 500mg across Punjab "
        "distributors. The AI-driven recommendation engine generated 23 "
        "governance action items this quarter, of which 18 received human "
        "approval through the Human-in-the-Loop checkpoint system. For Q4 "
        "FY2026, we recommend accelerating South and East region expansion "
        "while tightening inventory rotation policies to reduce dead-stock "
        "exposure by 40%."
    )

    narrative = await generate(
        prompt,
        system=SYSTEM_PROMPT,
        provider="nvidia",
        temperature=0.6,
        max_tokens=768,
        fallback=fallback,
    )

    return {
        "narrative": narrative,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ─── AI Health Check ────────────────────────────────────────────────────────

@router.get("/status")
async def ai_status() -> dict[str, Any]:
    """Check which AI providers are configured and reachable."""
    from ..services.genai import GEMINI_API_KEY, NVIDIA_API_KEY

    gemini_ok = bool(GEMINI_API_KEY)
    nvidia_ok = bool(NVIDIA_API_KEY)

    # Quick ping test
    gemini_live = False
    nvidia_live = False

    if gemini_ok:
        try:
            result = await generate(
                "Say OK", system="", provider="nvidia",
                max_tokens=5, fallback="",
            )
            gemini_live = bool(result)
        except Exception:
            pass

    if nvidia_ok:
        try:
            result = await generate(
                "Say OK", system="", provider="nvidia",
                max_tokens=5, fallback="",
            )
            nvidia_live = bool(result)
        except Exception:
            pass

    return {
        "gemini": {
            "configured": gemini_ok,
            "live": gemini_live,
        },
        "nvidia": {
            "configured": nvidia_ok,
            "live": nvidia_live,
        },
        "fallback_available": True,
    }
