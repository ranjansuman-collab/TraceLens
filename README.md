# 🔬 TraceLens: Living Requirements-to-Test Traceability & Quality Intelligence System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Pytest Tests](https://img.shields.io/badge/tests-44%20passed-brightgreen.svg)](https://docs.pytest.org/)
[![Test Coverage](https://img.shields.io/badge/coverage-core%2081%25%20%7C%20total%2038%25-yellow.svg)](https://coverage.readthedocs.io/)
[![Zero-Crash Guarantee](https://img.shields.io/badge/mode-Offline%20Mock%20Resilient-emerald.svg)]()

> A living, graph-reactive software engineering traceability platform built for university Software Engineering coursework.
> Connects requirements, architectural design elements, and test cases into an interactive dependency network that reacts to baseline changes, simulates blast radius impact, lints requirement quality against IEEE standards, detects semantic contradictions, exposes test coverage gaps, prioritizes risk, and exports certified SRS and Test Plan documentation.

---

## 🌟 Key Features

| Capability | Module | Description |
|:-----------|:-------|:------------|
| **Requirements Manager & CM** | `pages/requirements_page.py` | Add, edit, delete requirements with automated version increments, immutable history tracking, and one-click revision rollback. |
| **Quality Linter & Conflict Engine** | `pages/linter_page.py` | Scores requirement clarity (0-100) deducting for vague terms, missing metrics, passive voice, missing 'shall', and flags semantic contradictions. |
| **AI / Mock Refactoring** | `core/ai_client.py` | Rewrites ambiguous requirements into quantifiable IEEE specifications with unified diff inspection. Works offline via deterministic mock engine. |
| **Automated Test Generator** | `pages/tests_page.py` | Synthesizes positive, negative, boundary, and security test cases individually or in bulk for all uncovered requirements. |
| **Traceability Matrix** | `pages/traceability_page.py` | Bi-directional Requirements $\times$ Tests and Requirements $\times$ Design cross-reference grids with checkmarks and CSV export. |
| **Change Impact Simulator** | `pages/impact_page.py` | BFS blast radius analysis with interactive PyVis network coloring (Red, Orange, Yellow, Rose, Grey), rework effort estimations, and automated test regression tagging. |
| **Test Gap Heatmap** | `pages/heatmap_page.py` | Plotly heatmap of Requirements $\times$ Test Tiers (Unit, Integration, System, Acceptance) highlighting 0-count blind spots in red. |
| **Risk Prioritizer & RMMM** | `pages/risk_page.py` | Orders test execution by risk formula $\text{Impact} \times \text{Complexity} \times (1 + \text{Changes})$ and auto-generates top-5 RMMM table. |
| **Quality Health Score** | `pages/dashboard_page.py` | Composite 0-100 gauge (40% coverage + 30% clarity + 20% stability + 10% design links) with ISO/IEC 25010 factor evaluations. |
| **One-Click Export Pack** | `pages/export_page.py` | Compiles and downloads an in-memory ZIP containing `SRS.md`, `TestPlan.md`, `traceability_matrix.csv`, and `quality_report.md`. |

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.11 or newer (Python 3.11, 3.12 verified)
- Modern web browser (Chrome, Edge, Firefox, Safari)

### 1. Installation
Clone or navigate to the repository directory:
```bash
cd "d:/LAB PROJECT/Soft engr"
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
TraceLens runs with **100% functionality in Offline Mock Mode** right out of the box with zero configuration.
To enable Claude-powered AI rewrites and test generation:
```bash
cp .env.example .env
```
Edit `.env` and insert your Anthropic API key:
```ini
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-sonnet-4-6
```
*(If left empty or if network calls fail, TraceLens gracefully operates in Offline Mode with a visible UI badge).*

### 3. Launch the Application
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

---

## 🧪 Running Automated Tests

TraceLens includes a comprehensive Pytest test suite covering domain invariants, quality rules, BFS impact traversal, risk formulas, JSON sanitizers, and export generators.

Run all tests:
```bash
pytest -v
```

Run tests with test coverage analysis:
```bash
pytest --cov=core tests/
```
*Current test metrics: **44 passed tests**, **0 warnings**, **core coverage ~81%**, **total coverage ~38%**.*

---

## 🎬 3-Minute Live Demo Script

Follow this step-by-step walkthrough during presentations or project reviews:

### Step 1: Baseline Overview (0:00 - 0:30)
1. Launch `streamlit run app.py`.
2. Point out the **Mode Badge** in the sidebar: `⚡ Offline Mode (Deterministic Mock Engine)` or `🤖 AI Mode`.
3. In the **Dashboard**, show the **Quality Health Score Gauge (69.8 / Fair)**, the 4-factor breakdown, the **ISO 25010 Quality Factor Mapping**, and the active defect list.
4. If testing with modified data, click **"🔄 Reset Demo Data"** in the sidebar to return to the clean 12-requirement food delivery baseline.

### Step 2: Quality Linter & Semantic Contradictions (0:30 - 1:15)
1. Navigate to **🔍 Quality Linter & AI Rewrite**.
2. Notice the high-severity alert flagging the contradiction between:
   - **R6:** Guest checkout without creating an account.
   - **R7:** Mandatory phone authentication before placing orders.
3. Look at requirement **R3** (*"The UI must be user-friendly."*) or **R4** (*"The app should be fast."*), scored red/amber with deductions for vague terminology and missing measurable criteria.
4. Click **"🤖 AI Rewrite R4"**:
   - Inspect the side-by-side comparison and unified diff.
   - Click **"✅ Accept & Commit"** to instantly update the baseline to version `v2`.

### Step 3: Change Impact Simulator & BFS Blast Radius (1:15 - 2:00)
1. Navigate to **💥 Change Impact Simulator**.
2. Select **R2** (*Payment processing via Stripe*).
3. In the modification text box, change the latency threshold from `3 seconds` to `1 second` and add PayPal support.
4. Click **"⚡ Simulate Change Impact"**:
   - Show the interactive **PyVis Network Graph**:
     - 🔴 **R2** (Changed node in Red)
     - 🟠 **D2, D8** (Impacted Design Elements in Orange)
     - 🌸 **R11, R12** (Sibling Requirements sharing design elements in Rose)
     - 🟡 **T3, T4, T5, T13, T14** (Impacted Test Cases in Yellow)
   - Show the **Engineering Effort Estimation** table (Design: 4h, Code: 6h, Tests: 1.5h adjusted for complexity).
5. Click **"Apply Change & Flag Impacted Tests"**:
   - Show how the requirement bumps to `v3` and the impacted test cases are automatically flagged as **"Needs Review"**!

### Step 4: Test Gap Heatmap & Bulk Test Generation (2:00 - 2:30)
1. Navigate to **🗺️ Test Gap Heatmap**.
2. Point out the red cells indicating requirements lacking Unit, Integration, System, or Acceptance tests.
3. Show the table of uncovered requirements ranked by Risk Score.
4. Navigate to **🧪 Test Generator & Runner**:
   - Click **"🚀 Generate Tests for ALL Uncovered Requirements"**.
   - Watch the balloon celebration as tests are synthesized and linked for all gaps.
5. Re-check the **Dashboard** and **Heatmap** to see the Health Score jump from **Fair** to **Excellent (90+)**!

### Step 5: Exporting the Engineering Documentation Pack (2:30 - 3:00)
1. Navigate to **📦 Export Pack**.
2. Click **"📦 Download Complete Export Pack (.ZIP)"**.
3. Inspect the live previews of the generated documentation:
   - `SRS.md` (IEEE 830 compliant functional & non-functional requirements)
   - `TestPlan.md` (IEEE 829 strategy and risk-prioritized execution schedule)
   - `traceability_matrix.csv` (Bi-directional verification matrix)
   - `quality_report.md` (Health audit and RMMM table)

---

## 📸 Screenshots & Visual Asset Placeholders

When preparing your report or presentation slides, capture screenshots of the following views:
1. `screenshots/01_dashboard_health_gauge.png`: Executive dashboard showing the Plotly health score gauge, ISO 25010 factor evaluations, and test pass rate metrics.
2. `screenshots/02_requirements_catalog_and_cm.png`: Requirements catalog with version indicators, status badges, and the historical rollback view.
3. `screenshots/03_quality_linter_and_conflict.png`: Linter page displaying vague term deductions, semantic contradiction detection (R6 vs R7), and the AI rewrite diff inspector.
4. `screenshots/04_impact_blast_radius_graph.png`: Interactive PyVis network graph displaying the red/orange/yellow/rose blast radius and engineering effort estimation.
5. `screenshots/05_test_gap_heatmap.png`: Plotly verification gap heatmap highlighting red coverage voids across Unit, Integration, System, and Acceptance levels.
6. `screenshots/06_risk_and_rmmm_matrix.png`: Test cases sorted by risk score and the auto-generated top-5 RMMM table.
7. `screenshots/07_export_pack_preview.png`: One-click export download button and live in-app preview of IEEE 830 SRS and TestPlan.

---

## 📂 Project Directory Structure

```
tracelens/
├── app.py                      # Streamlit application entry point & layout shell
├── requirements.txt            # Pinned production dependencies
├── .env.example                # Sample environment configuration
├── README.md                   # System documentation & demo guide
├── data/
│   ├── sample_project.json     # Preloaded Online Food Delivery App baseline (12 reqs, 8 design, 14 tests)
│   └── project.json            # Active persistent project state (auto-created on run)
├── core/                       # Decoupled domain engine (pure Python, zero UI dependency)
│   ├── __init__.py             # Core package metadata
│   ├── models.py               # Dataclass models (Requirement, DesignElement, TestCase, Project)
│   ├── storage.py              # Atomic JSON persistence & sample reset
│   ├── linter.py               # Rule-based IEEE linter, conflict detector & diff engine
│   ├── graph.py                # NetworkX builder & PyVis interactive HTML renderer
│   ├── impact.py               # BFS change blast radius & effort estimator
│   ├── risk.py                 # Risk calculation, test ordering & RMMM table generator
│   ├── scoring.py              # 4-factor composite health score & ISO 25010 mapping
│   ├── ai_client.py            # Anthropic Claude client & deterministic mock engine
│   └── exporter.py             # SRS.md, TestPlan.md, Matrix CSV & ZIP packaging
├── pages/                      # Modular Streamlit view renderers
│   ├── __init__.py             # Pages package
│   ├── dashboard_page.py       # Health gauge, breakdown chart & defect tracker
│   ├── requirements_page.py    # CRUD forms & CM version rollback
│   ├── linter_page.py          # Quality linter, contradiction alerts & AI rewrite
│   ├── tests_page.py           # Single & bulk test generators and test runner
│   ├── traceability_page.py    # Req x Test and Req x Design matrices with CSV export
│   ├── impact_page.py          # BFS blast radius, PyVis graph & change commit
│   ├── heatmap_page.py         # Test gap density heatmap & risk-ranked gap list
│   ├── risk_page.py            # Risk-prioritized test schedule & RMMM table
│   └── export_page.py          # Documentation bundle generator & live previews
├── tests/                      # Automated test suite (35 unit & integration tests)
│   ├── __init__.py             # Test package
│   ├── test_models.py          # Invariant bounds, version increment & restore tests
│   ├── test_storage.py         # Atomic persistence & sample reload tests
│   ├── test_linter.py          # Quality penalty, conflict & diff tests
│   ├── test_graph.py           # NetworkX and PyVis rendering tests
│   ├── test_impact.py          # BFS blast radius, node coloring & effort tests
│   ├── test_risk.py            # Risk score, prioritization & RMMM tests
│   ├── test_scoring.py         # Composite health & ISO 25010 evaluation tests
│   ├── test_ai_client.py       # AI JSON sanitizer & mock fallback tests
│   └── test_exporter.py        # SRS, TestPlan, CSV & ZIP generation tests
└── docs/                       # Project report documentation & Mermaid models
    ├── use_case_diagram.md     # Mermaid use case model & actor descriptions
    ├── class_diagram.md        # Mermaid domain class diagram
    ├── architecture_diagram.md # Layered component & data flow diagram
    ├── sequence_diagram_impact.md # Sequence diagram for change impact simulation
    ├── srs_tracelens.md        # IEEE 830 SRS for TraceLens itself
    └── design_rationale.md     # Cohesion, coupling & modularity rationale
```

---

## ⚖️ License
Academic and Coursework Open Source License. Designed for university Software Engineering curricula.
