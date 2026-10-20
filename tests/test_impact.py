"""
Unit tests for BFS change impact simulation and effort estimation.
"""

from core.models import Project, Requirement, DesignElement, TestCase
from core.impact import simulate_change_impact, apply_change_commit


def test_bfs_impact_analysis():
    """Verify blast radius detection for changed requirement and siblings."""
    proj = Project(
        requirements=[
            Requirement(id="R1", text="Req 1", complexity=3),
            Requirement(id="R2", text="Req 2 (sibling sharing D1)", complexity=3),
            Requirement(id="R3", text="Req 3 (unrelated)", complexity=3),
        ],
        design_elements=[
            DesignElement(id="D1", name="SharedModule", kind="Module", linked_reqs=["R1", "R2"]),
            DesignElement(id="D2", name="UnrelatedModule", kind="Module", linked_reqs=["R3"]),
        ],
        test_cases=[
            TestCase(id="T1", title="Test for R1", steps=["S1"], expected="E1", linked_req="R1", status="Pass"),
            TestCase(id="T2", title="Test for R2", steps=["S2"], expected="E2", linked_req="R2", status="Pass"),
            TestCase(id="T3", title="Test for R3", steps=["S3"], expected="E3", linked_req="R3", status="Pass"),
        ]
    )

    result = simulate_change_impact(proj, "R1")
    assert result.changed_req_id == "R1"
    assert "D1" in result.impacted_design_elements
    assert "R2" in result.impacted_requirements  # Sibling requirement identified!
    assert "T1" in result.impacted_test_cases
    assert "T2" in result.impacted_test_cases  # Test for sibling also impacted!
    assert "R3" in result.unaffected_nodes
    assert "D2" in result.unaffected_nodes
    assert "T3" in result.unaffected_nodes

    # Colors
    assert result.node_color_map["R1"] == "#EF4444"  # Red
    assert result.node_color_map["D1"] == "#F97316"  # Orange
    assert result.node_color_map["T1"] == "#FACC15"  # Yellow

    # Effort calculation check (complexity=3 -> factor 1.0)
    # D1 (1 design) -> 4.0h, code (1 design) -> 6.0h, tests (2 tests) -> 2 * 1.5 = 3.0h. Total = 13.0h
    assert result.total_effort_hours > 0


def test_apply_change_commit():
    """Verify applying change updates requirement and marks impacted tests as Needs Review."""
    proj = Project(
        requirements=[Requirement(id="R1", text="Old text", version=1)],
        design_elements=[DesignElement(id="D1", name="Mod1", kind="Module", linked_reqs=["R1"])],
        test_cases=[TestCase(id="T1", title="Test 1", steps=["S1"], expected="E1", linked_req="R1", status="Pass")]
    )
    impact = simulate_change_impact(proj, "R1")
    apply_change_commit(proj, "R1", "New updated text", impact)

    req = proj.get_requirement("R1")
    assert req.text == "New updated text"
    assert req.version == 2
    assert req.status == "Changed"

    tc = proj.get_test_case("T1")
    assert tc.status == "Needs Review"
