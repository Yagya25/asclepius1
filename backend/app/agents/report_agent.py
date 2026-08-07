"""Report Agent: generates reports ONLY from approved recommendations."""
from datetime import datetime

from ..models import AuditLog, Dataset, Recommendation
from .base_agent import BaseAgent


class ReportAgent(BaseAgent):
    """Agent 4: Generate structured report after human approval.
    Refuses to run if zero recommendations are approved.
    """

    def __init__(self, db):
        super().__init__("REPORT", db)

    def run(self, dataset_id: int) -> dict | None:
        """Generate report from approved recommendations only.

        Returns structured report dict, or None if nothing approved.
        """
        approved = (
            self.db.query(Recommendation)
            .filter(Recommendation.dataset_id == dataset_id,
                    Recommendation.status == "approved")
            .all()
        )

        if not approved:
            self.log_action(
                dataset_id=dataset_id,
                action="REPORT_SKIPPED",
                input_summary=f"Dataset {dataset_id}",
                output_summary="No approved recommendations. Report not generated.",
            )
            return None

        # Get dataset info
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()

        # Get audit trail for this dataset
        audit_entries = (
            self.db.query(AuditLog)
            .filter(AuditLog.dataset_id == dataset_id)
            .order_by(AuditLog.timestamp.asc())
            .all()
        )

        # Build structured report
        report = {
            "title": "Asclepius — Operations Report",
            "generated_at": datetime.utcnow().isoformat(),
            "dataset": {
                "id": dataset.id,
                "filename": dataset.filename,
                "domain": dataset.detected_domain,
                "rows_processed": dataset.row_count,
                "business_health_score": dataset.business_health_score,
            },
            "summary": {
                "total_recommendations": len(approved),
                "critical": sum(1 for r in approved if r.severity == "critical"),
                "warning": sum(1 for r in approved if r.severity == "warning"),
                "info": sum(1 for r in approved if r.severity == "info"),
            },
            "approved_actions": [
                {
                    "title": r.title,
                    "description": r.description,
                    "action_type": r.action_type,
                    "severity": r.severity,
                    "estimated_impact": r.estimated_impact,
                    "approved_by": r.approved_by,
                    "approved_at": r.approved_at.isoformat() if r.approved_at else None,
                }
                for r in approved
            ],
            "audit_trail": [
                {
                    "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                    "agent": entry.agent_name,
                    "action": entry.action,
                    "details": entry.output_summary,
                    "human_checkpoint": entry.human_checkpoint,
                    "approved_by": entry.approved_by,
                }
                for entry in audit_entries
            ],
        }

        self.log_action(
            dataset_id=dataset_id,
            action="REPORT_GENERATED",
            input_summary=f"Approved recommendations: {len(approved)}",
            output_summary=f"Report generated with {len(approved)} approved actions",
        )

        dataset.status = "completed"
        self.db.commit()

        return report
