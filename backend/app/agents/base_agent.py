"""Base agent class with audit logging."""
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import AuditLog


class BaseAgent:
    """Every agent inherits this. All actions are logged automatically."""

    def __init__(self, name: str, db: Session):
        self.name = name
        self.db = db

    def log_action(self, dataset_id: int, action: str, input_summary: str,
                   output_summary: str, human_checkpoint: bool = False):
        """Log every step to the audit trail."""
        log = AuditLog(
            dataset_id=dataset_id,
            agent_name=self.name,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            human_checkpoint=human_checkpoint,
            timestamp=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()
        return log

    def run(self, dataset_id: int, **kwargs):
        """Override this in each agent."""
        raise NotImplementedError("Each agent must implement run()")
