# TraceLens Requirement Configuration Management (CM) State Machine

This document models the lifecycle states and transitions of a software requirement artifact within TraceLens.

```mermaid
stateDiagram-v2
    [*] --> Draft : Requirement Created (v1)

    Draft --> Approved : Quality Lint Passed (Score >= 80) & Peer Review Signed Off
    Draft --> Draft : Text Refined / AI Rewritten

    Approved --> Changed : Modification Committed / Baseline Churn Detected (v + 1)
    
    state Changed {
        [*] --> ImpactAssessment : BFS Blast Radius Evaluated
        ImpactAssessment --> StaleTestsFlagged : Downstream Tests Marked Needs Review
        StaleTestsFlagged --> VerificationReady : Tests Updated or Regressed
    }

    Changed --> Approved : Regression Testing Passes & Change Approved
    Changed --> Draft : Reverted for Major Redrafting

    Approved --> Changed : Historical Version Rollback (v + 1, history appended)
    Draft --> [*] : Deleted from Project
    Changed --> [*] : Deleted from Project
```

## Lifecycle States Explanation

| State | Description | Permitted Actions |
|---|---|---|
| **Draft** | Initial authored requirement statement. Not yet formally approved or tested. | Edit text, run AI rewrite, run quality linter, delete. |
| **Approved** | Baselined requirement that has passed quality linting and is linked to architecture and verification tests. | Link design elements, link test cases, trigger impact simulation. |
| **Changed** | Modified requirement whose previous baseline was changed. Triggers blast-radius analysis across connected design elements and test cases. | Run BFS impact simulation, review test regressions, rollback to prior version, re-approve. |
