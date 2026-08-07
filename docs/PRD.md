# Product Requirements Document — Asclepius

## 1. Platform Vision

Asclepius is an **AI Business Operating System** — a modular platform that automates repetitive business workflows across departments. Each module follows the same agent-driven pattern: AI performs analysis, generates recommendations, and waits for human approval before any action is taken.

The platform currently includes two active modules (Inventory & Sales, HR Automation) with Finance and Operations planned. All modules share the same approval center, audit trail, and reporting infrastructure.

## 2. Problem Statement

Pharmaceutical distributors and small-to-medium businesses rely on monthly ERP Excel exports to make operational decisions. Today, employees manually download these files, filter rows, build pivot tables, identify near-expiry stock, calculate dead inventory, prepare sales reports, and email them to managers. At a typical pharma distributor, this process takes **4–6 hours per cycle**, is performed by a single trained employee (creating a bus-factor-of-one risk), and routinely produces errors — missed expiry batches, incorrect revenue totals, overlooked declining customers.

The core issue is not that the data is unavailable. It is that **extracting decisions from the data requires repetitive, multi-step manual work** that no one in a 15-person distribution company has time to do properly.

This problem was observed directly during an internship at a pharmaceutical distribution company, where the operations team spent a full working day each month on exactly this workflow.

## 3. Target Users

| User | Role | Key Need |
|------|------|----------|
| **Business Owner** | Makes final decisions on purchasing, pricing, clearance | Needs a single view of business health and a prioritized action list — not 30 charts |
| **Inventory Manager** | Manages stock levels, reordering, expiry tracking | Needs dead stock alerts, near-expiry warnings, and reorder suggestions with specific product names and quantities |
| **Operations Manager** | Oversees daily workflow, approves actions | Needs an approval queue where AI recommendations wait for human sign-off before anything happens |
| **HR Manager** | Handles hiring, onboarding, workforce management | Needs AI-assisted resume screening and automated onboarding checklists — not manual shortlisting |

All four users share one trait: **they are not data analysts.** They understand their business but do not write SQL, build pivot tables, or interpret statistical charts without labels. Every output must be in plain language.

## 4. Product Vision

Asclepius is an **AI Operations Manager**, not a dashboard. The difference:

- A dashboard shows you data. Asclepius **tells you what to do about it**.
- A dashboard requires you to interpret charts. Asclepius **generates plain-language recommendations** ("Reduce Crocin purchase by 30% — sales dropped 42% since April").
- A dashboard lets anyone act on anything. Asclepius **requires human approval** before any recommendation is considered final.
- A dashboard has no memory. Asclepius **logs every automated step** so a manager can trace exactly how a recommendation was produced.

## 5. Scope — What We Will Build (MVP)

### 4.1 Data Ingestion and Validation
- Multi-format upload (Excel `.xlsx`, CSV `.csv`)
- Automatic column-type detection (date, quantity, price, product, customer)
- Automatic business-domain detection (pharma, retail, inventory, generic)
- Data cleaning: duplicate removal, blank row dropping, column name standardization, numeric coercion
- Entity resolution: fuzzy-match inconsistent product names ("Crocin" = "CROCIN-500" = "crocin 500mg")
- Audit logging of every transformation with before/after counts

### 4.2 Business Analysis (All Deterministic — No LLM Computation)
- **Sales analysis**: revenue by product/customer/month, top/bottom performers, MoM growth rate, average order value, sales velocity, Pareto analysis (revenue concentration)
- **Inventory analysis**: ABC classification, dead stock detection (no sales in 60+ days), near-expiry detection (< 90 days), slow/fast movers by velocity, inventory turnover ratio, overstock/understock flags
- **Customer analysis**: RFM segmentation (Recency, Frequency, Monetary), customer segments (Champions, Loyal, At-Risk, Lost), inactive customer detection, customer concentration risk
- **KPI engine**: Business Health Score (composite 0–100 with sub-scores), revenue, growth %, inventory turnover, customer retention rate, expiry risk index

### 4.3 AI Recommendations with Human-in-the-Loop
- Rule-based recommendation generation triggered by analysis findings
- Each recommendation includes: title, description, affected products/customers, severity (critical/warning/info), estimated ₹ impact, suggested action type
- **All recommendations created with status `pending`** — nothing executes without human approval
- Manager can Approve, Reject (with reason), or Modify each recommendation
- Report generation is blocked until at least one recommendation is approved

### 4.4 Audit Trail
- Every agent action logged: agent name, action, input summary, output summary, timestamp
- Human approval checkpoints visually distinct in the timeline
- Full traceability: any recommendation can be traced back through the insight that produced it, the analysis that found it, and the data that was uploaded

### 4.5 Report Generation
- Structured report containing only approved recommendations
- Includes KPIs, Business Health Score, priority queue, and audit trail excerpt
- Each action in the report shows who approved it and when

### 5.6 HR Automation Module
- **Resume Screening**: Upload CSV of candidate resumes, AI extracts skills, matches against Job Description, scores and ranks candidates. All shortlist recommendations require HR manager approval.
- **Employee Onboarding**: Register a new employee, AI auto-generates department-specific onboarding checklist (IT setup, HR docs, training, team introductions). Task completion is tracked with progress percentage.
- **Same agent pattern**: HR agents inherit from `BaseAgent`, use the same audit trail, same approval flow, same `Recommendation` model as Inventory. This proves the architecture is genuinely modular.

## 6. Out of Scope — What We Will Not Build, and Why

| Excluded Feature | Reason |
|-----------------|--------|
| **Multi-tenant authentication / user accounts** | MVP targets a single-company deployment. Adding auth increases complexity without validating the core value proposition (automated analysis + HITL approval). Will add in v2 if the core workflow proves useful. |
| **Direct ERP/Tally/Zoho integration** | ERP APIs vary wildly across vendors (Tally, Zoho, SAP B1). Excel export is the universal common denominator — every ERP can produce one. Building direct integrations before proving the analysis pipeline works is premature optimization. |
| **Real-time streaming data** | Pharma distributors operate on monthly/weekly cycles, not real-time. Batch upload matches their actual workflow. Real-time adds infrastructure cost (message queues, WebSockets) with no user benefit. |
| **Demand forecasting with ML models** | Requires minimum 12 months of historical data to produce reliable forecasts. Most SME Excel exports cover 3–6 months. Shipping a forecasting feature that produces unreliable results is worse than not shipping it. Will add when we can validate accuracy. |
| **Mobile application** | Target users operate from desktop during work hours. Mobile adds a second frontend to maintain. Browser-responsive design covers the occasional mobile check. |
| **Automated email notifications** | Requires SMTP configuration and adds a failure mode (email delivery). The approval queue in the UI serves the same purpose — the manager sees pending items when they open the app. |
| **Multi-currency support** | All target users operate in INR. Supporting multi-currency requires exchange rate handling, display formatting, and aggregation logic changes. Not worth the complexity for a single-country MVP. |
| **PDF/DOCX resume parsing** | Structured CSV upload is more reliable for the hackathon demo. PDF parsing adds impressive factor but also fragility — different resume formats break parsers. Will add in v2 with pdfplumber/docx2txt. |
| **Attendance & leave analysis** | Listed as a planned HR sub-module. Requires time-series attendance data that SMEs rarely export in Excel. Will implement when we validate the resume screening workflow. |
| **Finance module** | Listed as planned. Invoice processing and GST reconciliation require domain expertise in Indian tax law. The architecture supports it — the module slot exists — but implementation is deferred. |

## 7. User Stories

Each story has a unique ID for traceability. These IDs appear in the task breakdown (`TASKS.md`) and in commit messages.

---

### US-01: Upload Business Data

**As a** business owner, **I want to** upload my monthly ERP Excel files, **so that** the system can analyze my business data without me doing manual filtering.

**Acceptance Criteria:**
- [ ] The upload endpoint accepts `.xlsx` and `.csv` files
- [ ] Files larger than 50MB are rejected with error message "File too large. Maximum size is 50MB."
- [ ] Non-spreadsheet files (e.g., `.pdf`, `.jpg`) are rejected with error message "Unsupported file format. Upload .xlsx or .csv files."
- [ ] After upload, the API response includes: `dataset_id`, `filename`, `row_count`, and `detected_domain`
- [ ] The upload event is recorded in the audit trail with agent name "INGESTION"

---

### US-02: Automatic Data Cleaning

**As a** business owner, **I want** the system to automatically detect and fix data quality issues, **so that** my analysis is based on clean, reliable data.

**Acceptance Criteria:**
- [ ] Exact duplicate rows are detected and removed
- [ ] Rows where all values are missing are dropped
- [ ] Column names are standardized to lowercase with underscores (e.g., "Product Name" → "product_name")
- [ ] Leading/trailing whitespace is stripped from all string columns
- [ ] The cleaning summary is returned: number of duplicates removed, number of blank rows dropped, final row count
- [ ] Every cleaning step is logged in the audit trail with before/after counts

---

### US-03: Business Health Score

**As a** business owner, **I want to** see my overall business health as a single score from 0 to 100, **so that** I can immediately understand whether things are going well or need attention.

**Acceptance Criteria:**
- [ ] The Business Health Score is a number between 0 and 100
- [ ] Sub-scores are provided: `sales_health`, `inventory_health`, `customer_health`
- [ ] Each sub-score is a number between 0 and 100
- [ ] The composite score is a weighted average of sub-scores (Sales 40%, Inventory 35%, Customer 25%)
- [ ] The score and sub-scores are included in the `/datasets/{id}/kpis` API response

---

### US-04: Dead Stock and Expiry Detection

**As an** inventory manager, **I want** dead stock and near-expiry items identified automatically, **so that** I can take action before stock becomes a financial loss.

**Acceptance Criteria:**
- [ ] Products with zero sales in the last 60 days are flagged as "dead stock"
- [ ] Products expiring within 90 days are flagged as "near-expiry" (only when expiry data is present in the uploaded file)
- [ ] The total ₹ value of dead stock (quantity × unit price) is calculated
- [ ] Each flagged item shows: product name, days since last sale or days to expiry, and ₹ value at risk
- [ ] If the uploaded data does not contain expiry date columns, expiry detection is skipped without error

---

### US-05: AI-Generated Recommendations

**As a** business owner, **I want** the system to tell me what actions to take in plain language, **so that** I don't need to be a data analyst to make decisions.

**Acceptance Criteria:**
- [ ] Recommendations are generated in plain language (e.g., "Consider clearance pricing on Product X — no sales in 83 days, ₹45,000 tied up")
- [ ] Each recommendation includes: `title`, `description`, `severity`, `action_type`, `estimated_impact`
- [ ] Severity is one of: `critical`, `warning`, `info`
- [ ] All recommendations are created with `status = "pending"`
- [ ] At least 3 recommendations are generated for any non-trivial dataset (>50 rows with sales and inventory data)
- [ ] Recommendations are logged in the audit trail with `human_checkpoint = true`

---

### US-06: Human Approval Before Action

**As a** manager, **I want to** approve or reject each AI recommendation individually, **so that** no automated action is taken without my explicit consent.

**Acceptance Criteria:**
- [ ] Each pending recommendation can be approved via `POST /recommendations/{id}/approve`
- [ ] Each pending recommendation can be rejected via `POST /recommendations/{id}/reject`
- [ ] Approving records the approver's name and timestamp on the recommendation
- [ ] Rejecting allows an optional `note` field for the reason
- [ ] Attempting to approve an already-approved recommendation returns HTTP 400 with message "Already approved"
- [ ] The approval or rejection event is logged in the audit trail with `human_checkpoint = true` and `approved_by` set

---

### US-07: Audit Trail

**As a** manager, **I want to** see a complete timeline of every automated and human step, **so that** I can trace how any recommendation was produced and verify that nothing happened silently.

**Acceptance Criteria:**
- [ ] The audit trail is accessible via `GET /audit-log?dataset_id={id}`
- [ ] Each entry contains: `agent_name`, `action`, `input_summary`, `output_summary`, `timestamp`
- [ ] Entries where `human_checkpoint = true` include `approved_by`
- [ ] Entries are returned in chronological order (oldest first)
- [ ] The audit log is append-only — no entries are ever deleted or modified

---

### US-08: Report Generation from Approved Actions

**As a** business owner, **I want** a report generated from only the recommendations I approved, **so that** I can share clear, approved action items with my team.

**Acceptance Criteria:**
- [ ] The report is generated via `POST /datasets/{id}/generate-report`
- [ ] The report contains only recommendations with `status = "approved"`
- [ ] Each recommendation in the report shows who approved it and when
- [ ] If zero recommendations are approved, the endpoint returns HTTP 400 with message "No approved recommendations. Approve at least one recommendation first."
- [ ] The report generation event is logged in the audit trail

---

### US-09: Sales and Customer Rankings

**As a** business owner, **I want to** see my top and bottom performing products and customers, **so that** I can focus attention where it has the most impact.

**Acceptance Criteria:**
- [ ] Top 10 products by revenue are returned, with revenue amount for each
- [ ] Bottom 10 products by revenue are returned
- [ ] Products are classified as A (top 80% cumulative revenue), B (next 15%), or C (bottom 5%)
- [ ] Top 5 customers by total purchase value are returned
- [ ] Customers with no purchases in the last 60 days are flagged as "inactive"

---

### US-10: Anomaly and Opportunity Detection

**As a** business owner, **I want** the system to flag sudden changes in my business metrics, **so that** I don't miss problems or opportunities.

**Acceptance Criteria:**
- [ ] Products with sales declining >30% compared to their average are flagged as anomalies
- [ ] Products with sales increasing >30% compared to their average are flagged as opportunities
- [ ] Each anomaly/opportunity shows: product name, previous value, current value, percentage change
- [ ] Anomalies are included in the recommendation list with appropriate severity

---

### US-11: Resume Screening

**As an** HR manager, **I want to** upload candidate resumes and have AI screen them against a job description, **so that** I can quickly identify the best-fit candidates without manually reading 50+ resumes.

**Acceptance Criteria:**
- [ ] HR manager can create a Job Description with required skills, preferred skills, and minimum experience
- [ ] Resumes are uploaded as a CSV file with columns: Name, Email, Skills, Experience, Education
- [ ] AI extracts skills from each resume and normalizes them (e.g., "MS Excel" → "excel")
- [ ] Each candidate receives a fit score (0–100) based on: required skills match (60%), preferred skills match (20%), experience (20%)
- [ ] Candidates are ranked by fit score and assigned a tier: Strong (≥70), Moderate (45–69), Weak (<45)
- [ ] Shortlist recommendations are generated with `status = "pending"` — same HITL pattern as inventory
- [ ] All screening steps are logged in the audit trail with agent name `HR_RESUME_SCREENING`

---

### US-12: Employee Onboarding

**As an** HR manager, **I want** the system to auto-generate a department-specific onboarding checklist when I register a new employee, **so that** no onboarding step is missed and progress is tracked.

**Acceptance Criteria:**
- [ ] HR manager can register a new employee with name, email, department, role, and join date
- [ ] Triggering onboarding generates a checklist with tasks in categories: HR, IT, Training, Team
- [ ] The checklist is department-specific (Sales, Warehouse, Finance, or Default template)
- [ ] Each task has a due date (days from join date)
- [ ] Tasks can be marked as completed with `completed_by` tracking
- [ ] Employee progress percentage is auto-calculated (completed/total tasks × 100)
- [ ] When all tasks are completed, employee status transitions to `completed`
- [ ] Onboarding creation is logged in the audit trail with agent name `HR_ONBOARDING`

---

## 8. Non-Functional Requirements

| Requirement | Target |
|------------|--------|
| **Response time** | Analysis pipeline completes in < 30 seconds for datasets up to 5,000 rows |
| **Data privacy** | Uploaded files stored locally only. No data sent to external services except LLM API for narrative generation (text summaries only, never raw business data) |
| **Auditability** | 100% of agent actions logged. Zero silent operations. |
| **Error handling** | All error states return clear, user-readable messages. No silent failures, no stack traces exposed to the user. |
| **Idempotency** | Re-analyzing the same dataset produces identical results (deterministic computation, no randomness in analysis) |

## 9. Success Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| Pipeline completion rate | % of uploaded files that complete the full Ingestion → Analysis → Insight pipeline without errors | > 95% |
| Recommendation relevance | % of generated recommendations that are Approved (not Rejected) by the manager | > 60% |
| Time to decision | Time from upload to manager reviewing recommendations | < 2 minutes |
| Audit coverage | % of pipeline steps that have a corresponding audit log entry | 100% |
<!-- PRD final revision sign-off -->

<!-- PRD final revision sign-off -->
