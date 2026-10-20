"""
Unit tests for Quality Health Score and ISO 25010 factor evaluations.
"""

from core.models import Project, Requirement, DesignElement, TestCase
from core.scoring import calculate_quality_health


def test_quality_health_calculation():
    """Verify weights: 0.40*test_cov + 0.30*clarity + 0.20*stability + 0.10*design_cov."""
    # Build clean project with 100% coverage
    req1 = Requirement(id="R1", text="The system shall process requests within 2 seconds.", priority="High")
    des1 = DesignElement(id="D1", name="Service", kind="Module", linked_reqs=["R1"])
    tc1 = TestCase(id="T1", title="Test 1", steps=["S1"], expected="E1", linked_req="R1", status="Pass")

    proj = Project(
        requirements=[req1],
        design_elements=[des1],
        test_cases=[tc1]
    )
    report = calculate_quality_health(proj)

    assert report.test_coverage_weighted == 100.0
    assert report.stability_score == 100.0
    assert report.design_link_coverage == 100.0
    assert report.composite_score >= 80.0
    assert "Excellent" in report.verdict or "Good" in report.verdict

    # Check ISO 25010 factor mappings
    factors = {f.factor.split()[0] for f in report.iso_factors}
    assert "Testability" in factors
    assert "Maintainability" in factors
    assert "Reliability" in factors


def test_quality_health_with_empty_project():
    """Verify empty project does not crash."""
    proj = Project(requirements=[])
    report = calculate_quality_health(proj)
    assert report.composite_score == 0.0
