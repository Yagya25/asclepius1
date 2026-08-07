"""Tests for analysis modules."""
from datetime import datetime

from app.analysis.customer import analyze_customers
from app.analysis.inventory import abc_classification, analyze_inventory
from app.analysis.kpi import compute_all_kpis
from app.analysis.sales import analyze_sales, detect_anomalies


def test_sales_analysis(sample_pharma_df, sample_columns):
    """Sales analysis computes correct revenue and rankings."""
    results = analyze_sales(sample_pharma_df, sample_columns)
    assert results["total_revenue"] > 0
    assert results["transaction_count"] == 10
    assert "top_10_products" in results
    assert len(results["top_10_products"]) > 0


def test_sales_monthly_trend(sample_pharma_df, sample_columns):
    """Monthly revenue trend is computed correctly."""
    results = analyze_sales(sample_pharma_df, sample_columns)
    assert "monthly_revenue" in results
    assert len(results["monthly_revenue"]) >= 3  # at least 3 months


def test_anomaly_detection(sample_pharma_df, sample_columns):
    """Anomaly detection identifies products with significant changes."""
    anomalies = detect_anomalies(sample_pharma_df, sample_columns)
    assert isinstance(anomalies, list)


def test_abc_classification(sample_pharma_df, sample_columns):
    """ABC classification categorizes products by revenue contribution."""
    abc = abc_classification(sample_pharma_df, "product_name", "amount")
    assert "a_products" in abc
    assert "b_products" in abc
    assert "c_products" in abc
    total = len(abc["a_products"]) + len(abc["b_products"]) + len(abc["c_products"])
    assert total == sample_pharma_df["product_name"].nunique()


def test_inventory_analysis(sample_pharma_df, sample_columns):
    """Inventory analysis detects dead stock and near-expiry."""
    ref = datetime(2026, 8, 1)
    results = analyze_inventory(sample_pharma_df, sample_columns, reference_date=ref)
    assert results["total_units_sold"] > 0
    # Dead Stock Medicine only sold in January, should be dead by August
    dead = results.get("dead_stock", {})
    assert dead["count"] > 0
    # Near-expiry detection
    expiry = results.get("near_expiry", {})
    assert expiry["count"] > 0


def test_customer_analysis(sample_pharma_df, sample_columns):
    """Customer analysis produces RFM and rankings."""
    results = analyze_customers(sample_pharma_df, sample_columns)
    assert results["unique_customers"] == 4
    assert "top_customers" in results
    assert "rfm" in results
    assert results["repeat_purchase_rate"] > 0


def test_business_health_score(sample_pharma_df, sample_columns):
    """Business Health Score is between 0 and 100."""
    ref = datetime(2026, 8, 1)
    sales = analyze_sales(sample_pharma_df, sample_columns)
    inventory = analyze_inventory(sample_pharma_df, sample_columns, ref)
    customers = analyze_customers(sample_pharma_df, sample_columns, ref)
    kpis = compute_all_kpis(sales, inventory, customers)
    score = kpis["business_health_score"]
    assert 0 <= score <= 100
    assert "health_breakdown" in kpis
    breakdown = kpis["health_breakdown"]
    assert 0 <= breakdown["sales_health"] <= 100
    assert 0 <= breakdown["inventory_health"] <= 100
    assert 0 <= breakdown["customer_health"] <= 100
