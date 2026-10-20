"""
Unit tests for Requirement Quality Linter and Conflict Detector.
"""

from core.models import Requirement
from core.linter import lint_requirement, detect_conflicts, generate_template_rewrite, compute_diff


def test_high_quality_requirement():
    """Verify clean, quantified requirement scores green (>= 80)."""
    req = Requirement(
        id="R1",
        text="The system shall process customer payments within 3 seconds and return a receipt."
    )
    result = lint_requirement(req)
    assert result.score >= 80
    assert result.grade == "Green"


def test_vague_terms_penalty():
    """Verify vague term penalties (-15 each)."""
    req = Requirement(id="R2", text="The app should be fast and user-friendly.")
    result = lint_requirement(req)
    vague_rules = [i for i in result.issues if i.category == "Vagueness"]
    assert len(vague_rules) >= 2  # 'fast' and 'user-friendly'
    assert result.score < 80


def test_missing_shall_and_unquantifiable_penalties():
    """Verify missing 'shall' (-10) and missing number (-20) penalties."""
    req = Requirement(id="R3", text="The UI must look nice.")
    result = lint_requirement(req)
    categories = {i.category for i in result.issues}
    assert "Syntax" in categories       # Missing 'shall'
    assert "Measurability" in categories # No numbers or criteria


def test_compound_requirement_penalty():
    """Verify compound requirement penalty with multiple and/or (-10)."""
    req = Requirement(
        id="R4",
        text="The driver shall accept tasks and the system shall notify the kitchen and the client shall receive SMS."
    )
    result = lint_requirement(req)
    categories = {i.category for i in result.issues}
    assert "Structure" in categories


def test_conflict_detection():
    """Verify conflict detection between guest checkout and mandatory authentication."""
    r1 = Requirement(id="R6", text="The customer shall be permitted to checkout as an anonymous guest without logging in.")
    r2 = Requirement(id="R7", text="The system shall require mandatory user authentication and verified phone registration.")
    conflicts = detect_conflicts([r1, r2])
    assert len(conflicts) >= 1
    assert conflicts[0].severity == "High"
    assert "R6" in (conflicts[0].req1_id, conflicts[0].req2_id)
    assert "R7" in (conflicts[0].req1_id, conflicts[0].req2_id)


def test_template_rewrite_and_diff():
    """Verify template rewrite resolves issues and diff generates unified output."""
    req = Requirement(id="R4", text="The app should be fast.")
    rewritten = generate_template_rewrite(req)
    assert "shall" in rewritten.lower()
    assert any(c.isdigit() for c in rewritten)  # Has numbers

    # Verify score improves
    new_req = Requirement(id="R4", text=rewritten)
    new_result = lint_requirement(new_req)
    orig_result = lint_requirement(req)
    assert new_result.score > orig_result.score

    # Diff test
    diff = compute_diff(req.text, rewritten)
    assert len(diff) > 0
    assert "Original" in diff
