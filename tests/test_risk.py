"""
Unit tests for risk calculation, test execution sorting, and RMMM table generation.
"""

from core.models import Project, Requirement, TestCase
from core.risk import (
    calculate_requirement_risk,
    get_prioritized_test_cases,
    get_uncovered_requirements_by_risk,
    generate_rmmm_table,
)


def test_calculate_requirement_risk():
    """Verify formula: Impact * Complexity * (1 + Change_Count)."""
    req = Requirement(id="R1", text="Test", impact=4, complexity=5, change_count=2)
    # 4 * 5 * (1 + 2) = 60
    assert calculate_requirement_risk(req) == 60.0


def test_test_case_prioritization_by_risk():
    """Verify tests are sorted descending by linked requirement risk."""
    r_high = Requirement(id="R_HIGH", text="High risk", impact=5, complexity=5, change_count=1) # 50
    r_low = Requirement(id="R_LOW", text="Low risk", impact=1, complexity=1, change_count=0)   # 1
    t_high = TestCase(id="T_H", title="High test", steps=["S1"], expected="E1", linked_req="R_HIGH")
    t_low = TestCase(id="T_L", title="Low test", steps=["S2"], expected="E2", linked_req="R_LOW")

    proj = Project(
        requirements=[r_low, r_high],
        test_cases=[t_low, t_high]
    )
    sorted_tests = get_prioritized_test_cases(proj)
    assert sorted_tests[0]["test_id"] == "T_H"
    assert sorted_tests[0]["risk_score"] == 50.0
    assert sorted_tests[1]["test_id"] == "T_L"
    assert sorted_tests[1]["risk_score"] == 1.0


def test_uncovered_requirements_by_risk():
    """Verify uncovered requirements list is ranked by risk score."""
    r1 = Requirement(id="R1", text="Req 1", impact=4, complexity=4, change_count=0) # 16
    r2 = Requirement(id="R2", text="Req 2", impact=5, complexity=5, change_count=0) # 25
    t1 = TestCase(id="T1", title="Test 1", steps=["S1"], expected="E1", linked_req="R1")

    proj = Project(requirements=[r1, r2], test_cases=[t1])
    uncovered = get_uncovered_requirements_by_risk(proj)
    assert len(uncovered) == 1
    assert uncovered[0]["req_id"] == "R2"
    assert uncovered[0]["risk_score"] == 25.0


def test_rmmm_table_generation():
    """Verify top-5 RMMM table generation."""
    reqs = [
        Requirement(id=f"R{i}", text=f"Req {i}", impact=i % 5 + 1, complexity=i % 5 + 1)
        for i in range(1, 10)
    ]
    proj = Project(requirements=reqs)
    rmmm = generate_rmmm_table(proj)
    assert len(rmmm) == 5
    assert rmmm[0].risk_id == "RSK-01"
    assert rmmm[0].risk_score >= rmmm[1].risk_score
    assert len(rmmm[0].mitigation) > 0
    assert len(rmmm[0].monitoring) > 0
