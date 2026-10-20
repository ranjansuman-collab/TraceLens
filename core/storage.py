"""
Storage layer for TraceLens.
Handles thread-safe, atomic JSON persistence for local project data.
"""

from __future__ import annotations
import json
import os
import shutil
from pathlib import Path
from typing import Optional

from core.models import Project

# Default file locations
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROJECT_FILE = DATA_DIR / "project.json"
SAMPLE_FILE = DATA_DIR / "sample_project.json"


def ensure_data_dir() -> Path:
    """Ensure data directory exists and return Path."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def load_project(custom_path: Optional[Path] = None) -> Project:
    """
    Load project from local JSON file.
    If project.json does not exist, copies from sample_project.json or creates a default.
    """
    ensure_data_dir()
    target_path = custom_path or PROJECT_FILE

    if not target_path.exists():
        if SAMPLE_FILE.exists():
            shutil.copyfile(SAMPLE_FILE, target_path)
        else:
            # Fallback default project
            empty_project = Project()
            save_project(empty_project, target_path)
            return empty_project

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Project.from_dict(data)
    except (json.JSONDecodeError, OSError) as err:
        # If file is corrupted, fall back to sample or clean instance
        if SAMPLE_FILE.exists() and target_path != SAMPLE_FILE:
            shutil.copyfile(SAMPLE_FILE, target_path)
            with open(target_path, "r", encoding="utf-8") as f:
                return Project.from_dict(json.load(f))
        return Project()


def save_project(project: Project, custom_path: Optional[Path] = None) -> None:
    """
    Atomically persist the project to JSON to prevent corruption.
    """
    ensure_data_dir()
    target_path = custom_path or PROJECT_FILE
    temp_path = target_path.with_suffix(".tmp")

    payload = project.to_dict()
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Atomic replace
    os.replace(temp_path, target_path)


def reset_to_sample_data(custom_path: Optional[Path] = None) -> Project:
    """
    Reset data/project.json back to initial sample_project.json data.
    """
    ensure_data_dir()
    target_path = custom_path or PROJECT_FILE
    if SAMPLE_FILE.exists():
        shutil.copyfile(SAMPLE_FILE, target_path)
    return load_project(target_path)


QUALITY_HISTORY_FILE = DATA_DIR / "quality_history.json"


def record_quality_snapshot(
    composite: float,
    test_coverage: float,
    clarity: float,
    stability: float,
    design_coverage: float,
    project_name: str = "",
) -> None:
    """
    Append a timestamped quality snapshot to data/quality_history.json.
    Keeps up to last 100 snapshots.
    """
    ensure_data_dir()
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    snapshots = []
    if QUALITY_HISTORY_FILE.exists():
        try:
            with open(QUALITY_HISTORY_FILE, "r", encoding="utf-8") as f:
                snapshots = json.load(f)
        except Exception:
            snapshots = []

    # Avoid duplicate rapid logging within same minute
    if snapshots and snapshots[-1].get("timestamp", "").startswith(now_iso[:16]):
        # Update last record
        snapshots[-1].update({
            "timestamp": now_iso,
            "composite": composite,
            "test_coverage": test_coverage,
            "clarity": clarity,
            "stability": stability,
            "design_coverage": design_coverage,
            "project_name": project_name,
        })
    else:
        snapshots.append({
            "timestamp": now_iso,
            "composite": composite,
            "test_coverage": test_coverage,
            "clarity": clarity,
            "stability": stability,
            "design_coverage": design_coverage,
            "project_name": project_name,
        })

    # Keep at most 100 snapshots
    if len(snapshots) > 100:
        snapshots = snapshots[-100:]

    temp_path = QUALITY_HISTORY_FILE.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(snapshots, f, indent=2)
    os.replace(temp_path, QUALITY_HISTORY_FILE)


def get_quality_history() -> list[dict[str, Any]]:
    """Retrieve recorded quality snapshots."""
    if not QUALITY_HISTORY_FILE.exists():
        return []
    try:
        with open(QUALITY_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def list_available_projects() -> list[str]:
    """
    List all JSON project filenames stored in data directory.
    Excludes sample_project.json and quality_history.json.
    """
    ensure_data_dir()
    names = []
    for p in DATA_DIR.glob("*.json"):
        if p.name not in ("sample_project.json", "quality_history.json") and not p.name.endswith(".tmp"):
            names.append(p.name)
    if "project.json" not in names:
        names.insert(0, "project.json")
    return sorted(list(set(names)))


def create_new_project(name: str, filename: str) -> Project:
    """
    Create a new empty project file with given name and filename.
    """
    ensure_data_dir()
    safe_filename = filename if filename.endswith(".json") else f"{filename}.json"
    safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._-")
    target_path = DATA_DIR / safe_filename

    new_proj = Project(
        name=name,
        version="1.0.0",
        description=f"TraceLens Project: {name}",
        requirements=[],
        design_elements=[],
        test_cases=[],
    )
    save_project(new_proj, target_path)
    return new_proj

