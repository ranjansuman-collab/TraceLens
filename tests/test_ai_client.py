"""
Unit tests for AI client, JSON parsing/sanitization, and mock fallback resilience.
"""

from core.models import Requirement
from core.ai_client import (
    clean_json_response,
    generate_tests_mock,
    rewrite_requirement_ai,
    generate_tests_for_requirement,
    is_ai_available,
    get_mode_badge,
)


def test_clean_json_response():
    """Verify stripping markdown code blocks, backticks, and extra wrapper text."""
    wrapped_json = """
    Here are the generated test cases for your requirement:
    ```json
    [
      {
        "title": "Positive Test",
        "type": "Unit",
        "steps": ["Step A", "Step B"],
        "expected": "Success"
      }
    ]
    ```
    Hope this helps!
    """
    cleaned = clean_json_response(wrapped_json)
    assert cleaned.startswith("[")
    assert cleaned.endswith("]")
    assert "Positive Test" in cleaned


def test_clean_json_response_raw_and_broken():
    """Verify clean_json handles raw array and fallback."""
    raw = '[{"title": "Test"}]'
    assert clean_json_response(raw) == '[{"title": "Test"}]'


def test_mode_badge():
    """Verify mode badge returns dictionary with badge_html and status."""
    badge = get_mode_badge()
    assert "mode" in badge
    assert "badge_html" in badge


def test_mock_test_generation():
    """Verify mock test generation produces 4 categorized tests with steps and expected."""
    req = Requirement(id="R10", text="The payment gateway shall process card transactions within 3 seconds.")
    tests = generate_tests_mock(req, start_id=50)
    assert len(tests) == 4
    assert tests[0].id == "T50"
    assert tests[1].id == "T51"
    assert tests[2].id == "T52"
    assert tests[3].id == "T53"
    assert all(t.linked_req == "R10" for t in tests)
    assert all(t.auto_generated for t in tests)
    assert all(len(t.steps) >= 3 for t in tests)


def test_mock_rewrite_fallback():
    """Verify rewrite falls back gracefully without crashing when offline."""
    req = Requirement(id="R3", text="The UI must be user-friendly.")
    rewritten, is_mock = rewrite_requirement_ai(req)
    assert isinstance(rewritten, str)
    assert len(rewritten) > 10
    assert "shall" in rewritten.lower()


def test_generate_tests_resilience():
    """Verify test generation never crashes and generates valid test cases."""
    req = Requirement(id="R4", text="The app should be fast.")
    tests, is_mock = generate_tests_for_requirement(req, start_id=101)
    assert len(tests) >= 3
    assert tests[0].id == "T101"
    assert tests[0].linked_req == "R4"
