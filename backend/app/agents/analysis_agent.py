"""Analysis Agent: orchestrates all analysis modules.

Calls sales, inventory, customer, and KPI modules.
All numbers come from deterministic Pandas computation — zero LLM.
"""
import pandas as pd

from ..analysis.customer import analyze_customers
from ..analysis.inventory import analyze_inventory
from ..analysis.kpi import compute_all_kpis
from ..analysis.sales import analyze_sales, detect_anomalies
from ..models import Dataset
from .base_agent import BaseAgent


class AnalysisAgent(BaseAgent):
    """Agent 2: Run all business analysis modules and compute KPIs."""

    def __init__(self, db):
        super().__init__("ANALYSIS", db)

    def run(self, dataset_id: int, df: pd.DataFrame, columns: dict[str, str]) -> dict:
        """Run full analysis pipeline.

        Args:
            dataset_id: ID of the dataset being analyzed.
            df: Cleaned DataFrame from IngestionAgent.
            columns: Column mapping from IngestionAgent.

        Returns:
            Complete analysis results dict with sales, inventory, customer, kpis.
        """
        results: dict = {}

        # Sales analysis
        sales = analyze_sales(df, columns)
        results["sales"] = sales

        # Anomaly detection
        anomalies = detect_anomalies(df, columns)
        results["anomalies"] = anomalies

        # Inventory analysis
        inventory = analyze_inventory(df, columns)
        results["inventory"] = inventory

        # Customer analysis
        customers = analyze_customers(df, columns)
        results["customers"] = customers

        # KPI engine + Business Health Score
        kpis = compute_all_kpis(sales, inventory, customers)
        results["kpis"] = kpis

        self.log_action(
            dataset_id=dataset_id,
            action="ANALYSIS_COMPLETE",
            input_summary=f"DataFrame: {len(df)} rows, columns mapped: {list(columns.keys())}",
            output_summary=(
                f"Revenue: {kpis.get('total_revenue', 0)}, "
                f"Health Score: {kpis.get('business_health_score', 'N/A')}, "
                f"Dead Stock: {kpis.get('dead_stock_count', 0)}, "
                f"Near Expiry: {kpis.get('near_expiry_count', 0)}, "
                f"Anomalies: {len(anomalies)}"
            ),
        )

        # Update dataset status and cache health score
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        dataset.status = "analyzed"
        dataset.business_health_score = kpis.get("business_health_score")

        # Cache full analysis as JSON
        import json
        try:
            dataset.analysis_summary = json.loads(json.dumps(results, default=str))
        except (TypeError, ValueError):
            dataset.analysis_summary = {"error": "Could not serialize results"}

        self.db.commit()

        return results
