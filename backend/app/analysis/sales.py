"""Sales analysis module.

Computes revenue metrics, product rankings, trends, and anomaly detection.
All computations are deterministic Pandas operations — no LLM calls.
"""
from typing import Any

import numpy as np
import pandas as pd


def analyze_sales(df: pd.DataFrame, columns: dict[str, str]) -> dict[str, Any]:
    """Run complete sales analysis on a cleaned DataFrame.

    Args:
        df: Cleaned DataFrame with standardized column names.
        columns: Mapping of semantic types to column names,
                 e.g. {"revenue": "amount", "product": "product_name", "date": "invoice_date"}

    Returns:
        Dictionary of sales metrics and rankings.
    """
    results: dict[str, Any] = {}

    revenue_col = columns.get("revenue")
    product_col = columns.get("product")
    date_col = columns.get("date")
    qty_col = columns.get("quantity")
    customer_col = columns.get("customer")

    if not revenue_col or revenue_col not in df.columns:
        return {"error": "No revenue column found"}

    # --- Basic revenue metrics ---
    results["total_revenue"] = round(float(df[revenue_col].sum()), 2)
    mean_val = df[revenue_col].mean()
    results["avg_transaction"] = round(float(mean_val), 2) if not np.isnan(mean_val) else 0.0
    med_val = df[revenue_col].median()
    results["median_transaction"] = round(float(med_val), 2) if not np.isnan(med_val) else 0.0
    results["transaction_count"] = len(df)

    # --- Product rankings ---
    if product_col and product_col in df.columns:
        product_revenue = (
            df.groupby(product_col)[revenue_col]
            .sum()
            .sort_values(ascending=False)
        )
        results["top_10_products"] = [
            {"product": str(name), "revenue": round(float(rev), 2)}
            for name, rev in product_revenue.head(10).items()
        ]
        results["bottom_10_products"] = [
            {"product": str(name), "revenue": round(float(rev), 2)}
            for name, rev in product_revenue.tail(10).items()
        ]
        results["unique_products"] = int(product_revenue.shape[0])

    # --- Monthly revenue trend ---
    if date_col and date_col in df.columns:
        df_dated = df.copy()
        df_dated[date_col] = pd.to_datetime(df_dated[date_col], errors="coerce")
        df_dated = df_dated.dropna(subset=[date_col])
        df_dated["month"] = df_dated[date_col].dt.to_period("M").astype(str)

        monthly = df_dated.groupby("month")[revenue_col].sum().sort_index()
        results["monthly_revenue"] = [
            {"month": str(m), "revenue": round(float(r), 2)}
            for m, r in monthly.items()
        ]

        # Month-over-month growth
        if len(monthly) >= 2:
            values = monthly.values
            growths = []
            for i in range(1, len(values)):
                if values[i - 1] > 0:
                    g = ((values[i] - values[i - 1]) / values[i - 1]) * 100
                    growths.append(round(float(g), 1))
            results["mom_growth_rates"] = growths
            results["avg_mom_growth"] = round(float(np.mean(growths)), 1) if growths else 0.0

    # --- Average order value ---
    if customer_col and customer_col in df.columns and date_col and date_col in df.columns:
        aov = df[revenue_col].mean()
        results["avg_order_value"] = round(float(aov), 2) if not np.isnan(aov) else 0.0

    # --- Revenue concentration (Pareto) ---
    if product_col and product_col in df.columns:
        product_revenue = (
            df.groupby(product_col)[revenue_col].sum().sort_values(ascending=False)
        )
        total = product_revenue.sum()
        if total > 0:
            product_revenue.cumsum() / total
            top_20_pct = max(1, int(len(product_revenue) * 0.2))
            top_20_revenue_share = round(
                float(product_revenue.head(top_20_pct).sum() / total * 100), 1
            )
            results["pareto_top20_revenue_share"] = top_20_revenue_share

    # --- Sales velocity (units per day per product) ---
    if product_col and qty_col and date_col and all(c in df.columns for c in [product_col, qty_col, date_col]):
        df_v = df.copy()
        df_v[date_col] = pd.to_datetime(df_v[date_col], errors="coerce")
        df_v = df_v.dropna(subset=[date_col])
        if len(df_v) > 0:
            date_span = (df_v[date_col].max() - df_v[date_col].min()).days or 1
            velocity = (
                df_v.groupby(product_col)[qty_col].sum() / date_span
            ).sort_values(ascending=False)
            results["sales_velocity"] = [
                {"product": str(p), "units_per_day": round(float(v), 2)}
                for p, v in velocity.head(10).items()
            ]

    # --- Category mix ---
    category_col = columns.get("category")
    if category_col and category_col in df.columns:
        cat_rev = df.groupby(category_col)[revenue_col].sum().sort_values(ascending=False)
        results["by_category"] = [
            {"name": str(c), "revenue": round(float(r), 2)}
            for c, r in cat_rev.items()
        ]

    # --- Region split ---
    region_col = columns.get("region")
    if region_col and region_col in df.columns:
        reg_rev = df.groupby(region_col)[revenue_col].sum().sort_values(ascending=False)
        results["by_region"] = [
            {"name": str(r), "revenue": round(float(rev), 2)}
            for r, rev in reg_rev.items()
        ]

    return results


def detect_anomalies(df: pd.DataFrame, columns: dict[str, str]) -> list[dict[str, Any]]:
    """Detect products with significant sales changes.

    Compares each product's recent-period sales against its overall average.
    Products with >30% deviation are flagged.

    Args:
        df: Cleaned DataFrame.
        columns: Column mapping.

    Returns:
        List of anomaly dicts with product, direction, values, pct_change.
    """
    product_col = columns.get("product")
    revenue_col = columns.get("revenue")
    date_col = columns.get("date")

    if not all(c and c in df.columns for c in [product_col, revenue_col, date_col]):
        return []

    df_c = df.copy()
    df_c[date_col] = pd.to_datetime(df_c[date_col], errors="coerce")
    df_c = df_c.dropna(subset=[date_col])

    if len(df_c) < 10:
        return []

    # Split into first half / second half
    midpoint = df_c[date_col].min() + (df_c[date_col].max() - df_c[date_col].min()) / 2

    early = df_c[df_c[date_col] <= midpoint].groupby(product_col)[revenue_col].sum()
    late = df_c[df_c[date_col] > midpoint].groupby(product_col)[revenue_col].sum()

    anomalies = []
    for product in early.index:
        early_val = float(early.get(product, 0))
        late_val = float(late.get(product, 0))

        if early_val <= 0:
            continue

        pct_change = ((late_val - early_val) / early_val) * 100

        if abs(pct_change) > 30:
            anomalies.append({
                "product": str(product),
                "direction": "increasing" if pct_change > 0 else "declining",
                "previous_avg": round(early_val, 2),
                "current": round(late_val, 2),
                "pct_change": round(pct_change, 1),
            })

    # Sort by absolute change
    anomalies.sort(key=lambda x: abs(x["pct_change"]), reverse=True)
    return anomalies
