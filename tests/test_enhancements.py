"""
Unit tests for TraceLens enhancements:
- Duplicate detection
- Completeness scoring
- 8-characteristic ISO 25010 mapping
- Semantic conflict analyzer and AI suggestions
- Multi-project management and quality history recording
- Requirement dependency graph construction
"""

import pytest
from pathlib import Path
from core.models import Project, Requirement, DesignElement, TestCase
from core.linter import detect_duplicates, RequirementDuplicate
from core.scoring import calculate_requirement_completeness, calculate_all_completeness, calculate_quality_health
from core.ai_client import analyze_conflict_ai, suggest_requirement_ai, generate_rmmm_mitigation_ai
from core.storage import record_quality_snapshot, get_quality_history, list_available_projects, create_new_project
from core.graph import build_requirement_dependency_graph


def test_duplicate_detection():
    """Verify duplicate / overlap detection detects highly similar requirements."""
    r1 = Requirement(id="R101", text="The system shall process user payments through Stripe securely within 2 seconds.")
    r2 = Requirement(id="R102", text="The system shall process customer payments via Stripe securely within 2 seconds.")
    r3 = Requirement(id="R103", text="The system shall display restaurant menus with high resolution images.")

    dups = detect_duplicates([r1, r2, r3], threshold=0.75)
    assert len(dups) >= 1
    pair = dups[0]
    assert pair.req1_id == "R101"
    assert pair.req2_id == "R102"
    assert pair.similarity >= 0.75


def test_requirement_completeness():
    """Verify completeness scores based on test, design, measurability, and approval."""
    req_full = Requirement(id="R1", text="The system shall respond within 2.0 seconds.", status="Approved")
    des = DesignElement(id="D1", name="API", kind="API", linked_reqs=["R1"])
    tc = TestCase(id="T1", title="Test 1", steps=["Step 1"], expected="200 OK", linked_req="R1", status="Pass")

    proj = Project(
        requirements=[req_full],
        design_elements=[des],
        test_cases=[tc],
    )

    comp = calculate_requirement_completeness(proj, req_full)
    assert comp.score == 100.0
    assert comp.has_test is True
    assert comp.has_design is True
    assert comp.has_measurable is True
    assert comp.is_approved is True
    assert len(comp.missing) == 0

    # Incomplete req
    req_partial = Requirement(id="R2", text="The system must be flexible.", status="Draft")
    comp_partial = calculate_requirement_completeness(proj, req_partial)
    assert comp_partial.score == 0.0
    assert len(comp_partial.missing) == 4


def test_iso_25010_all_factors():
    """Verify all 8 ISO 25010 characteristics + Testability are evaluated."""
    req1 = Requirement(id="R1", text="The system shall authenticate users within 1.5 seconds.", priority="High")
    des1 = DesignElement(id="D1", name="AuthModule", kind="Module", linked_reqs=["R1"])
    tc1 = TestCase(id="T1", title="Auth Test", steps=["Login"], expected="Success", linked_req="R1", status="Pass")

    proj = Project(requirements=[req1], design_elements=[des1], test_cases=[tc1])
    report = calculate_quality_health(proj)

    factor_names = [f.factor for f in report.iso_factors]
    assert len(factor_names) >= 8
    assert any("Functional Suitability" in fn for fn in factor_names)
    assert any("Performance Efficiency" in fn for fn in factor_names)
    assert any("Compatibility" in fn for fn in factor_names)
    assert any("Usability" in fn for fn in factor_names)
    assert any("Reliability" in fn for fn in factor_names)
    assert any("Security" in fn for fn in factor_names)
    assert any("Maintainability" in fn for fn in factor_names)
    assert any("Portability" in fn for fn in factor_names)
    assert any("Testability" in fn for fn in factor_names)


def test_ai_conflict_analyzer_fallback():
    """Verify analyze_conflict_ai works deterministically without API key."""
    r1 = Requirement(id="R1", text="The customer may complete orders as an anonymous guest without logging in.")
    r2 = Requirement(id="R2", text="The system mandates verified user authentication before order placement.")

    res, is_mock = analyze_conflict_ai(r1, r2)
    assert res["conflict_detected"] is True
    assert "contradiction" in res["explanation"].lower() or "authentication" in res["explanation"].lower()
    assert len(res["resolution"]) > 0


def test_ai_suggest_requirement_fallback():
    """Verify suggest_requirement_ai returns clean IEEE statements in mock mode."""
    stmt, is_mock = suggest_requirement_ai("payment via Stripe card tokenization", "Functional")
    assert "shall" in stmt.lower()
    assert "system" in stmt.lower() or "payment" in stmt.lower()


def test_ai_rmmm_mitigation_fallback():
    """Verify generate_rmmm_mitigation_ai produces actionable plan."""
    req = Requirement(id="R2", text="The system shall charge credit cards via Stripe API within 2 seconds.", impact=5, complexity=4)
    res, is_mock = generate_rmmm_mitigation_ai(req)
    assert "title" in res
    assert "mitigation" in res
    assert "monitoring" in res


def test_quality_history_storage(tmp_path):
    """Verify quality history snapshot logging and retrieval."""
    record_quality_snapshot(85.0, 90.0, 80.0, 95.0, 75.0, project_name="TestProj")
    history = get_quality_history()
    assert len(history) >= 1
    last = history[-1]
    assert last["composite"] == 85.0


def test_req_dependency_graph():
    """Verify build_requirement_dependency_graph correctly links shared elements."""
    r1 = Requirement(id="R1", text="Req 1")
    r2 = Requirement(id="R2", text="Req 2")
    des = DesignElement(id="D1", name="SharedModule", kind="Module", linked_reqs=["R1", "R2"])

    proj = Project(requirements=[r1, r2], design_elements=[des])
    g = build_requirement_dependency_graph(proj)

    assert g.has_node("R1")
    assert g.has_node("R2")
    assert g.has_edge("R1", "R2")
    edge_data = g.get_edge_data("R1", "R2")
    assert "Shared Design" in edge_data["relation"]


def test_testcase_defect_fields():
    """Verify defect_notes and severity serialization."""
    tc = TestCase(
        id="T99",
        title="Sample Test",
        steps=["Step 1"],
        expected="Result",
        status="Fail",
        defect_notes="Null pointer exception on line 42",
        defect_severity="Critical",
        execution_comment="Tested on Chrome 120",
    )
    d = tc.to_dict()
    assert d["defect_notes"] == "Null pointer exception on line 42"
    assert d["defect_severity"] == "Critical"
    assert d["execution_comment"] == "Tested on Chrome 120"

    tc_deser = TestCase.from_dict(d)
    assert tc_deser.defect_severity == "Critical"
    assert tc_deser.defect_notes == "Null pointer exception on line 42"
