"""KPI engine and Business Health Score for pharma distributors.

The Business Health Score is a composite 0-100 metric that gives
a business owner a single number to understand overall health.
"""
from typing import Any


def compute_all_kpis(sales: dict, inventory: dict, customers: dict) -> dict[str, Any]:
    """Aggregate all analysis results into a unified KPI dashboard."""
    kpis: dict[str, Any] = {}

    # Sales KPIs
    kpis["total_revenue"] = sales.get("total_revenue", 0)
    kpis["transaction_count"] = sales.get("transaction_count", 0)
    kpis["avg_transaction"] = sales.get("avg_transaction", 0)
    kpis["avg_mom_growth"] = sales.get("avg_mom_growth", 0)
    kpis["unique_products"] = sales.get("unique_products", 0)
    kpis["pareto_top20_revenue_share"] = sales.get("pareto_top20_revenue_share", 0)

    # Inventory KPIs
    kpis["inventory_value"] = inventory.get("inventory_value", 0.0)
    kpis["total_units_sold"] = inventory.get("total_units_sold", 0)
    dead = inventory.get("dead_stock", {})
    kpis["dead_stock_count"] = dead.get("count", 0)
    kpis["dead_stock_value"] = dead.get("total_value_at_risk", 0)
    expiry = inventory.get("near_expiry", {})
    kpis["near_expiry_count"] = expiry.get("near_expiry_count", 0)
    kpis["expired_count"] = expiry.get("expired_count", 0)
    kpis["low_stock_count"] = inventory.get("low_stock_count", 0)
    turnover = inventory.get("turnover", {})
    kpis["inventory_turnover"] = turnover.get("overall_turnover", 0)

    # Customer KPIs
    kpis["unique_customers"] = customers.get("unique_customers", 0)
    kpis["repeat_purchase_rate"] = customers.get("repeat_purchase_rate", 0)
    inactive = customers.get("inactive_customers", {})
    kpis["inactive_customer_count"] = inactive.get("count", 0)
    conc = customers.get("concentration_risk", {})
    kpis["customer_concentration_risk"] = conc.get("risk_level", "unknown")

    # Profit leakage
    leakage = inventory.get("profit_leakage", {})
    kpis["total_leakage"] = leakage.get("total_leakage", 0)
    kpis["monthly_leakage_estimate"] = leakage.get("monthly_estimate", 0)

    # Business Health Score
    health = compute_business_health_score(kpis)
    kpis["business_health_score"] = health["score"]
    kpis["health_breakdown"] = health

    return kpis


def compute_business_health_score(kpis: dict) -> dict[str, Any]:
    """Compute composite Business Health Score (0-100).

    Sub-scores:
    - Sales Health (40%): based on growth, revenue diversity
    - Inventory Health (35%): based on dead stock, expiry, turnover
    - Customer Health (25%): based on retention, concentration, activity

    Each sub-score is 0-100. Composite is weighted average.
    """
    sales_health = _compute_sales_health(kpis)
    inventory_health = _compute_inventory_health(kpis)
    customer_health = _compute_customer_health(kpis)

    composite = int(round(
        sales_health * 0.40 +
        inventory_health * 0.35 +
        customer_health * 0.25
    ))
    composite = max(0, min(100, composite))

    return {
        "score": composite,
        "sales_health": sales_health,
        "inventory_health": inventory_health,
        "customer_health": customer_health,
        "interpretation": _interpret_score(composite),
    }


def _compute_sales_health(kpis: dict) -> int:
    """Sales health sub-score (0-100)."""
    score = 60  # baseline

    # Growth factor
    growth = kpis.get("avg_mom_growth", 0)
    if growth > 10:
        score += 20
    elif growth > 0:
        score += 10
    elif growth > -10:
        score -= 5
    else:
        score -= 20

    # Revenue diversity (Pareto — lower concentration is healthier)
    pareto = kpis.get("pareto_top20_revenue_share", 80)
    if pareto < 60:
        score += 15  # well diversified
    elif pareto < 80:
        score += 5
    else:
        score -= 10  # too concentrated

    # Transaction volume
    txns = kpis.get("transaction_count", 0)
    if txns > 200:
        score += 5
    elif txns < 50:
        score -= 10

    return max(0, min(100, score))


def _compute_inventory_health(kpis: dict) -> int:
    """Inventory health sub-score (0-100)."""
    score = 70  # baseline

    # Dead stock penalty
    dead = kpis.get("dead_stock_count", 0)
    total_products = kpis.get("unique_products", 1) or 1
    dead_pct = (dead / total_products) * 100
    if dead_pct > 20:
        score -= 30
    elif dead_pct > 10:
        score -= 15
    elif dead_pct > 0:
        score -= 5

    # Near-expiry penalty (pharma-critical)
    near_exp = kpis.get("near_expiry_count", 0)
    expired = kpis.get("expired_count", 0)
    if expired > 0:
        score -= 20
    if near_exp > 10:
        score -= 15
    elif near_exp > 5:
        score -= 10
    elif near_exp > 0:
        score -= 5

    # Turnover bonus
    turnover = kpis.get("inventory_turnover", 0)
    if turnover > 6:
        score += 10
    elif turnover < 2:
        score -= 10

    return max(0, min(100, score))


def _compute_customer_health(kpis: dict) -> int:
    """Customer health sub-score (0-100)."""
    score = 65  # baseline

    # Repeat purchase rate
    repeat = kpis.get("repeat_purchase_rate", 0)
    if repeat > 80:
        score += 20
    elif repeat > 60:
        score += 10
    elif repeat < 30:
        score -= 15

    # Inactive customers penalty
    inactive = kpis.get("inactive_customer_count", 0)
    total_cust = kpis.get("unique_customers", 1) or 1
    inactive_pct = (inactive / total_cust) * 100
    if inactive_pct > 30:
        score -= 20
    elif inactive_pct > 15:
        score -= 10

    # Concentration risk
    risk = kpis.get("customer_concentration_risk", "unknown")
    if risk == "high":
        score -= 15
    elif risk == "medium":
        score -= 5

    return max(0, min(100, score))


def _interpret_score(score: int) -> str:
    """Plain-language interpretation of the health score."""
    if score >= 80:
        return "Excellent — business is performing well across all dimensions"
    elif score >= 60:
        return "Good — some areas need attention but overall healthy"
    elif score >= 40:
        return "Concerning — multiple issues require immediate action"
    else:
        return "Critical — urgent intervention needed across several areas"
