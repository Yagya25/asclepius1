# Asclepius — Agents and Skills

## Architecture Overview

Asclepius uses a four-agent sequential pipeline where each agent inherits from `BaseAgent`, which provides automatic audit trail logging. The pipeline enforces a **human checkpoint** between the Insight Agent (which generates recommendations) and the Report Agent (which only processes approved recommendations).

```
Upload → [Ingestion Agent] → [Analysis Agent] → [Insight Agent] → ⏸️ Human Approval → [Report Agent]
```

**Constitutional rule**: All numerical computation is performed by Pandas/SQL deterministically. LLM (Gemini) is used only for converting computed facts into plain-language narrative. This prevents hallucinated numbers.

---

## Custom Agents

### Agent 1: IngestionAgent

**File**: `backend/app/agents/ingestion_agent.py`
**Responsibility**: Parse uploaded files, validate data quality, clean and standardize data, detect business domain.

**Decision Logic**:
1. Detect file format from extension → use `pd.read_excel()` or `pd.read_csv()`
2. Run `ColumnTypeClassifier` skill to detect column semantics
3. Run `EntityResolver` skill to standardize inconsistent product/customer names
4. Apply cleaning: dedup, drop blank rows, standardize column names, coerce numerics
5. Run `DomainDetector` skill to classify dataset as pharma/retail/inventory/generic
6. Log every transformation to audit trail with before/after row counts

**Input**: `dataset_id`, `file_path`
**Output**: Cleaned `pandas.DataFrame`, updated `Dataset` record with status `validated`

**Audit entries produced**: `FILE_LOADED`, `DATA_CLEANED`, `VALIDATION_COMPLETE`

---

### Agent 2: AnalysisAgent

**File**: `backend/app/agents/analysis_agent.py`
**Responsibility**: Compute all business metrics using deterministic Pandas operations.

**Decision Logic**:
1. Query dataset domain from DB
2. Route to appropriate analysis modules based on available columns:
   - If revenue/amount columns exist → run `SalesAnalyzer`
   - If quantity/stock columns exist → run `InventoryAnalyzer`
   - If customer columns exist → run `CustomerAnalyzer`
   - Always run `KPIEngine` to compute Business Health Score
3. Store results in `analysis_results` table, grouped by category
4. Cache Business Health Score on the dataset record

**Input**: `dataset_id`, cleaned `pandas.DataFrame`
**Output**: Dictionary of KPIs and metrics by category

**Rule**: Zero LLM calls. Every number is a Pandas computation.

**Audit entries produced**: `ANALYSIS_COMPLETE`

---

### Agent 3: InsightAgent

**File**: `backend/app/agents/insight_agent.py`
**Responsibility**: Generate actionable recommendations from analysis results. This is the human checkpoint — all recommendations require approval.

**Decision Logic** (15 business rules):
1. Dead stock detected (zero sales > 60 days) → severity `critical`, action `clearance`
2. Near-expiry stock (< 90 days) → severity `critical`, action `discount`
3. High inventory holding → severity `warning`, action `clearance`
4. Sales declining > 30% → severity `warning`, action `review`
5. Sales increasing > 30% → severity `info`, action `increase_purchase`
6. Zero-stock items → severity `critical`, action `reorder`
7. At-risk customers detected → severity `warning`, action `outreach`
8. High customer concentration → severity `warning`, action `diversify`
9. Low inventory turnover → severity `warning`, action `review`
10. ABC shift (product moved down) → severity `info`, action `review`
11. Overstock detected → severity `warning`, action `clearance`
12. Inactive customers detected → severity `info`, action `outreach`
13. Low Business Health Score (< 50) → severity `critical`, action `review`
14. Revenue opportunity (high-growth products) → severity `info`, action `increase_purchase`
15. Profit leakage (expired + dead stock total value) → severity `critical`, action `clearance`

**Key design**: Every recommendation is created with `status = "pending"`. The pipeline stops here until a human acts.

**Input**: `dataset_id`, analysis results dictionary
**Output**: List of `Recommendation` records (all pending)

**Audit entries produced**: `RECOMMENDATIONS_GENERATED` (with `human_checkpoint = true`)

---

### Agent 4: ReportAgent

**File**: `backend/app/agents/report_agent.py`
**Responsibility**: Generate a structured report containing ONLY recommendations that a human has approved.

**Decision Logic**:
1. Query `recommendations` table for `dataset_id` where `status = "approved"`
2. If zero approved → log `REPORT_SKIPPED`, return `None`
3. Build structured report with sections: Executive Summary, KPIs, Approved Actions, Audit Trail
4. Each action includes who approved it and when
5. Mark dataset status as `completed`

**Input**: `dataset_id`
**Output**: Structured report dictionary, or `None` if no approvals exist

**Audit entries produced**: `REPORT_GENERATED` or `REPORT_SKIPPED`

---

## Custom Skills

Skills are reusable components that agents call. They are distinct from agents — an agent orchestrates a workflow, a skill performs a specific computation.

### Skill 1: ABCClassifier

**File**: `backend/app/analysis/inventory.py` → `abc_classification()`
**Used by**: AnalysisAgent
**What it does**: Classifies products into A/B/C categories based on cumulative revenue contribution.
- **A**: Products contributing to the top 80% of revenue
- **B**: Products contributing to the next 15%
- **C**: Products contributing to the bottom 5%
**Input**: DataFrame with product and revenue columns
**Output**: DataFrame with added `abc_class` column

### Skill 2: RFMScorer

**File**: `backend/app/analysis/customer.py` → `rfm_analysis()`
**Used by**: AnalysisAgent
**What it does**: Scores customers on Recency (days since last purchase), Frequency (number of purchases), and Monetary (total spend). Segments customers into: Champions, Loyal, At-Risk, Lost.
**Input**: DataFrame with customer, date, and amount columns
**Output**: DataFrame with `rfm_score`, `recency`, `frequency`, `monetary`, `segment` columns

### Skill 3: BusinessHealthScorer

**File**: `backend/app/analysis/kpi.py` → `compute_business_health_score()`
**Used by**: AnalysisAgent
**What it does**: Computes a composite 0–100 score from three sub-scores:
- Sales Health (40% weight): based on revenue trend, growth rate, concentration
- Inventory Health (35% weight): based on turnover, dead stock %, ABC distribution
- Customer Health (25% weight): based on retention, RFM distribution, churn rate
**Input**: KPI dictionary from all analysis modules
**Output**: `{ score: int, sales_health: int, inventory_health: int, customer_health: int }`

### Skill 4: AnomalyDetector

**File**: `backend/app/analysis/sales.py` → `detect_anomalies()`
**Used by**: AnalysisAgent, InsightAgent
**What it does**: Identifies products with significant sales changes by comparing each product's recent sales against its historical average. Products with >30% deviation (positive or negative) are flagged.
**Input**: DataFrame with product, date, and quantity/revenue columns
**Output**: List of anomalies: `{ product, direction, previous_avg, current, pct_change }`

### Skill 5: ColumnTypeClassifier

**File**: `backend/app/agents/ingestion_agent.py` → `_detect_columns()`
**Used by**: IngestionAgent
**What it does**: Classifies columns by semantic type (date, product_name, quantity, price, customer, batch, expiry) using keyword matching on column names. Handles variations like "Qty", "Quantity", "Units Sold", "No. of Units".
**Input**: List of column names
**Output**: Dictionary mapping semantic types to column names

---

## Human-in-the-Loop (HITL) Design

The HITL checkpoint is not optional decoration — it is a structural requirement of the pipeline. It applies identically across all modules:

**Inventory Module:**
1. **InsightAgent** generates recommendations → all set to `status = "pending"`
2. **Pipeline stops** — no further automated processing occurs
3. **Manager** reviews each recommendation via the Approval Queue UI
4. **Approve**: `POST /recommendations/{id}/approve` → records approver name and timestamp
5. **Reject**: `POST /recommendations/{id}/reject` → records reason
6. **ReportAgent** only runs when explicitly triggered, and only processes `status = "approved"` items
7. If zero items are approved, ReportAgent refuses to generate (returns HTTP 400)

**HR Module:**
1. **ResumeScreeningAgent** generates shortlist recommendations → all set to `status = "pending"`
2. **Pipeline stops** — candidates are not shortlisted until HR manager acts
3. **HR Manager** reviews each shortlist recommendation in the same Approval Queue
4. Same approve/reject endpoints, same audit logging, same `human_checkpoint = true`

Every approval/rejection is logged to the audit trail with `human_checkpoint = true`.

---

## HR Module — Agents and Skills

### Agent 5: ResumeScreeningAgent

**File**: `backend/app/modules/hr/resume_agent.py`
**Responsibility**: Parse uploaded resumes, extract skills, match against a Job Description, score and rank candidates. All shortlist recommendations require HR manager approval.

**Decision Logic**:
1. Load resume CSV (Name, Email, Skills, Experience, Education)
2. Load target Job Description from database
3. For each candidate: extract and normalize skills using `SkillExtractor`
4. Score each candidate using `JDMatcher` (weighted: required 60%, preferred 20%, experience 20%)
5. Rank candidates by fit score, assign tier (Strong ≥70, Moderate 45–69, Weak <45)
6. Save `ResumeScreening` records to database
7. Generate `Recommendation` records: "Shortlist N strong candidates" — all `status="pending"`

**Input**: `dataset_id`, `file_path` (CSV), `jd_id`
**Output**: List of `Recommendation` records (all pending) + `ResumeScreening` records

**Audit entries produced**: `RESUMES_LOADED`, `SKILLS_EXTRACTED`, `CANDIDATES_SCORED`, `SHORTLIST_GENERATED`

---

### Agent 6: OnboardingAgent

**File**: `backend/app/modules/hr/onboarding_agent.py`
**Responsibility**: Auto-generate department-specific onboarding checklists when a new employee is registered.

**Decision Logic**:
1. Load employee record from database
2. Select department-specific template (Sales, Warehouse, Finance, or Default)
3. Generate onboarding tasks with categories: HR, IT, Training, Team
4. Each task has a due date (days from join date)
5. Create `Recommendation` for HR manager to review the generated checklist

**Templates**:
- **Sales**: 12 tasks including product knowledge training, territory mapping, regulatory compliance (FSSAI)
- **Warehouse**: 11 tasks including cold chain handling, batch tracking, safety procedures
- **Finance**: 10 tasks including Tally/ERP access, GST portal setup, financial policy training
- **Default**: 10 tasks covering standard onboarding (HR docs, IT setup, orientation, team intro)

**Input**: `employee_id`
**Output**: List of `OnboardingTask` records

**Audit entries produced**: `EMPLOYEE_REGISTERED`, `ONBOARDING_CHECKLIST_GENERATED`

---

### Skill 6: SkillExtractor

**File**: `backend/app/modules/hr/analysis.py` → `extract_skills()`
**Used by**: ResumeScreeningAgent
**What it does**: Extracts and normalizes skills from a comma-separated skills string using a pharma industry synonym dictionary. Maps variations like "MS Excel" → "excel", "pharmaceutical sales" → "pharma sales", "B.Pharm" → "b.pharm".
**Input**: Raw skills string (e.g., "Python, MS Excel, pharma sales")
**Output**: List of normalized skill strings (e.g., `["python", "excel", "pharma sales"]`)

### Skill 7: JDMatcher

**File**: `backend/app/modules/hr/analysis.py` → `match_jd()`
**Used by**: ResumeScreeningAgent
**What it does**: Scores a candidate's skills against a Job Description using a deterministic weighted formula:
- Required skill match: 60% weight
- Preferred skill match: 20% weight
- Experience match: 20% weight (capped at 2x minimum requirement)
**Input**: Candidate skills, JD required/preferred skills, experience
**Output**: `{ fit_score: 0-100, tier: "Strong"|"Moderate"|"Weak", required_matched, required_missing }`

---

## Audit Trail

Every agent action is logged to the `audit_log` table via `BaseAgent.log_action()`:

```python
class BaseAgent:
    def log_action(self, dataset_id, action, input_summary, output_summary, human_checkpoint=False):
        # Creates an AuditLog record with agent_name, action, summaries, timestamp
        # This is called automatically by every agent at every step
```

The audit trail provides full traceability: for any recommendation, a judge can query the audit log by `dataset_id` and see the complete chain from file upload to final approval. This works identically across Inventory and HR modules.

See `docs/AUDIT_TRAIL.md` for the detailed audit trail design.

