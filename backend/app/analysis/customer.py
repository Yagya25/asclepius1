"""Customer analysis module for pharma distributors.

Covers: RFM segmentation, top/bottom customers, inactive detection,
customer concentration risk, repeat purchase analysis.
"""
from datetime import datetime
from typing import Any

import pandas as pd


def analyze_customers(df: pd.DataFrame, columns: dict[str, str],
                      reference_date: datetime | None = None) -> dict[str, Any]:
    """Run complete customer analysis for pharma distributors."""
    ref = reference_date or datetime.utcnow()
    results: dict[str, Any] = {}
    customer_col = columns.get("customer")
    revenue_col = columns.get("revenue")
    date_col = columns.get("date")
    columns.get("quantity")

    if not customer_col or customer_col not in df.columns:
        return {"error": "No customer column found"}

    results["unique_customers"] = int(df[customer_col].nunique())

    # Top / bottom customers by revenue
    if revenue_col and revenue_col in df.columns:
        cust_rev = df.groupby(customer_col)[revenue_col].sum().sort_values(ascending=False)
        results["top_customers"] = [
            {"customer": str(c), "total_revenue": round(float(r), 2)}
            for c, r in cust_rev.head(10).items()
        ]
        results["bottom_customers"] = [
            {"customer": str(c), "total_revenue": round(float(r), 2)}
            for c, r in cust_rev.tail(5).items()
        ]
        # Concentration risk
        total = cust_rev.sum()
        if total > 0 and len(cust_rev) > 0:
            top_customer_pct = round(float(cust_rev.iloc[0] / total * 100), 1)
            top3_pct = round(float(cust_rev.head(3).sum() / total * 100), 1)
            results["concentration_risk"] = {
                "top_customer_pct": top_customer_pct,
                "top_3_pct": top3_pct,
                "risk_level": "high" if top_customer_pct > 30 else ("medium" if top3_pct > 60 else "low"),
            }

    # RFM Analysis
    if date_col and revenue_col and date_col in df.columns and revenue_col in df.columns:
        results["rfm"] = rfm_analysis(df, customer_col, date_col, revenue_col, ref)

    # Inactive customers
    if date_col and date_col in df.columns:
        results["inactive_customers"] = detect_inactive(df, customer_col, date_col, ref)

    # Repeat purchase rate
    purchase_counts = df.groupby(customer_col).size()
    repeat = int((purchase_counts > 1).sum())
    results["repeat_purchase_rate"] = round(repeat / max(1, len(purchase_counts)) * 100, 1)

    return results


def rfm_analysis(df: pd.DataFrame, customer_col: str, date_col: str,
                 revenue_col: str, ref: datetime) -> dict[str, Any]:
    """RFM (Recency, Frequency, Monetary) segmentation.

    Segments: Champions, Loyal, At-Risk, Lost.
    """
    dc = df.copy()
    dc[date_col] = pd.to_datetime(dc[date_col], errors="coerce")
    dc = dc.dropna(subset=[date_col])

    if len(dc) == 0:
        return {"segments": {}, "details": []}

    ref_ts = pd.Timestamp(ref)
    rfm = dc.groupby(customer_col).agg(
        recency=(date_col, lambda x: (ref_ts - x.max()).days),
        frequency=(date_col, "count"),
        monetary=(revenue_col, "sum"),
    ).reset_index()

    # Score each dimension 1-4 using quartiles
    for col in ["recency", "frequency", "monetary"]:
        try:
            if col == "recency":
                rfm[f"{col}_score"] = pd.qcut(rfm[col], 4, labels=[4, 3, 2, 1], duplicates="drop").astype(int)
            else:
                rfm[f"{col}_score"] = pd.qcut(rfm[col], 4, labels=[1, 2, 3, 4], duplicates="drop").astype(int)
        except (ValueError, TypeError):
            rfm[f"{col}_score"] = 2  # fallback if not enough unique values

    rfm["rfm_score"] = rfm["recency_score"] + rfm["frequency_score"] + rfm["monetary_score"]

    # Segment
    def segment(row):
        s = row["rfm_score"]
        if s >= 10:
            return "Champions"
        elif s >= 7:
            return "Loyal"
        elif s >= 5:
            return "At-Risk"
        else:
            return "Lost"

    rfm["segment"] = rfm.apply(segment, axis=1)

    segment_counts = rfm["segment"].value_counts().to_dict()
    details = []
    for _, row in rfm.iterrows():
        details.append({
            "customer": str(row[customer_col]),
            "recency_days": int(row["recency"]),
            "frequency": int(row["frequency"]),
            "monetary": round(float(row["monetary"]), 2),
            "rfm_score": int(row["rfm_score"]),
            "segment": row["segment"],
        })

    details.sort(key=lambda x: x["rfm_score"], reverse=True)
    return {"segments": segment_counts, "details": details}


def detect_inactive(df: pd.DataFrame, customer_col: str, date_col: str,
                    ref: datetime, threshold_days: int = 60) -> dict[str, Any]:
    """Detect customers with no purchases in the last N days."""
    dc = df.copy()
    dc[date_col] = pd.to_datetime(dc[date_col], errors="coerce")
    dc = dc.dropna(subset=[date_col])

    if len(dc) == 0:
        return {"items": [], "count": 0}

    last_purchase = dc.groupby(customer_col)[date_col].max()
    days_since = (pd.Timestamp(ref) - last_purchase).dt.days
    inactive = days_since[days_since > threshold_days].sort_values(ascending=False)

    items = [{"customer": str(c), "days_since_last_purchase": int(d)}
             for c, d in inactive.items()]

    return {"items": items, "count": len(items), "threshold_days": threshold_days}
