# Audit Trail Design — Asclepius

## Purpose

The audit trail is the backbone of Asclepius's Track A compliance. The hackathon requirement states: *"Every automated step is traceable and auditable. A judge should be able to follow how a decision was made, see where a human approved it, and trust that nothing happened silently."*

This document describes what gets logged, when, and how to trace any recommendation back to its source.

## What Gets Logged

Every agent action produces an `audit_log` entry with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `agent_name` | string | Which agent performed the action: `INGESTION`, `ANALYSIS`, `INSIGHT`, `REPORT`, or `HUMAN_APPROVAL` |
| `action` | string | What happened: `FILE_LOADED`, `DATA_CLEANED`, `ANALYSIS_COMPLETE`, `RECOMMENDATIONS_GENERATED`, `APPROVED_RECOMMENDATION`, `REJECTED_RECOMMENDATION`, `REPORT_GENERATED`, `REPORT_SKIPPED` |
| `input_summary` | text | What went into the step (e.g., "File: sales.xlsx, Original rows: 500") |
| `output_summary` | text | What came out (e.g., "Duplicates removed: 5, Final rows: 495") |
| `human_checkpoint` | boolean | `true` when this step required or recorded human approval |
| `approved_by` | string | Name of the human who approved (null for automated steps) |
| `timestamp` | datetime | When the action occurred |

## When Logging Happens

### Ingestion Agent
1. **FILE_LOADED** — immediately after parsing the uploaded file. Records filename, original row count, column count.
2. **DATA_CLEANED** — after cleaning. Records duplicates removed, blank rows dropped, final row count.
3. **VALIDATION_COMPLETE** — after domain detection. Records detected domain and final status.

### Analysis Agent
4. **ANALYSIS_COMPLETE** — after computing all KPIs. Records the list of metrics computed and the dataset domain.

### Insight Agent
5. **RECOMMENDATIONS_GENERATED** — after generating recommendations. Records count of recommendations and sets `human_checkpoint = true` because the pipeline pauses here for human review.

### Human Approval (not an agent — recorded by the API layer)
6. **APPROVED_RECOMMENDATION** — when a manager clicks Approve. Records the recommendation title, approver name. `human_checkpoint = true`.
7. **REJECTED_RECOMMENDATION** — when a manager clicks Reject. Records the recommendation title, approver name, rejection reason. `human_checkpoint = true`.

### Report Agent
8. **REPORT_GENERATED** — after building the report from approved recommendations. Records count of approved actions included.
9. **REPORT_SKIPPED** — if no approved recommendations exist when report generation is attempted.

### HR Resume Screening Agent
10. **RESUMES_LOADED** — after parsing the uploaded resumes CSV. Records filename and resume count.
11. **SKILLS_EXTRACTED** — after extracting and normalizing skills from all resumes.
12. **CANDIDATES_SCORED** — after scoring and ranking candidates against the JD. Records Strong/Moderate/Weak counts.
13. **SHORTLIST_GENERATED** — after generating shortlist recommendations. `human_checkpoint = true` because HR manager must approve.

### HR Onboarding Agent
14. **EMPLOYEE_REGISTERED** — after loading the employee record. Records employee name, department, template selected.
15. **ONBOARDING_CHECKLIST_GENERATED** — after creating all onboarding tasks. `human_checkpoint = true`.

## Example Timeline

A complete pipeline run produces this audit trail:

### Inventory Module
```
10:05:12  INGESTION       FILE_LOADED                  File: Q2_Sales.xlsx, 520 rows, 11 columns
10:05:13  INGESTION       DATA_CLEANED                 Duplicates: 5, Blanks: 3, Final: 512 rows
10:05:13  INGESTION       VALIDATION_COMPLETE          Domain: pharma, Status: validated
10:05:15  ANALYSIS        ANALYSIS_COMPLETE            KPIs: [revenue, growth, abc, dead_stock, rfm, health_score]
10:05:16  INSIGHT         RECOMMENDATIONS_GENERATED    8 recommendations, ALL pending (human_checkpoint=true)
          ─── PIPELINE PAUSED: Waiting for human approval ───
10:15:02  HUMAN_APPROVAL  APPROVED_RECOMMENDATION      "17 batches expire within 90 days" → Approved by Manager Utkarsh
10:15:45  HUMAN_APPROVAL  APPROVED_RECOMMENDATION      "Product X: zero sales in 83 days" → Approved by Manager Utkarsh
10:16:01  HUMAN_APPROVAL  REJECTED_RECOMMENDATION      "Increase purchase of Paracetamol" → Rejected (reason: "Already ordered last week")
10:18:00  REPORT          REPORT_GENERATED             2 approved actions included in report
```

### HR Module
```
11:00:01  HR_RESUME_SCREENING   RESUMES_LOADED              File: resumes.csv, 50 candidates
11:00:02  HR_RESUME_SCREENING   SKILLS_EXTRACTED             50 candidates processed
11:00:02  HR_RESUME_SCREENING   CANDIDATES_SCORED            Strong: 8, Moderate: 22, Weak: 20
11:00:03  HR_RESUME_SCREENING   SHORTLIST_GENERATED          4 recommendations, ALL pending (human_checkpoint=true)
          ─── PIPELINE PAUSED: Waiting for HR manager approval ───
11:10:00  HUMAN_APPROVAL        APPROVED_RECOMMENDATION      "Shortlist 8 strong candidates" → Approved by HR Manager
11:12:00  HR_ONBOARDING         EMPLOYEE_REGISTERED          Employee: Priya Sharma, Dept: Sales
11:12:01  HR_ONBOARDING         ONBOARDING_CHECKLIST_GENERATED  12 tasks created (human_checkpoint=true)
```

## Traceability: From Recommendation to Source Data

To trace any recommendation back to its origin:

1. **Find the recommendation** in the `recommendations` table → note its `dataset_id` and `created_at`
2. **Query the audit log** for that `dataset_id`, ordered by timestamp
3. **Follow the chain**: `FILE_LOADED` → `DATA_CLEANED` → `ANALYSIS_COMPLETE` → `RECOMMENDATIONS_GENERATED` → `APPROVED_RECOMMENDATION`
4. Each entry shows exactly what data went in and what came out at each step
5. The `module` field on each audit entry identifies which business module produced it

## Design Rules

1. **Append-only**: The audit log table never has rows updated or deleted. No API endpoint exists for modification.
2. **No silent operations**: If an agent does something, it logs it. If no log entry exists, the action did not happen.
3. **Human checkpoints are explicit**: The `human_checkpoint` boolean makes it trivially easy to filter for human decisions vs. automated steps.
4. **Cross-module**: The same audit log table captures entries from all modules (inventory, HR, future finance). The `module` field enables per-module filtering.
5. **Timestamps are UTC**: All timestamps use `datetime.utcnow()` for consistency.

