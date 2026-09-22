# BugLens — Automated Bug Report Classification using Agentic AI

> **Course Project:** Agentic AI (B.Tech Computer Science & Engineering)  
> **Product Name:** BugLens  
> **Subtitle:** Intelligent bug triage, technical research, and debugging recommendations powered by Groq and Tavily.

---

## 1. Project Overview

**BugLens** is a full-stack, developer-focused Automated Bug Report Classification and Triage system. Rather than acting as a simple conversational chatbot, BugLens implements an **autonomous multi-agent pipeline** where six specialized agents collaborate to parse, classify, research, evaluate, and provide diagnostic recommendations for incoming software defects.

### Key Capabilities
- **Deep Report Parsing:** Deconstructs user bug reports, error logs, and stack traces into structured symptoms, technical entities, and missing information.
- **Strict Classification:** Automatically assigns standard defect categories (12 classes), severity levels (`Critical`, `High`, `Medium`, `Low`), and priority tags (`P0`, `P1`, `P2`, `P3`).
- **Targeted Technical Research:** Formulates focused technical search queries and retrieves 3–5 authoritative sources (documentation, GitHub issues, StackOverflow) using the Tavily Search API.
- **Grounded Evidence Synthesis:** Synthesizes external findings against reported symptoms using Groq LLM reasoning without false certainty.
- **Actionable Debugging Guidance:** Generates ordered, non-invasive debugging steps, verification tests, and long-term architectural prevention measures.
- **Persistent Local History:** Stores and indexes reports in SQLite with fast search and filtering by category and severity.
- **Export & Reporting:** One-click JSON export and printable browser report generation.
- **Zero-Config Demo Mode:** Comes with realistic pre-computed demo scenarios for immediate testing without external API keys.

---

## 2. Agentic AI Architecture & Workflow

BugLens decomposes defect triage into a sequential pipeline of specialized agents:

```
                  ┌─────────────────────────────────┐
                  │    User Bug Report & Telemetry   │
                  │ (Title, Steps, Environment, Log) │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │      Input Validation Layer     │
                  │   Checks mandatory requirements │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │ 1. Bug Understanding Agent      │
                  │    Extracts symptoms & entities │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │ 2. Classification Agent         │
                  │    Category, Severity, Priority │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │ 3. Tavily Research Agent        │
                  │    Fetches external tech docs   │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │ 4. Evidence Analysis Agent      │
                  │    Corroborates symptoms & docs │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │ 5. Recommendation Agent         │
                  │    Investigation steps & tests  │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │ 6. Final Report Generator Agent │
                  │    Compiles RFC-8259 JSON       │
                  └────────────────┬────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
       ┌────────────────────────┐    ┌────────────────────────┐
       │     SQLite Database    │    │  Interactive Dashboard │
       │ (Thread-safe storage)  │    │  (Vanilla HTML/CSS/JS) │
       └────────────────────────┘    └────────────────────────┘
```

### Agent Roles Breakdown
| Agent | Responsibility | Output Artifact |
|---|---|---|
| **Agent 1: Bug Understanding Agent** | Reads the report, extracts factual symptoms, runtimes, versions, modules, and flags missing details. | `BugUnderstandingResult` |
| **Agent 2: Classification Agent** | Evaluates defect impact to categorize the bug, assign severity, assign priority, and formulate a root-cause hypothesis. | `ClassificationResult` |
| **Agent 3: Tavily Research Agent** | Formulates precision technical queries and retrieves external documentation, issues, and references. | `ResearchResult` |
| **Agent 4: Evidence Analysis Agent** | Compares external findings with user symptoms and assesses confidence. | `EvidenceAnalysisResult` |
| **Agent 5: Recommendation Agent** | Orders debugging steps logically, generates verification test steps, and architectural prevention rules. | `RecommendationResult` |
| **Agent 6: Final Report Generator** | Synthesizes all intermediate agent outputs into a standardized schema with an auditable agent trace. | `FinalBugReport` |

---

## 3. Technology Stack

- **Backend:** Python 3.10+, Flask 3.0
- **Reasoning LLM:** Groq API (`llama-3.3-70b-versatile` configurable in `.env`)
- **Technical Research:** Tavily Search API (`tavily-python`)
- **Database:** SQLite 3 (built-in, thread-safe, parameterized queries)
- **Frontend:** Plain HTML5, CSS3, Vanilla JavaScript (ES6+)
  - *No React, No Vue, No Angular, No Tailwind, No Bootstrap*
- **Testing:** Pytest

---

## 4. Project Directory Structure

```
automated-bug-classifier/
├── app.py                      # Flask Application Entry Point & Route Handlers
├── requirements.txt            # Python Dependencies
├── .env.example                # Environment Variable Template
├── .env                        # Local Environment Config (Ignored by Git)
├── .gitignore                  # Git Ignore Rules
├── README.md                   # Complete Documentation
│
├── database/                   # SQLite Storage
│   └── bug_reports.db          # Auto-created on First Execution
│
├── models/                     # Data Schemas & Validation
│   ├── __init__.py
│   └── schemas.py              # Strict Schema Definitions & Sanitizers
│
├── services/                   # Backend Services
│   ├── __init__.py
│   ├── database_service.py     # Parameterized SQLite Operations & Metrics
│   ├── groq_service.py         # Groq LLM Client & JSON Output Enforcement
│   ├── tavily_service.py       # Tavily Search Client & Fallback Logic
│   └── demo_data.py            # Calibrated Sample Bugs & Offline Demos
│
├── agents/                     # Multi-Agent Workflow Implementation
│   ├── __init__.py
│   ├── prompts.py              # Dedicated System & User Prompts
│   ├── bug_understanding.py    # Agent 1: Understanding & Telemetry Extraction
│   ├── classifier.py           # Agent 2: Category, Severity & Priority Triage
│   ├── researcher.py           # Agent 3: Search Querying & Tavily Context
│   ├── evidence_analyzer.py    # Agent 4: Evidence Corroboration & Hypotheses
│   ├── recommender.py          # Agent 5: Debugging Actions & Testing Plans
│   ├── report_generator.py     # Agent 6: Report Synthesis & Agent Trace
│   └── orchestrator.py         # Pipeline Coordinator & State Machine
│
├── routes/                     # REST API Blueprints
│   ├── __init__.py
│   ├── analysis_routes.py      # /api/analyze, /api/health, /api/sample-bugs
│   ├── history_routes.py       # /api/history CRUD
│   └── dashboard_routes.py     # /api/dashboard Metrics
│
├── templates/                  # Jinja2 HTML5 Templates
│   ├── base.html               # Common Developer Layout & Modal
│   ├── index.html              # Analytics Dashboard
│   ├── analyze.html            # New Report Form & Real-Time Stepper
│   ├── result.html             # Detailed Triage Verdict & Export Options
│   ├── history.html            # Searchable History Table & Filters
│   └── about.html              # Architecture & CSS Workflow Diagram
│
├── static/                     # Frontend Assets (Vanilla Only)
│   ├── css/
│   │   └── style.css           # Developer-Tool Design System & Print Styles
│   └── js/
│       ├── api.js              # Centralized Fetch Client
│       ├── ui.js               # Toasts, Modals, Badges, Print & JSON Download
│       ├── dashboard.js        # Metric Counters & Recent Analyses Table
│       ├── analysis.js         # Form Validation & Multi-Agent Progression
│       └── history.js          # Search, Filtering & Delete Actions
│
└── tests/                      # Automated Pytest Suite
    ├── __init__.py
    ├── test_api.py             # Integration Tests for REST Endpoints
    ├── test_database.py        # Database Operations & Aggregations
    └── test_agents.py          # Validation, Agents & Orchestration
```

---

## 5. Prerequisites

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** Python 3.10 or higher (Python 3.11, 3.12, and 3.13 supported)
- **PowerShell** (on Windows) or Bash

---

## 6. Windows Installation & Setup (PowerShell)

Open PowerShell and follow these exact steps:

### Step 1: Open the Project Directory
```powershell
cd "d:\CA3 Agentic"
```

### Step 2: Create a Virtual Environment
```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

> **Note on PowerShell Execution Policy:**  
> If you see `File Activate.ps1 cannot be loaded because running scripts is disabled`, run this single command to enable script execution for your current user:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then re-run `.\.venv\Scripts\Activate.ps1`.

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```

Open `.env` in VS Code or Notepad:
```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Tavily API Configuration
TAVILY_API_KEY=your_tavily_api_key_here

# Demo Mode (Set 'true' to run offline without API keys, 'false' for live APIs)
DEMO_MODE=true

# Flask Configuration
PORT=5000
```

---

## 7. Running the Application

Ensure your virtual environment is active, then execute:

```powershell
python app.py
```

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

The system will initialize the SQLite database at `database/bug_reports.db` automatically on first run.

---

## 8. Demo Mode vs. Live Mode

BugLens includes a native **Demo Mode** designed specifically for academic evaluations, grading, and offline presentations:

- **When `DEMO_MODE=true`:**
  - The application requires **zero external API keys**.
  - All 6 agent workflow stages simulate realistic timing and telemetry extraction.
  - Generates rich, pre-calibrated analyses with valid categories, severities, real technical links, and debugging steps.
  - Saves all analyses persistently in your local SQLite database.
  - Clearly displays a `Demo Mode` indicator in the header and result badges.

- **When `DEMO_MODE=false`:**
  - Connects directly to the **Groq API** for live LLM reasoning.
  - Connects to the **Tavily API** to execute live technical web searches.
  - If Tavily is unconfigured or rate-limited, the system gracefully falls back and indicates: `External research unavailable` while still performing classification via Groq.

---

## 9. API Endpoints Reference

All endpoints return standard JSON responses:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Returns health status, API key states, model, and demo mode. |
| `GET` | `/api/dashboard` | Returns aggregate metrics (Total, Critical, High Priority, Categories). |
| `GET` | `/api/sample-bugs` | Returns list of pre-configured sample bugs for form pre-filling. |
| `POST` | `/api/analyze` | Submits a bug report to the Agentic AI pipeline. |
| `GET` | `/api/history` | Lists historical reports with `search`, `category`, and `severity` filters. |
| `GET` | `/api/history/<id>` | Retrieves full details and result JSON for a specific report. |
| `DELETE` | `/api/history/<id>` | Permanently deletes a report record from SQLite. |

---

## 10. Example Bug Report Walkthrough

Try loading the preset example in the UI or submitting via `POST /api/analyze`:

```json
{
  "title": "Flask API returns database locked error under concurrent requests",
  "description": "The appointment booking API intermittently fails with a 500 status when multiple concurrent users attempt to reserve slots simultaneously.",
  "expected_behavior": "All concurrent valid appointment requests should be processed sequentially or queued gracefully without database lock exceptions.",
  "actual_behavior": "Flask application raises 'sqlite3.OperationalError: database is locked' during peak booking times.",
  "steps_to_reproduce": "1. Start Flask API.\n2. Send 25 concurrent POST requests to /api/appointments.\n3. Observe intermittent 500 error in server logs.",
  "environment": "Windows 11, Python 3.11, Flask 3.0, SQLite 3.42, Gunicorn 21.2 (4 workers)",
  "error_log": "sqlite3.OperationalError: database is locked at cursor.execute() in appointments.py:45",
  "stack_trace": "File flask/app.py line 1477\nFile routes/appointments.py line 45",
  "component": "Database / Appointment Service",
  "existing_labels": "backend, database, concurrency"
}
```

### Generated Triage Verdict:
- **Category:** `Database Bug`
- **Severity:** `High`
- **Priority:** `P1`
- **Confidence:** `92%`
- **Probable Root Cause:** `Concurrent write operations across multiple Gunicorn worker processes exceed SQLite's single-writer concurrency limit, triggering busy timeout exceptions.`
- **Recommended Actions:**
  1. Enable Write-Ahead Logging (WAL) mode: `PRAGMA journal_mode=WAL;`.
  2. Increase connection busy timeout: `sqlite3.connect(db_path, timeout=30.0)`.
  3. Ensure connections are scoped per request using Flask's `g` object.

---

## 11. Running Automated Tests

BugLens includes an automated test suite verifying database integrity, REST API endpoints, agent pipelines, and validation logic.

To run the tests:
```powershell
pytest -v tests/
```

Expected output:
```
tests/test_agents.py::test_validate_bug_input_valid PASSED
tests/test_agents.py::test_validate_bug_input_missing_fields PASSED
tests/test_agents.py::test_sanitize_classification PASSED
tests/test_agents.py::test_report_generator PASSED
tests/test_agents.py::test_orchestrator_demo_mode PASSED
tests/test_api.py::test_health_endpoint PASSED
tests/test_api.py::test_sample_bugs_endpoint PASSED
tests/test_api.py::test_dashboard_endpoint PASSED
tests/test_api.py::test_analyze_empty_payload PASSED
tests/test_api.py::test_analyze_valid_demo_mode PASSED
tests/test_database.py::test_db_initialization PASSED
tests/test_database.py::test_save_and_get_report PASSED
tests/test_database.py::test_list_and_filter_reports PASSED
tests/test_database.py::test_delete_report PASSED
tests/test_database.py::test_dashboard_metrics PASSED

15 passed in ~1.2s
```

---

## 12. Troubleshooting

### Issue: "Execution of scripts is disabled on this system"
**Solution:** Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell, then activate `.venv` again.

### Issue: "Port 5000 is already in use"
**Solution:** Change `PORT=5001` in your `.env` file and re-run `python app.py`.

### Issue: "Groq API key missing"
**Solution:** Either set `DEMO_MODE=true` in `.env` to test offline immediately, or acquire a free API key from [Groq Console](https://console.groq.com/) and paste it into `.env`.

---

## 13. License & Academic Integrity
Developed as a B.Tech Computer Science course project demonstrating **Agentic AI** principles, autonomous multi-stage reasoning, and full-stack software architecture.
