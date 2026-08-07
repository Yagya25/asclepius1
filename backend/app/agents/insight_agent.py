"""Insight Agent: generates pharma-specific recommendations with HUMAN CHECKPOINT.

All recommendations are created with status='pending'.
The pipeline STOPS here until a manager approves.
"""
from ..models import Recommendation
from .base_agent import BaseAgent


class InsightAgent(BaseAgent):
    """Agent 3: Apply business rules to analysis results → actionable recommendations."""

    def __init__(self, db):
        super().__init__("INSIGHT", db)

    def run(self, dataset_id: int, analysis: dict) -> list[Recommendation]:
        """Generate recommendations from analysis results. ALL pending approval."""
        recs: list[Recommendation] = []
        analysis.get("sales", {})
        inventory = analysis.get("inventory", {})
        customers = analysis.get("customers", {})
        kpis = analysis.get("kpis", {})
        anomalies = analysis.get("anomalies", [])

        # --- Rule 1: Near-expiry batches (pharma-critical) ---
        near_exp = inventory.get("near_expiry", {})
        ne_count = near_exp.get("near_expiry_count", 0)
        if ne_count > 0:
            items = near_exp.get("items", [])
            near_items = [i for i in items if i.get("status") == "near_expiry"][:5]
            names = ", ".join(i["product"] for i in near_items)
            recs.append(self._create_rec(
                dataset_id, f"{ne_count} batches expiring within 90 days",
                f"Products at risk: {names}. Consider push sales or discounts to move stock before expiry.",
                "discount", "critical",
                f"Prevent loss on {ne_count} near-expiry batches"))

        # --- Rule 2: Already expired stock ---
        exp_count = near_exp.get("expired_count", 0)
        if exp_count > 0:
            expired_items = [i for i in near_exp.get("items", []) if i.get("status") == "expired"][:5]
            names = ", ".join(i["product"] for i in expired_items)
            recs.append(self._create_rec(
                dataset_id, f"{exp_count} batches already expired",
                f"Expired products: {names}. Initiate return to manufacturer or write off immediately.",
                "write_off", "critical", f"{exp_count} expired batches requiring action"))

        # --- Rule 3: Dead stock ---
        dead = inventory.get("dead_stock", {})
        dead_count = dead.get("count", 0)
        if dead_count > 0:
            dead_val = dead.get("total_value_at_risk", 0)
            items = dead.get("items", [])[:3]
            names = ", ".join(f"{i['product']} ({i['days_since_last_sale']}d)" for i in items)
            recs.append(self._create_rec(
                dataset_id, f"{dead_count} products are dead stock (no sales in 60+ days)",
                f"Top offenders: {names}. Historical value: ₹{dead_val:,.0f}. "
                f"Consider clearance pricing, bundling, or returning to supplier.",
                "clearance", "critical", f"₹{dead_val:,.0f} tied up in dead stock"))

        # --- Rule 4: Sales declining products ---
        declining = [a for a in anomalies if a.get("direction") == "declining"]
        if declining:
            top = declining[0]
            recs.append(self._create_rec(
                dataset_id,
                f"{top['product']} sales declined {abs(top['pct_change'])}%",
                f"Revenue dropped from ₹{top['previous_avg']:,.0f} to ₹{top['current']:,.0f}. "
                f"Investigate cause — demand shift, competitor, or seasonal pattern. Reduce purchase accordingly.",
                "review", "warning",
                f"{len(declining)} products with declining sales"))

        # --- Rule 5: Sales increasing (opportunity) ---
        increasing = [a for a in anomalies if a.get("direction") == "increasing"]
        if increasing:
            top = increasing[0]
            recs.append(self._create_rec(
                dataset_id,
                f"Opportunity: {top['product']} demand up {top['pct_change']}%",
                f"Revenue grew from ₹{top['previous_avg']:,.0f} to ₹{top['current']:,.0f}. "
                f"Increase purchase by 15-20% to avoid stockouts and capture demand.",
                "increase_purchase", "info",
                f"{len(increasing)} products with growing demand"))

        # --- Rule 6: High customer concentration risk ---
        conc = customers.get("concentration_risk", {})
        if conc.get("risk_level") == "high":
            recs.append(self._create_rec(
                dataset_id,
                f"Customer concentration risk: top customer is {conc['top_customer_pct']}% of revenue",
                f"Top 3 customers account for {conc['top_3_pct']}% of revenue. "
                f"Losing one major customer would severely impact business. Diversify customer base.",
                "diversify", "warning",
                "Revenue depends heavily on few customers"))

        # --- Rule 7: Inactive customers (churn risk) ---
        inactive = customers.get("inactive_customers", {})
        inactive_count = inactive.get("count", 0)
        if inactive_count > 0:
            items = inactive.get("items", [])[:3]
            names = ", ".join(i["customer"] for i in items)
            recs.append(self._create_rec(
                dataset_id,
                f"{inactive_count} customers inactive for 60+ days",
                f"Inactive customers: {names}. Reach out to understand why they stopped purchasing.",
                "outreach", "warning",
                f"{inactive_count} customers at risk of churning"))

        # --- Rule 8: At-risk customers from RFM ---
        rfm = customers.get("rfm", {})
        at_risk = rfm.get("segments", {}).get("At-Risk", 0)
        lost = rfm.get("segments", {}).get("Lost", 0)
        if at_risk + lost > 0:
            recs.append(self._create_rec(
                dataset_id,
                f"{at_risk + lost} customers classified as At-Risk or Lost",
                f"At-Risk: {at_risk}, Lost: {lost}. "
                f"These customers had significant past business but activity has dropped. "
                f"Priority outreach recommended for At-Risk segment before they become Lost.",
                "outreach", "warning" if at_risk > lost else "info",
                f"Potential revenue recovery from {at_risk} at-risk customers"))

        # --- Rule 9: Low inventory turnover ---
        turnover = kpis.get("inventory_turnover", 0)
        if turnover < 3 and turnover > 0:
            recs.append(self._create_rec(
                dataset_id,
                f"Low inventory turnover ratio: {turnover:.1f}x",
                "Stock is moving slowly. Healthy pharma distribution targets 4-6x turnover. "
                "Review slow movers and consider quantity discounts to increase movement.",
                "review", "warning", "Low stock movement efficiency"))

        # --- Rule 10: Slow movers ---
        slow = inventory.get("slow_movers", [])
        if len(slow) >= 3:
            names = ", ".join(s["product"] for s in slow[:3])
            recs.append(self._create_rec(
                dataset_id,
                f"{len(slow)} slow-moving products identified",
                f"Slowest movers: {names}. "
                f"Consider reducing purchase quantities or offering combination deals.",
                "review", "info", f"{len(slow)} products with low velocity"))

        # --- Rule 11: Profit leakage ---
        leakage = inventory.get("profit_leakage", {})
        total_leak = leakage.get("total_leakage", 0)
        monthly = leakage.get("monthly_estimate", 0)
        if monthly > 0:
            recs.append(self._create_rec(
                dataset_id,
                f"Profit leakage detected: ₹{monthly:,.0f}/month estimated",
                f"Total leakage from expired stock, dead stock, and slow movers: ₹{total_leak:,.0f}. "
                f"Address expiry and dead stock items to reduce monthly losses.",
                "review", "critical" if monthly > 50000 else "warning",
                f"Potential monthly savings: ₹{monthly:,.0f}"))

        # --- Rule 12: Low Business Health Score ---
        health = kpis.get("business_health_score", 100)
        if health < 50:
            breakdown = kpis.get("health_breakdown", {})
            recs.append(self._create_rec(
                dataset_id,
                f"Business Health Score is {health}/100 — needs attention",
                f"Sales Health: {breakdown.get('sales_health', 'N/A')}/100, "
                f"Inventory Health: {breakdown.get('inventory_health', 'N/A')}/100, "
                f"Customer Health: {breakdown.get('customer_health', 'N/A')}/100. "
                f"Focus on the lowest-scoring area first.",
                "review", "critical",
                f"Overall health at {health}/100"))

        # --- Rule 13: ABC shift - too many C products ---
        abc = inventory.get("abc_classification", {})
        summary = abc.get("summary", {})
        c_count = summary.get("c_count", 0)
        total_products = summary.get("a_count", 0) + summary.get("b_count", 0) + c_count
        if total_products > 0 and c_count / total_products > 0.5:
            recs.append(self._create_rec(
                dataset_id,
                f"{c_count} of {total_products} products are C-class (bottom 5% revenue)",
                "Over half your product line contributes minimal revenue. "
                "Review whether these medicines are worth stocking.",
                "review", "info", f"{c_count} low-revenue products"))

        # Commit all recommendations
        self.db.commit()

        self.log_action(
            dataset_id=dataset_id,
            action="RECOMMENDATIONS_GENERATED",
            input_summary=f"Analysis with {len(anomalies)} anomalies, health={health}",
            output_summary=f"Generated {len(recs)} recommendations. ALL pending human approval.",
            human_checkpoint=True,
        )

        return recs

    def _create_rec(self, dataset_id: int, title: str, description: str,
                    action_type: str, severity: str, impact: str) -> Recommendation:
        """Create a recommendation record with status=pending."""
        rec = Recommendation(
            dataset_id=dataset_id,
            agent_name="INSIGHT",
            title=title,
            description=description,
            action_type=action_type,
            severity=severity,
            estimated_impact=impact,
            status="pending",
        )
        self.db.add(rec)
        return rec
