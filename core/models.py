"""
Domain models for TraceLens.
Defines requirements, design elements, test cases, and the composite project model.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


def get_current_utc_timestamp() -> str:
    """Return ISO format UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RequirementHistoryEntry:
    """Historical snapshot of a requirement version."""
    version: int
    text: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "version": self.version,
            "text": self.text,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RequirementHistoryEntry:
        """Create entry from dictionary."""
        return cls(
            version=int(data.get("version", 1)),
            text=str(data.get("text", "")),
            timestamp=str(data.get("timestamp", get_current_utc_timestamp())),
        )


@dataclass
class Requirement:
    """
    Software requirement representation.
    Supports versioning, impact assessment, and change auditing.
    """
    id: str
    text: str
    type: str = "Functional"  # "Functional" | "Non-Functional"
    priority: str = "Medium"  # "High" | "Medium" | "Low"
    impact: int = 3           # 1-5
    complexity: int = 3       # 1-5
    version: int = 1
    change_count: int = 0
    status: str = "Approved"  # "Draft" | "Approved" | "Changed"
    history: List[RequirementHistoryEntry] = field(default_factory=list)

    def __post_init__(self):
        """Ensure boundary invariants."""
        self.impact = max(1, min(5, int(self.impact)))
        self.complexity = max(1, min(5, int(self.complexity)))
        self.version = max(1, int(self.version))
        self.change_count = max(0, int(self.change_count))
        if self.type not in ("Functional", "Non-Functional"):
            self.type = "Functional"
        if self.priority not in ("High", "Medium", "Low"):
            self.priority = "Medium"
        if self.status not in ("Draft", "Approved", "Changed"):
            self.status = "Draft"
        # Seed history if empty
        if not self.history:
            self.history = [
                RequirementHistoryEntry(
                    version=self.version,
                    text=self.text,
                    timestamp=get_current_utc_timestamp(),
                )
            ]

    def update_text(self, new_text: str, mark_changed: bool = True) -> None:
        """
        Update the requirement text, incrementing version and appending history.
        """
        stripped_new = new_text.strip()
        if stripped_new == self.text.strip():
            return

        self.version += 1
        self.change_count += 1
        self.text = stripped_new
        if mark_changed:
            self.status = "Changed"
        self.history.append(
            RequirementHistoryEntry(
                version=self.version,
                text=self.text,
                timestamp=get_current_utc_timestamp(),
            )
        )

    def restore_version(self, target_version: int) -> bool:
        """
        Restore requirement text to a previous historical version.
        Increments version and adds a new history entry documenting the restoration.
        """
        target_entry = next((h for h in self.history if h.version == target_version), None)
        if not target_entry:
            return False

        self.version += 1
        self.change_count += 1
        self.text = target_entry.text
        self.status = "Changed"
        self.history.append(
            RequirementHistoryEntry(
                version=self.version,
                text=self.text,
                timestamp=get_current_utc_timestamp(),
            )
        )
        return True

    def calculate_risk_score(self) -> float:
        """
        Calculate raw risk metric: impact * complexity * (1 + change_count).
        """
        return float(self.impact * self.complexity * (1 + self.change_count))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize requirement to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "type": self.type,
            "priority": self.priority,
            "impact": self.impact,
            "complexity": self.complexity,
            "version": self.version,
            "change_count": self.change_count,
            "status": self.status,
            "history": [h.to_dict() for h in self.history],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Requirement:
        """Deserialize requirement from dictionary."""
        history_raw = data.get("history", [])
        history_entries = [RequirementHistoryEntry.from_dict(h) for h in history_raw]
        return cls(
            id=str(data.get("id", "")),
            text=str(data.get("text", "")),
            type=str(data.get("type", "Functional")),
            priority=str(data.get("priority", "Medium")),
            impact=int(data.get("impact", 3)),
            complexity=int(data.get("complexity", 3)),
            version=int(data.get("version", 1)),
            change_count=int(data.get("change_count", 0)),
            status=str(data.get("status", "Approved")),
            history=history_entries,
        )


@dataclass
class DesignElement:
    """
    Architectural or design element linked to requirements.
    Kinds: Module, Class, API, DB Table.
    """
    id: str
    name: str
    kind: str = "Module"  # "Module" | "Class" | "API" | "DB Table"
    linked_reqs: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate kind."""
        valid_kinds = ("Module", "Class", "API", "DB Table")
        if self.kind not in valid_kinds:
            self.kind = "Module"
        self.linked_reqs = list(set(self.linked_reqs))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize design element."""
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "linked_reqs": self.linked_reqs,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DesignElement:
        """Deserialize design element."""
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            kind=str(data.get("kind", "Module")),
            linked_reqs=list(data.get("linked_reqs", [])),
        )


@dataclass
class TestCase:
    """
    Test case linked to a requirement.
    Types: Unit, Integration, System, Acceptance.
    Statuses: Not Run, Pass, Fail, Needs Review.
    """
    __test__ = False  # Instruct pytest not to collect this domain model as a test suite

    id: str
    title: str
    steps: List[str]
    expected: str
    type: str = "System"  # "Unit" | "Integration" | "System" | "Acceptance"
    linked_req: str = ""
    status: str = "Not Run"  # "Not Run" | "Pass" | "Fail" | "Needs Review"
    auto_generated: bool = False
    defect_notes: str = ""
    execution_comment: str = ""
    defect_severity: str = "None"  # "None" | "Low" | "Medium" | "High" | "Critical"

    def __post_init__(self):
        """Validate test type and status."""
        valid_types = ("Unit", "Integration", "System", "Acceptance")
        if self.type not in valid_types:
            self.type = "System"
        valid_statuses = ("Not Run", "Pass", "Fail", "Needs Review")
        if self.status not in valid_statuses:
            self.status = "Not Run"
        valid_severities = ("None", "Low", "Medium", "High", "Critical")
        if self.defect_severity not in valid_severities:
            self.defect_severity = "None"
        if isinstance(self.steps, str):
            self.steps = [s.strip() for s in self.steps.split("\n") if s.strip()]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize test case."""
        return {
            "id": self.id,
            "title": self.title,
            "steps": self.steps,
            "expected": self.expected,
            "type": self.type,
            "linked_req": self.linked_req,
            "status": self.status,
            "auto_generated": self.auto_generated,
            "defect_notes": self.defect_notes,
            "execution_comment": self.execution_comment,
            "defect_severity": self.defect_severity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TestCase:
        """Deserialize test case."""
        steps_val = data.get("steps", [])
        if isinstance(steps_val, str):
            steps_val = [s.strip() for s in steps_val.split("\n") if s.strip()]
        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            steps=steps_val,
            expected=str(data.get("expected", "")),
            type=str(data.get("type", "System")),
            linked_req=str(data.get("linked_req", "")),
            status=str(data.get("status", "Not Run")),
            auto_generated=bool(data.get("auto_generated", False)),
            defect_notes=str(data.get("defect_notes", "")),
            execution_comment=str(data.get("execution_comment", "")),
            defect_severity=str(data.get("defect_severity", "None")),
        )



@dataclass
class Project:
    """
    Top-level project containing all traceability assets.
    """
    name: str = "Online Food Delivery Platform"
    version: str = "1.0.0"
    description: str = "University SE Course Project Traceability Matrix"
    requirements: List[Requirement] = field(default_factory=list)
    design_elements: List[DesignElement] = field(default_factory=list)
    test_cases: List[TestCase] = field(default_factory=list)

    def get_requirement(self, req_id: str) -> Optional[Requirement]:
        """Retrieve requirement by ID."""
        return next((r for r in self.requirements if r.id == req_id), None)

    def get_design_element(self, design_id: str) -> Optional[DesignElement]:
        """Retrieve design element by ID."""
        return next((d for d in self.design_elements if d.id == design_id), None)

    def get_test_case(self, test_id: str) -> Optional[TestCase]:
        """Retrieve test case by ID."""
        return next((t for t in self.test_cases if t.id == test_id), None)

    def get_tests_for_requirement(self, req_id: str) -> List[TestCase]:
        """Find all tests linked to a requirement."""
        return [t for t in self.test_cases if t.linked_req == req_id]

    def get_design_for_requirement(self, req_id: str) -> List[DesignElement]:
        """Find all design elements referencing a requirement."""
        return [d for d in self.design_elements if req_id in d.linked_reqs]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire project state."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "requirements": [r.to_dict() for r in self.requirements],
            "design_elements": [d.to_dict() for d in self.design_elements],
            "test_cases": [t.to_dict() for t in self.test_cases],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Project:
        """Deserialize project state."""
        reqs = [Requirement.from_dict(r) for r in data.get("requirements", [])]
        des = [DesignElement.from_dict(d) for d in data.get("design_elements", [])]
        tests = [TestCase.from_dict(t) for t in data.get("test_cases", [])]
        return cls(
            name=str(data.get("name", "Online Food Delivery Platform")),
            version=str(data.get("version", "1.0.0")),
            description=str(data.get("description", "")),
            requirements=reqs,
            design_elements=des,
            test_cases=tests,
        )
