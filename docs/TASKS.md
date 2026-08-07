# Task Breakdown — Asclepius

Tasks are organized by user story ID for traceability. Each task references the story it implements. Commit messages follow the pattern `feat(US-XX): description`.

## Sprint 1: Foundation and Spec (Day 1)

- [x] **TASK-01** (US-01, US-02): Set up repo structure, CI skeleton, agent rules file
- [x] **TASK-02**: Write PRD with problem statement, users, scope, out-of-scope reasoning
- [x] **TASK-03**: Write user stories US-01 through US-10 with testable acceptance criteria
- [x] **TASK-04**: Write architecture document with stack, data model, diagrams, decision reasoning
- [x] **TASK-05**: Write AGENTS_AND_SKILLS.md documenting all agents and skills

## Sprint 2: Data Pipeline (Day 1–2)

- [x] **TASK-06** (US-01): Implement upload endpoint with file validation
- [x] **TASK-07** (US-02): Implement IngestionAgent — parse, clean, deduplicate, standardize columns
- [x] **TASK-08** (US-02): Add entity resolution for inconsistent product names
- [x] **TASK-09**: Generate synthetic sample datasets (pharma + retail)

## Sprint 3: Analysis Engine (Day 2)

- [x] **TASK-10** (US-09): Implement sales analysis module — revenue, rankings, trends, Pareto
- [x] **TASK-11** (US-04): Implement inventory analysis — ABC classification, dead stock, near-expiry
- [x] **TASK-12** (US-09): Implement customer analysis — RFM scoring, segmentation, churn detection
- [x] **TASK-13** (US-03): Implement KPI engine and Business Health Score (0–100)
- [x] **TASK-14** (US-10): Implement anomaly and opportunity detection
- [x] **TASK-15** (US-09, US-03, US-04): Wire AnalysisAgent to call real analysis modules

## Sprint 4: Recommendations and Approval (Day 2)

- [x] **TASK-16** (US-05): Upgrade InsightAgent with 15 business rules
- [x] **TASK-17** (US-06): Implement approve/reject API with audit logging
- [x] **TASK-18** (US-08): Implement ReportAgent — structured report from approved items only
- [x] **TASK-19** (US-07): Implement audit trail API endpoint

## Sprint 5: API and Integration (Day 2–3)

- [x] **TASK-20** (US-03): Add `/datasets/{id}/kpis` endpoint
- [x] **TASK-21** (US-09): Add `/datasets/{id}/sales`, `/inventory`, `/customers` endpoints
- [x] **TASK-22** (US-05): Add `/datasets/{id}/priority-queue` endpoint
- [x] **TASK-23**: Mount all new routers in main.py

## Sprint 6: Testing and CI (Day 3)

- [x] **TASK-24**: Write pytest fixtures with sample data
- [x] **TASK-25**: Write agent unit tests (ingestion, analysis, insight, report)
- [x] **TASK-26**: Write analysis module tests (sales, inventory, customer, KPI)
- [x] **TASK-27**: Fix CI pipeline — remove `|| true`, add real validation
- [x] **TASK-28**: Fix Dockerfile build order
- [x] **TASK-29**: End-to-end smoke test: upload → analyze → approve → report

## Sprint 7: Polish and Submission (Day 3)

- [x] **TASK-30**: Update README with complete setup instructions
- [x] **TASK-31**: Create `.env.example`
- [ ] **TASK-32**: Frontend integration (separate track)
- [ ] **TASK-33**: Demo video recording
- [ ] **TASK-34**: Tag release v1.0.0

## Sprint 8: HR Automation Module (Day 3)

- [x] **TASK-35** (US-11): Add `module` field to Dataset, Recommendation, AuditLog for multi-module support
- [x] **TASK-36** (US-11): Add HR models — JobDescription, ResumeScreening, Employee, OnboardingTask
- [x] **TASK-37** (US-11): Implement skill extraction with pharma industry synonym normalization
- [x] **TASK-38** (US-11): Implement JD matching with weighted scoring (required 60%, preferred 20%, experience 20%)
- [x] **TASK-39** (US-11): Implement ResumeScreeningAgent — parse, extract, score, rank, recommend
- [x] **TASK-40** (US-12): Implement OnboardingAgent — department-specific checklists (Sales, Warehouse, Finance, Default)
- [x] **TASK-41** (US-11, US-12): Implement HR API endpoints (JDs, screening, employees, onboarding)
- [x] **TASK-42**: Generate HR sample data (50 resumes, 1 JD)
- [x] **TASK-43** (US-11, US-12): Write HR module tests (7 tests covering full pipelines)
- [x] **TASK-44**: Update all documentation (PRD US-11/US-12, Architecture, Agents, Audit Trail)
- [x] **TASK-45**: Add `/modules` endpoint and rebrand as AI Business Operating System

