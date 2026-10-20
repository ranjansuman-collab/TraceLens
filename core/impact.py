"""
Change Impact Simulation Engine for TraceLens.
Executes BFS graph traversal to trace blast radius across design elements, test cases,
and sibling requirements, calculating effort estimations based on complexity metrics.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Set, Any
from collections import deque

from core.models import Project, Requirement, DesignElement, TestCase
from core.graph import build_traceability_graph


@dataclass
class EffortBreakdownItem:
    """Component line item for engineering change effort."""
    activity: str
    affected_count: int
    base_unit_hours: float
    complexity_factor: float
    total_hours: float


@dataclass
class ImpactAnalysisResult:
    """Complete impact simulation report."""
    changed_req_id: str
    impacted_requirements: List[str]   # Sibling requirements sharing design elements
    impacted_design_elements: List[str]
    impacted_test_cases: List[str]
    unaffected_nodes: List[str]
    node_color_map: Dict[str, str]
    effort_breakdown: List[EffortBreakdownItem]
    total_effort_hours: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert impact analysis result to dictionary."""
        return {
            "changed_req_id": self.changed_req_id,
            "impacted_requirements": self.impacted_requirements,
            "impacted_design_elements": self.impacted_design_elements,
            "impacted_test_cases": self.impacted_test_cases,
            "unaffected_nodes": self.unaffected_nodes,
            "total_effort_hours": self.total_effort_hours,
            "effort_breakdown": [
                {
                    "activity": b.activity,
                    "affected_count": b.affected_count,
                    "base_unit_hours": b.base_unit_hours,
                    "complexity_factor": b.complexity_factor,
                    "total_hours": b.total_hours,
                }
                for b in self.effort_breakdown
            ],
        }


def simulate_change_impact(project: Project, changed_req_id: str) -> ImpactAnalysisResult:
    """
    Run BFS traversal from changed requirement to identify all directly and transitively
    impacted nodes:
      - Changed requirement (RED)
      - Directly linked design elements (ORANGE)
      - Sibling requirements sharing any of those design elements (AMBER/ROSE)
      - Directly linked tests + tests on impacted design elements (YELLOW)
      - Unaffected nodes (GREY)
    Calculates engineering rework effort based on complexity.
    """
    target_req = project.get_requirement(changed_req_id)
    complexity = target_req.complexity if target_req else 3
    complexity_multiplier = complexity / 3.0

    # 1. Direct design elements
    impacted_design: Set[str] = set()
    for d in project.design_elements:
        if changed_req_id in d.linked_reqs:
            impacted_design.add(d.id)

    # 2. Sibling requirements sharing design elements
    impacted_sibling_reqs: Set[str] = set()
    for d_id in impacted_design:
        des = project.get_design_element(d_id)
        if des:
            for r_id in des.linked_reqs:
                if r_id != changed_req_id:
                    impacted_sibling_reqs.add(r_id)

    # 3. Impacted tests (direct tests on changed req, plus tests on impacted design)
    impacted_tests: Set[str] = set()
    for t in project.test_cases:
        if t.linked_req == changed_req_id:
            impacted_tests.add(t.id)
        elif t.linked_req in impacted_sibling_reqs:
            impacted_tests.add(t.id)

    # 4. Color map for PyVis
    # Red: Changed node (#EF4444)
    # Orange: Impacted design elements (#F97316)
    # Yellow: Impacted tests (#FACC15)
    # Amber/Pink: Sibling requirements (#FB7185)
    # Grey: Unaffected nodes (#64748B)
    color_map: Dict[str, str] = {}

    all_node_ids = (
        [r.id for r in project.requirements]
        + [d.id for d in project.design_elements]
        + [t.id for t in project.test_cases]
    )

    unaffected: List[str] = []

    for nid in all_node_ids:
        if nid == changed_req_id:
            color_map[nid] = "#EF4444"  # Red
        elif nid in impacted_design:
            color_map[nid] = "#F97316"  # Orange
        elif nid in impacted_tests:
            color_map[nid] = "#FACC15"  # Yellow
        elif nid in impacted_sibling_reqs:
            color_map[nid] = "#FB7185"  # Rose / Sibling Req
        else:
            color_map[nid] = "#64748B"  # Grey
            unaffected.append(nid)

    # 5. Effort estimation:
    # design change: 4h each
    # code change: 6h each (for impacted design components)
    # test update: 1.5h each
    # multiplied by (complexity / 3.0)
    num_design = len(impacted_design)
    num_tests = len(impacted_tests)

    design_hours = round(num_design * 4.0 * complexity_multiplier, 1)
    code_hours = round(max(1, num_design) * 6.0 * complexity_multiplier, 1)
    test_hours = round(num_tests * 1.5 * complexity_multiplier, 1)
    total_hours = round(design_hours + code_hours + test_hours, 1)

    breakdown = [
        EffortBreakdownItem(
            activity="Architectural / Design Updates",
            affected_count=num_design,
            base_unit_hours=4.0,
            complexity_factor=round(complexity_multiplier, 2),
            total_hours=design_hours,
        ),
        EffortBreakdownItem(
            activity="Source Code Refactoring & Implementation",
            affected_count=num_design,
            base_unit_hours=6.0,
            complexity_factor=round(complexity_multiplier, 2),
            total_hours=code_hours,
        ),
        EffortBreakdownItem(
            activity="Test Case Updates & Regression Verification",
            affected_count=num_tests,
            base_unit_hours=1.5,
            complexity_factor=round(complexity_multiplier, 2),
            total_hours=test_hours,
        ),
    ]

    return ImpactAnalysisResult(
        changed_req_id=changed_req_id,
        impacted_requirements=sorted(list(impacted_sibling_reqs)),
        impacted_design_elements=sorted(list(impacted_design)),
        impacted_test_cases=sorted(list(impacted_tests)),
        unaffected_nodes=sorted(unaffected),
        node_color_map=color_map,
        effort_breakdown=breakdown,
        total_effort_hours=total_hours,
    )


def apply_change_commit(
    project: Project,
    changed_req_id: str,
    new_text: str,
    impact_result: ImpactAnalysisResult,
) -> None:
    """
    Commit the simulated change:
      1. Updates requirement text, increments version, logs history.
      2. Marks all impacted tests as 'Needs Review'.
    """
    req = project.get_requirement(changed_req_id)
    if req:
        req.update_text(new_text, mark_changed=True)

    for test_id in impact_result.impacted_test_cases:
        tc = project.get_test_case(test_id)
        if tc:
            tc.status = "Needs Review"
