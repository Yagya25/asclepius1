# Asclepius — AI Business Operating System

**Multi-Module Business Process Automation for SMEs**

Asclepius is a modular AI platform that automates repetitive business workflows across departments. Each module follows the same agent-driven pattern: **AI does the work → Human approves → Nothing happens silently.**

Built for the [Deploy or Die Hackathon](https://gdg.community.dev/), Track A: Business Process Automation.

## Active Modules

| Module | Description | Status |
|--------|-------------|--------|
| 📊 **Inventory & Sales Intelligence** | Upload pharma ERP data → AI analysis → recommendations → approval → report | ✅ Active |
| 👥 **HR Automation** | Resume screening, employee onboarding with department-specific checklists | ✅ Active |
| 💰 **Finance Automation** | Invoice processing, expense auditing, GST reconciliation | 🔜 Planned |
| ⚙️ **Operations Intelligence** | Task automation, workflow optimization, SLA tracking | 🔜 Planned |

## How It Works

Every module follows the same architecture:

```
Upload Data → Agent Pipeline (clean → analyze → recommend)
                  → ⏸️ Manager Approves/Rejects
                       → Report (approved actions only)
                            → Full Audit Trail
```

**Key principle**: Every automated step is logged. Every recommendation requires human approval. Nothing happens silently. This pattern is identical across Inventory, HR, and any future module.

## Quick Start

### Prerequisites
- Python 3.11+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_TEAM/asclepius-starter.git
cd asclepius-starter/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create uploads directory
mkdir -p uploads

# Start the server
uvicorn app.main:app --reload
```

### Verify

```bash
# Health check
curl http://localhost:8000/health
# → {"status": "ok", "service": "asclepius"}

# List available modules
curl http://localhost:8000/modules

# Open API docs
# → http://localhost:8000/docs
```

### Docker (Alternative)

```bash
docker-compose up --build
# → Backend at http://localhost:8000
# → PostgreSQL at localhost:5432
```

## API Reference

### Inventory & Sales Module

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/datasets/upload` | Upload Excel/CSV file |
| `GET` | `/datasets/` | List all datasets |
| `POST` | `/datasets/{id}/analyze` | Run full analysis pipeline |
| `GET` | `/datasets/{id}/kpis` | Get KPIs + Business Health Score |
| `GET` | `/datasets/{id}/sales` | Sales analysis results |
| `GET` | `/datasets/{id}/inventory` | Inventory analysis results |
| `GET` | `/datasets/{id}/customers` | Customer analysis results |
| `GET` | `/datasets/{id}/priority-queue` | Top actions by severity |
| `POST` | `/datasets/{id}/generate-report` | Generate report (approved only) |

### HR Automation Module

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/hr/job-descriptions` | Create a job description |
| `GET` | `/hr/job-descriptions` | List job descriptions |
| `POST` | `/hr/screen-resumes?jd_id={id}` | Upload resumes CSV → screen against JD |
| `GET` | `/hr/screenings/{id}/results` | Get scored & ranked candidates |
| `POST` | `/hr/employees` | Register new employee |
| `POST` | `/hr/employees/{id}/onboard` | Trigger onboarding agent |
| `GET` | `/hr/employees/{id}/onboarding` | Onboarding checklist & progress |
| `POST` | `/hr/onboarding-tasks/{id}/complete` | Mark task complete |

### Shared Infrastructure (Cross-Module)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/modules` | List all business modules |
| `GET` | `/recommendations/` | List recommendations (filter by module) |
| `POST` | `/recommendations/{id}/approve` | Approve a recommendation |
| `POST` | `/recommendations/{id}/reject` | Reject a recommendation |
| `GET` | `/audit-log/` | Audit trail (spans all modules) |
| `GET` | `/audit-log/timeline?dataset_id={id}` | Decision timeline |

## Sample Data

Sample datasets are included in `samples/` for testing:

### Inventory Module
- `pharma_distributor_sales.xlsx` — pharma distribution sales data with intentional data quality issues (Excel format)
- `pharma_retail_chemist_sales.csv` — clean pharma retail chemist sales data (CSV format)

### HR Module
- `hr_sample_resumes.csv` — 50 pharma industry candidate resumes (varied skill levels)
- `hr_sample_jd.json` — Job description for Pharma Sales Representative

Regenerate with:
```bash
python samples/generate_sample_data.py
python samples/generate_hr_data.py
```

## Project Structure

```
├── backend/app/
│   ├── agents/          # Core agent pipeline (ingestion, analysis, insight, report)
│   ├── analysis/        # Business analysis modules (sales, inventory, customer, KPI)
│   ├── modules/
│   │   └── hr/          # HR module (resume screening, onboarding)
│   ├── api/             # FastAPI route handlers (datasets, hr, approvals, audit)
│   ├── models.py        # SQLAlchemy data models (shared + module-specific)
│   └── db.py            # Database configuration
├── docs/
│   ├── ARCHITECTURE.md  # System design, stack choices, data model
│   ├── PRD.md           # Product requirements + user stories
│   ├── TASKS.md         # Task breakdown with story ID references
│   └── AUDIT_TRAIL.md   # Audit trail design
├── samples/             # Sample datasets + generators
├── AGENTS_AND_SKILLS.md # Custom agents and skills documentation
└── .clinerules          # Agent constitution / rules
```

## Documentation

| Document | Purpose |
|----------|---------|
| [PRD](docs/PRD.md) | Problem, users, scope, user stories with acceptance criteria |
| [Architecture](docs/ARCHITECTURE.md) | Stack, data model, diagrams, design decisions |
| [Agents & Skills](AGENTS_AND_SKILLS.md) | Custom agents and reusable skills |
| [Audit Trail](docs/AUDIT_TRAIL.md) | What gets logged, when, traceability design |
| [Tasks](docs/TASKS.md) | Task breakdown with story ID traceability |

## Team

Built for "Deploy or Die: HowToAlgo x GDG on Campus KIIT Hackathon"
Track A: Business Process Automation | Agent-Driven Lifecycle (ADLC)
