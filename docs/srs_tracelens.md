# Software Requirements Specification (SRS) for TraceLens

**Product:** TraceLens - Living Requirements-to-Test Traceability & Quality Intelligence System  
**Document Version:** 1.0.0  
**Standard:** IEEE Std 830-1998 Compliant  
**Target Environment:** Python 3.11+ / Streamlit / Modern Web Browsers  

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) establishes the complete functional and non-functional requirements for the **TraceLens** system. TraceLens is designed for university software engineering courses and industry-grade engineering environments to provide living traceability, automated quality linting, change impact blast radius analysis, risk prioritization, test case generation, and documentation export.

### 1.2 Scope
TraceLens provides an end-to-end connected network linking Requirements ($R$), Design Elements ($D$), and Test Cases ($T$). The software models changes dynamically, visualizes blast radius through graph algorithms, evaluates quality metrics mapped to ISO/IEC 25010, and automates test suite synthesis using Large Language Models with complete offline fallback resilience.

---

## 2. Overall Description

### 2.1 Product Perspective
TraceLens operates as a self-contained web application requiring zero external database setup. All state is maintained through atomic JSON persistence (`data/project.json`), with optional integration to the Anthropic Claude API for advanced NLP synthesis.

### 2.2 User Classes and Characteristics
1. **Requirements Engineers:** Need automated tools to detect ambiguities, enforce normative syntax, and audit revision histories.
2. **Software Architects:** Require graph visualization of architectural dependencies to evaluate blast radius before modifying baselines.
3. **QA & Test Engineers:** Require test gap heatmaps, risk-prioritized execution schedules, and automated test generators.
4. **Project Managers & Course Evaluators:** Need composite health gauges, ISO 25010 audits, and one-click export packs.

---

## 3. Functional Requirements

### Feature A: Requirements Baseline & Configuration Management
- **FR-01 (Baseline Management):** The system shall permit users to create, view, update, and delete software requirements with attributes: `id`, `text`, `type` (Functional/Non-Functional), `priority` (High/Medium/Low), `impact` (1-5), and `complexity` (1-5).
- **FR-02 (Audit & Versioning):** Every text edit to a requirement shall automatically increment its version number, record an immutable timestamped history snapshot, and set its status to `Changed`.
- **FR-03 (Configuration Management Rollback):** The system shall allow users to inspect historical snapshots and restore any previous version, creating a new revision entry documenting the rollback.

### Feature B: Requirement Quality Linter & AI Rewriter
- **FR-04 (Rule-Based Quality Linter):** The system shall score requirement clarity from 0 to 100, starting at 100 and deducting:
  - Vague terms (*fast, easy, user-friendly, efficient, flexible, robust, scalable, seamless, intuitive*): `-15` points each.
  - Absence of measurable criteria or numbers: `-20` points.
  - Absence of normative auxiliary `shall`: `-10` points.
  - Compound coordination conjunctions (multiple *and*/*or*): `-10` points.
  - Absence of explicit primary actor: `-10` points.
  - Passive voice constructions: `-5` points.
- **FR-05 (Semantic Conflict Detection):** The system shall evaluate requirement pairs to detect contradictory policies (e.g., anonymous guest checkout vs. mandatory authenticated phone registration) and display high-severity alerts.
- **FR-06 (AI & Template Refactoring):** The system shall provide an "AI Rewrite" capability that converts ambiguous statements into measurable IEEE specifications, showing unified text diffs and permitting user acceptance or rejection.

### Feature C: Automated Test Case Generator
- **FR-07 (Multi-Tier Test Generation):** The system shall synthesize 3 to 4 categorized test cases (Positive, Negative, Boundary, Performance/Security) for any selected requirement.
- **FR-08 (Bulk Test Generation):** The system shall provide a single-action bulk test generator that synthesizes and links test cases for all uncovered requirements.
- **FR-09 (Resilient Parsing):** The system shall safely parse JSON responses from AI models, retry once on malformed output, and fall back to template generation without crashing.

### Feature D: Bi-Directional Traceability Matrix
- **FR-10 (Cross-Reference Matrices):** The system shall render Requirements $\times$ Tests and Requirements $\times$ Design cross-reference matrices with checkmarks (`✔`).
- **FR-11 (Filtering & CSV Export):** Users shall be able to filter matrices by priority, type, and coverage status, and export the matrix to CSV.

### Feature E: Change Impact Simulation & Blast Radius
- **FR-12 (BFS Graph Traversal):** Upon editing a requirement, the system shall run a Breadth-First Search over the traceability network to identify all directly and transitively impacted nodes.
- **FR-13 (Visual Blast Radius):** The system shall render an interactive PyVis network color-coding:
  - Changed Requirement: Red (`#EF4444`)
  - Impacted Design Elements: Orange (`#F97316`)
  - Impacted Test Cases: Yellow (`#FACC15`)
  - Sibling Requirements Sharing Design Elements: Rose/Pink (`#FB7185`)
  - Unaffected Baseline Nodes: Grey (`#64748B`)
- **FR-14 (Rework Effort Estimation):** The system shall compute engineering rework hours using base rates: Design updates ($4.0\text{h}$), Source implementation ($6.0\text{h}$), Test updates ($1.5\text{h}$), scaled by $\frac{\text{complexity}}{3.0}$.
- **FR-15 (Automated Regression Tagging):** Applying a change shall commit the new revision and automatically mark all impacted test cases with status `Needs Review`.

### Feature F: Test Gap Density Heatmap
- **FR-16 (Heatmap Visualization):** The system shall display a Plotly heatmap plotting requirements as rows and test levels (*Unit, Integration, System, Acceptance*) as columns, highlighting zero-count coverage blind spots in red.
- **FR-17 (Risk-Ranked Gap Table):** Uncovered requirements shall be ranked descending by risk score below the heatmap.

### Feature G: Risk-Based Prioritizer & RMMM Table
- **FR-18 (Risk Metric Calculation):** Requirement risk shall be computed as $\text{Risk} = \text{Impact} \times \text{Complexity} \times (1 + \text{Change Count})$.
- **FR-19 (Test Prioritization):** The system shall sort test execution order descending by the risk score of linked requirements.
- **FR-20 (RMMM Generation):** The system shall auto-generate an RMMM (Risk Mitigation, Monitoring, and Management) table for the top 5 highest-risk requirements.

### Feature H: Quality Health Score & ISO 25010 Evaluation
- **FR-21 (Composite Health Metric):** The system shall compute an executive health score ($0-100$):
  $$\text{Health} = 0.40 \cdot \text{TestCoverage}_{\text{weighted}} + 0.30 \cdot \text{AvgClarity} + 0.20 \cdot \text{Stability} + 0.10 \cdot \text{DesignLinkCoverage}$$
  where Test Coverage weights priorities (High: 3, Medium: 2, Low: 1) and Stability equals $100 - \text{Volatility Index}$.
- **FR-22 (ISO/IEC 25010 Mapping):** The system shall evaluate and report compliance scores, statuses, and recommendations for **Testability (§4.2.7)**, **Maintainability (§4.2.8)**, and **Reliability (§4.2.4)**.

### Feature I: Artifact Export Pack
- **FR-23 (One-Click ZIP Bundle):** The system shall package and download an in-memory ZIP archive containing:
  - `SRS.md` (IEEE 830 formatted system requirements)
  - `TestPlan.md` (IEEE 829 formatted test strategy and risk-prioritized schedule)
  - `traceability_matrix.csv`
  - `quality_report.md` (Executive scorecard, ISO 25010 assessment, RMMM table)

### Feature J: Test Run Tracker & Defect Density
- **FR-24 (Execution State Tracking):** Users shall be able to update test statuses to *Pass, Fail, Needs Review,* or *Not Run*.
- **FR-25 (Defect Metrics):** The system shall compute pass rates, active defect counts, and defect density ($\frac{\text{Failed Tests}}{\text{Requirements Count}}$).

---

## 4. Non-Functional Requirements (NFR)

- **NFR-01 (Fault Tolerance & Zero Demo Crashes):** The system must execute fully in Offline Mock Mode when no API key is provided or when an external API call fails.
- **NFR-02 (Performance):** Graph BFS traversal, quality scoring, and matrix rendering must execute in under $500\text{ ms}$ for projects containing up to 100 requirements.
- **NFR-03 (Data Integrity & Atomic Persistence):** File writes to `data/project.json` shall use atomic staging (`.tmp` to target replacement) to prevent file corruption.
- **NFR-04 (Cross-Platform Portability):** The system shall run consistently on Windows, macOS, and Linux using Python 3.11+ and standard modern web browsers.
- **NFR-05 (Visual Distinction):** The active execution mode (AI Mode vs. Offline Mode) must be prominently displayed on every screen with distinct visual badges.
