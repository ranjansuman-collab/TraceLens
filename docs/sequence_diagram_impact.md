# TraceLens Sequence Diagram: Change Impact Simulation

This document outlines the detailed sequence of interactions during a Change Impact Simulation and commit lifecycle.

## Mermaid Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as Software Architect / Engineer
    participant UI as Streamlit Impact Page (impact_page.py)
    participant CoreImpact as Impact Engine (core/impact.py)
    participant CoreGraph as Graph Engine (core/graph.py)
    participant PyVisNet as PyVis / Vis.js Canvas
    participant Models as Domain Models (core/models.py)
    participant Storage as Persistence Layer (core/storage.py)

    %% Step 1: User Initiates Simulation
    User->>UI: Selects Requirement (e.g. R2) & Edits Text
    User->>UI: Clicks "⚡ Simulate Change Impact"
    activate UI
    
    UI->>CoreImpact: simulate_change_impact(project, "R2")
    activate CoreImpact

    %% Step 2: BFS Traversal & Blast Radius
    CoreImpact->>Models: Find direct design elements (D2, D8)
    CoreImpact->>Models: Find sibling requirements sharing D2/D8 (R11, R12)
    CoreImpact->>Models: Find direct test cases (T3, T4, T5)
    CoreImpact->>Models: Find transitive sibling test cases (T13, T14)
    
    %% Step 3: Color Mapping & Effort Calculation
    CoreImpact->>CoreImpact: Assign Color Codes (Red=R2, Orange=D2/D8, Rose=R11/R12, Yellow=Tests)
    CoreImpact->>CoreImpact: Compute Effort (Design: 4h*cf, Code: 6h*cf, Tests: 1.5h*cf)
    CoreImpact-->>UI: Returns ImpactAnalysisResult (Blast radius + Effort breakdown)
    deactivate CoreImpact

    %% Step 4: Render Interactive Visualization
    UI->>CoreGraph: build_traceability_graph(project)
    UI->>CoreGraph: generate_pyvis_html(nx_graph, highlight_nodes)
    CoreGraph-->>UI: Returns Interactive Vis.js HTML String
    UI->>PyVisNet: Embeds PyVis Network via iframe
    UI-->>User: Renders Interactive Graph, Blast Radius & Effort Table
    deactivate UI

    %% Step 5: User Confirms & Commits
    User->>UI: Reviews Blast Radius & Clicks "Apply Change"
    activate UI

    UI->>CoreImpact: apply_change_commit(project, "R2", new_text, impact_result)
    activate CoreImpact
    
    CoreImpact->>Models: req.update_text(new_text) [Bumps v2->v3, Status='Changed', Logs History]
    loop For Each Impacted Test Case
        CoreImpact->>Models: tc.status = "Needs Review"
    end
    deactivate CoreImpact

    UI->>Storage: save_project(project)
    Storage->>Storage: Atomic JSON write (.tmp -> rename to project.json)
    Storage-->>UI: Persistence Confirmed
    UI-->>User: Renders Success Alert (v3 committed, tests flagged Needs Review)
    deactivate UI
```
