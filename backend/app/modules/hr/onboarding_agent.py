"""Onboarding Agent: auto-generate department-specific onboarding checklists.

When HR registers a new employee, this agent creates a structured checklist
with tasks, due dates, and categories. Same HITL pattern: tasks require approval.
"""
from datetime import datetime

from ...agents.base_agent import BaseAgent
from ...models import Employee, OnboardingTask, Recommendation

# Department-specific onboarding templates
ONBOARDING_TEMPLATES: dict[str, list[dict]] = {
    "default": [
        {"category": "HR", "title": "Submit ID proof and address verification", "due_days": 1},
        {"category": "HR", "title": "Sign employment agreement and NDA", "due_days": 1},
        {"category": "HR", "title": "Complete PF and tax declaration forms", "due_days": 3},
        {"category": "IT", "title": "Set up company email account", "due_days": 1},
        {"category": "IT", "title": "Provision laptop/workstation and software access", "due_days": 2},
        {"category": "IT", "title": "Grant ERP system access with appropriate role", "due_days": 3},
        {"category": "Training", "title": "Complete company orientation module", "due_days": 5},
        {"category": "Training", "title": "Read and acknowledge company handbook", "due_days": 5},
        {"category": "Team", "title": "Introduction meeting with team members", "due_days": 3},
        {"category": "Team", "title": "Meet reporting manager for role walkthrough", "due_days": 2},
    ],
    "sales": [
        {"category": "HR", "title": "Submit ID proof and address verification", "due_days": 1},
        {"category": "HR", "title": "Sign employment agreement and NDA", "due_days": 1},
        {"category": "HR", "title": "Complete PF and tax declaration forms", "due_days": 3},
        {"category": "IT", "title": "Set up company email account", "due_days": 1},
        {"category": "IT", "title": "Provision mobile device with CRM access", "due_days": 2},
        {"category": "IT", "title": "Grant ERP and inventory system access", "due_days": 3},
        {"category": "Training", "title": "Complete company orientation module", "due_days": 5},
        {"category": "Training", "title": "Product knowledge training — pharma catalog", "due_days": 7},
        {"category": "Training", "title": "Sales process and territory mapping training", "due_days": 7},
        {"category": "Training", "title": "Regulatory compliance training (drug schedules, FSSAI)", "due_days": 10},
        {"category": "Team", "title": "Shadow senior sales rep for 2 field visits", "due_days": 14},
        {"category": "Team", "title": "Meet reporting manager for target setting", "due_days": 3},
    ],
    "warehouse": [
        {"category": "HR", "title": "Submit ID proof and address verification", "due_days": 1},
        {"category": "HR", "title": "Sign employment agreement and NDA", "due_days": 1},
        {"category": "HR", "title": "Complete PF and tax declaration forms", "due_days": 3},
        {"category": "IT", "title": "Set up attendance biometric access", "due_days": 1},
        {"category": "IT", "title": "Grant warehouse management system (WMS) access", "due_days": 2},
        {"category": "Training", "title": "Complete company orientation module", "due_days": 5},
        {"category": "Training", "title": "Cold chain handling and storage protocol training", "due_days": 7},
        {"category": "Training", "title": "Batch tracking and expiry management training", "due_days": 7},
        {"category": "Training", "title": "Safety and emergency procedure training", "due_days": 5},
        {"category": "Team", "title": "Warehouse tour and area assignment", "due_days": 2},
        {"category": "Team", "title": "Meet warehouse supervisor for shift briefing", "due_days": 2},
    ],
    "finance": [
        {"category": "HR", "title": "Submit ID proof and address verification", "due_days": 1},
        {"category": "HR", "title": "Sign employment agreement and NDA", "due_days": 1},
        {"category": "HR", "title": "Complete PF and tax declaration forms", "due_days": 3},
        {"category": "IT", "title": "Set up company email account", "due_days": 1},
        {"category": "IT", "title": "Grant Tally/ERP access with finance role", "due_days": 2},
        {"category": "IT", "title": "Set up GST portal credentials", "due_days": 3},
        {"category": "Training", "title": "Complete company orientation module", "due_days": 5},
        {"category": "Training", "title": "Company financial policies and approval workflow training", "due_days": 7},
        {"category": "Training", "title": "GST compliance and filing procedure training", "due_days": 10},
        {"category": "Team", "title": "Meet reporting manager for process walkthrough", "due_days": 2},
    ],
}


class OnboardingAgent(BaseAgent):
    """Agent 6: Register Employee → Generate Checklist → Track Completion."""

    def __init__(self, db):
        super().__init__("HR_ONBOARDING", db)

    def run(self, employee_id: int) -> list[OnboardingTask]:
        """Generate onboarding checklist for a new employee.

        Args:
            employee_id: ID of the registered employee.

        Returns:
            List of created OnboardingTask records.
        """
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        # Select template based on department
        dept = (employee.department or "").lower().strip()
        if "sales" in dept or "marketing" in dept:
            template_key = "sales"
        elif "warehouse" in dept or "logistics" in dept or "supply" in dept:
            template_key = "warehouse"
        elif "finance" in dept or "accounts" in dept:
            template_key = "finance"
        else:
            template_key = "default"

        template = ONBOARDING_TEMPLATES[template_key]

        self.log_action(
            dataset_id=None,
            action="EMPLOYEE_REGISTERED",
            input_summary=f"Employee: {employee.name}, Dept: {employee.department}, Role: {employee.role}",
            output_summary=f"Using '{template_key}' onboarding template ({len(template)} tasks)",
        )

        # Create onboarding tasks
        tasks: list[OnboardingTask] = []
        employee.join_date or datetime.utcnow()

        for item in template:
            task = OnboardingTask(
                employee_id=employee_id,
                category=item["category"],
                title=item["title"],
                description=f"Onboarding task for {employee.name} — {employee.department}",
                due_days=item["due_days"],
            )
            self.db.add(task)
            tasks.append(task)

        # Update employee status
        employee.onboarding_status = "in_progress"
        employee.onboarding_progress = 0

        # Generate recommendation for HR to review the checklist
        rec = Recommendation(
            dataset_id=None,
            module="hr",
            agent_name="HR_ONBOARDING",
            title=f"Onboarding checklist generated for {employee.name}",
            description=(
                f"Department: {employee.department}, Role: {employee.role}. "
                f"{len(tasks)} tasks created across categories: "
                f"HR ({sum(1 for t in tasks if t.category == 'HR')}), "
                f"IT ({sum(1 for t in tasks if t.category == 'IT')}), "
                f"Training ({sum(1 for t in tasks if t.category == 'Training')}), "
                f"Team ({sum(1 for t in tasks if t.category == 'Team')})."
            ),
            action_type="onboarding",
            severity="info",
            estimated_impact=f"{len(tasks)} onboarding tasks auto-generated",
            status="pending",
        )
        self.db.add(rec)

        self.db.commit()

        self.log_action(
            dataset_id=None,
            action="ONBOARDING_CHECKLIST_GENERATED",
            input_summary=f"Employee: {employee.name} ({template_key} template)",
            output_summary=f"{len(tasks)} tasks created. Pending HR manager review.",
            human_checkpoint=True,
        )

        return tasks
