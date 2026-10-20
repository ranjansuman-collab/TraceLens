"""
Unit tests for core domain models.
"""

import pytest
from core.models import Requirement, DesignElement, TestCase, Project, RequirementHistoryEntry


def test_requirement_creation_and_clamping():
    """Verify requirement boundary invariants and field initialization."""
    req = Requirement(
        id="R100",
        text="The system shall validate tokens.",
        type="Functional",
        priority="High",
        impact=10,      # should clamp to 5
        complexity=-2,   # should clamp to 1
        version=0,      # should clamp to 1
        change_count=-5 # should clamp to 0
    )
    assert req.impact == 5
    assert req.complexity == 1
    assert req.version == 1
    assert req.change_count == 0
    assert len(req.history) == 1
    assert req.history[0].version == 1


def test_requirement_update_and_versioning():
    """Verify version increment and history tracking on text update."""
    req = Requirement(id="R1", text="The system shall log in users.")
    initial_ver = req.version
    req.update_text("The system shall authenticate users with password.")
    assert req.version == initial_ver + 1
    assert req.change_count == 1
    assert req.status == "Changed"
    assert len(req.history) == 2
    assert req.history[-1].text == "The system shall authenticate users with password."


def test_requirement_version_restore():
    """Verify restoring a historical version."""
    req = Requirement(id="R1", text="Version 1 text.")
    req.update_text("Version 2 text.")
    req.update_text("Version 3 text.")
    assert req.version == 3

    success = req.restore_version(1)
    assert success is True
    assert req.version == 4
    assert req.text == "Version 1 text."
    assert req.change_count == 3


def test_design_element_and_test_case():
    """Verify DesignElement and TestCase models."""
    des = DesignElement(id="D1", name="AuthModule", kind="Module", linked_reqs=["R1", "R1", "R2"])
    assert len(des.linked_reqs) == 2  # unique

    tc = TestCase(
        id="T1",
        title="Test Login",
        steps=["Step 1", "Step 2"],
        expected="Success",
        type="Unit",
        linked_req="R1",
        status="Pass"
    )
    assert tc.type == "Unit"
    assert tc.status == "Pass"
    assert len(tc.steps) == 2


def test_project_roundtrip_serialization():
    """Verify Project serialization and deserialization."""
    project = Project(
        name="Demo App",
        requirements=[Requirement(id="R1", text="The system shall verify cards.")],
        design_elements=[DesignElement(id="D1", name="PaymentService", kind="Module", linked_reqs=["R1"])],
        test_cases=[TestCase(id="T1", title="Card charge", steps=["Charge $10"], expected="OK", linked_req="R1")]
    )
    data = project.to_dict()
    restored = Project.from_dict(data)
    assert restored.name == "Demo App"
    assert len(restored.requirements) == 1
    assert restored.get_requirement("R1") is not None
    assert len(restored.get_design_for_requirement("R1")) == 1
    assert len(restored.get_tests_for_requirement("R1")) == 1
