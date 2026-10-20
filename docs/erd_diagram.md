# TraceLens Data Architecture Entity-Relationship Diagram (ERD)

This document visualizes the entities, properties, and relationships stored within the local TraceLens JSON data model (`project.json`).

```mermaid
erDiagram
    PROJECT ||--|{ REQUIREMENT : contains
    PROJECT ||--|{ DESIGN_ELEMENT : contains
    PROJECT ||--|{ TEST_CASE : contains
    REQUIREMENT ||--|{ REQUIREMENT_HISTORY : maintains
    REQUIREMENT }|..|{ DESIGN_ELEMENT : implemented_by
    REQUIREMENT ||--|{ TEST_CASE : verified_by
    DESIGN_ELEMENT }|..|{ TEST_CASE : covered_by

    PROJECT {
        string name
        string version
        string description
    }

    REQUIREMENT {
        string id PK "e.g. R1, R2"
        string text "Normative IEEE requirement statement"
        string type "Functional | Non-Functional"
        string priority "High | Medium | Low"
        int impact "1-5 scale"
        int complexity "1-5 scale"
        int version "Current version counter"
        int change_count "Revisions counter"
        string status "Draft | Approved | Changed"
    }

    REQUIREMENT_HISTORY {
        int version "Snapshot version number"
        string text "Historical requirement text"
        string timestamp "UTC ISO 8601 timestamp"
    }

    DESIGN_ELEMENT {
        string id PK "e.g. D1, D2"
        string name "Component or schema name"
        string kind "Module | Class | API | DB Table"
        list linked_reqs "Foreign keys to Requirement IDs"
    }

    TEST_CASE {
        string id PK "e.g. T1, T2"
        string title "Short verification objective"
        list steps "Ordered procedural verification actions"
        string expected "Assertion outcome"
        string type "Unit | Integration | System | Acceptance"
        string linked_req FK "Reference to verified Requirement ID"
        string status "Not Run | Pass | Fail | Needs Review"
        boolean auto_generated "AI / template synthesized flag"
        string defect_notes "Bug details or reproduction steps"
        string execution_comment "Tester observations or env info"
        string defect_severity "None | Low | Medium | High | Critical"
    }
```

## Traceability Invariants

1. **Requirement Integrity:** Each requirement maintains an append-only `history` list of immutable version snapshots.
2. **Design Bidirectionality:** Design elements reference requirements via `linked_reqs`; the traceability engine projects bidirectional edges into the NetworkX graph.
3. **Verification Linkage:** Every test case specifies `linked_req` referencing exactly one requirement. Orphaned tests (`linked_req = ""`) are highlighted during quality audits.
4. **Defect Tracking:** Tests in `Fail` status record severity and actionable defect notes directly on the test entity.
