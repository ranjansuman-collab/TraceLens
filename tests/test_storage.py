"""
Unit tests for storage layer and atomic JSON persistence.
"""

from pathlib import Path
from core.models import Project, Requirement
from core.storage import load_project, save_project, reset_to_sample_data, SAMPLE_FILE


def test_load_sample_project(tmp_path: Path):
    """Verify loading from sample project file."""
    assert SAMPLE_FILE.exists()
    proj = load_project(SAMPLE_FILE)
    assert len(proj.requirements) == 12
    assert len(proj.design_elements) == 8
    assert len(proj.test_cases) == 14


def test_save_and_reload_atomic(tmp_path: Path):
    """Verify atomic write and reload."""
    test_file = tmp_path / "test_project.json"
    proj = Project(name="Custom Project", requirements=[Requirement(id="R99", text="The system shall save data.")])
    save_project(proj, test_file)

    loaded = load_project(test_file)
    assert loaded.name == "Custom Project"
    assert len(loaded.requirements) == 1
    assert loaded.requirements[0].id == "R99"


def test_reset_to_sample(tmp_path: Path):
    """Verify reset function reverts to original sample state."""
    target_file = tmp_path / "project.json"
    reset_proj = reset_to_sample_data(target_file)
    assert len(reset_proj.requirements) == 12
    assert target_file.exists()
