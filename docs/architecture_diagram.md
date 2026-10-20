# TraceLens System Architecture & Component Diagram

This document illustrates the layered architectural model, component boundaries, and data flows of TraceLens.

## Mermaid Architecture & Component Diagram

```mermaid
graph TD
    %% Presentation Tier
    subgraph UI_Layer [Presentation Layer - Streamlit UI]
        App["app.py (Main Application Shell & Glassmorphic Styling)"]
        P_Dash["dashboard_page.py (Health Gauge & Defect Tracker)"]
        P_Req["requirements_page.py (CRUD & CM History Rollback)"]
        P_Lint["linter_page.py (Rule Linter & Diff Inspector)"]
        P_Test["tests_page.py (Generator & Runner)"]
        P_Trace["traceability_page.py (Matrix Grids & CSV)"]
        P_Impact["impact_page.py (BFS Blast Radius & PyVis)"]
        P_Heat["heatmap_page.py (Gap Density Heatmap)"]
        P_Risk["risk_page.py (Prioritizer & RMMM Table)"]
        P_Export["export_page.py (ZIP Pack Generator)"]
    end

    %% Application / Domain Services Tier
    subgraph Service_Layer [Core Domain & Analytical Engines]
        S_Linter["core/linter.py (Rule-Based Linter & Conflict Engine)"]
        S_Impact["core/impact.py (BFS Blast Radius & Effort Estimator)"]
        S_Score["core/scoring.py (Composite Health & ISO 25010 Evaluator)"]
        S_Risk["core/risk.py (Risk Prioritizer & RMMM Generator)"]
        S_Graph["core/graph.py (NetworkX Builder & PyVis HTML Engine)"]
        S_AI["core/ai_client.py (Claude AI Client & Deterministic Mock Engine)"]
        S_Export["core/exporter.py (SRS/TestPlan/Matrix/Audit Packager)"]
    end

    %% Domain Entities Tier
    subgraph Model_Layer [Domain Models Layer]
        M_Models["core/models.py (Project, Requirement, DesignElement, TestCase)"]
    end

    %% Persistence & External Tier
    subgraph Data_Layer [Persistence & External Services]
        S_Storage["core/storage.py (Atomic File I/O Engine)"]
        DB_JSON[("data/project.json (Local JSON Store)")]
        DB_Sample[("data/sample_project.json (Demo Seed Data)")]
        Ext_Anthropic["Anthropic Claude API (claude-sonnet-4-6)"]
    end

    %% Inter-layer Dependencies
    App --> P_Dash
    App --> P_Req
    App --> P_Lint
    App --> P_Test
    App --> P_Trace
    App --> P_Impact
    App --> P_Heat
    App --> P_Risk
    App --> P_Export

    P_Dash --> S_Score
    P_Req --> M_Models
    P_Req --> S_Storage
    P_Lint --> S_Linter
    P_Lint --> S_AI
    P_Test --> S_AI
    P_Trace --> S_Export
    P_Impact --> S_Impact
    P_Impact --> S_Graph
    P_Heat --> S_Risk
    P_Risk --> S_Risk
    P_Export --> S_Export

    S_Linter --> M_Models
    S_Impact --> M_Models
    S_Impact --> S_Graph
    S_Score --> M_Models
    S_Score --> S_Linter
    S_Risk --> M_Models
    S_Graph --> M_Models
    S_AI --> M_Models
    S_AI --> Ext_Anthropic
    S_Export --> M_Models
    S_Export --> S_Linter
    S_Export --> S_Score
    S_Export --> S_Risk

    S_Storage --> M_Models
    S_Storage --> DB_JSON
    S_Storage --> DB_Sample
```

## Architectural Highlights

1. **Strict Layered Separation**: The presentation layer (Streamlit pages) depends exclusively on the domain services and domain models. The domain layer has zero dependency on UI frameworks.
2. **Deterministic Offline Resilience**: `core/ai_client.py` sits behind an abstract facade that queries Anthropic Claude when API credentials are provided, but falls back instantaneously to deterministic rule-based mock logic if offline or if an API failure occurs.
3. **Atomic File Persistence**: `core/storage.py` writes to a `.tmp` file and executes an atomic `os.replace` to prevent file corruption during demos or concurrent reads.
