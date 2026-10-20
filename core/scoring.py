"""
Quality Health Scoring and ISO 25010 Quality Factor Mapping for TraceLens.
Formula:
Health = 0.40 * Weighted_Test_Coverage
       + 0.30 * Avg_Clarity_Score
       + 0.20 * Stability_Score
       + 0.10 * Design_Link_Coverage
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List

from core.models import Project, Requirement
from core.linter import lint_requirement, NUMERIC_CRITERIA_REGEX, detect_conflicts


@dataclass
class RequirementCompleteness:
    """Evaluation of an individual requirement's completeness checklist."""
    req_id: str
    has_test: bool
    has_design: bool
    has_measurable: bool
    is_approved: bool
    score: float  # 0 to 100%
    missing: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert completeness data to dictionary."""
        return {
            "req_id": self.req_id,
            "has_test": self.has_test,
            "has_design": self.has_design,
            "has_measurable": self.has_measurable,
            "is_approved": self.is_approved,
            "score": self.score,
            "missing": self.missing,
        }


def calculate_requirement_completeness(project: Project, req: Requirement) -> RequirementCompleteness:
    """
    Calculate completeness score (0-100%) for a single requirement:
    - Has linked test(s) (25%)
    - Has linked design element(s) (25%)
    - Has measurable acceptance criterion / number (25%)
    - Is in 'Approved' status (25%)
    """
    has_test = any(t.linked_req == req.id for t in project.test_cases)
    has_design = any(req.id in d.linked_reqs for d in project.design_elements)
    has_measurable = bool(NUMERIC_CRITERIA_REGEX.search(req.text))
    is_approved = (req.status == "Approved")

    missing: List[str] = []
    if not has_test:
        missing.append("No verification test linked")
    if not has_design:
        missing.append("No architectural design element linked")
    if not has_measurable:
        missing.append("No quantifiable numeric metric or threshold")
    if not is_approved:
        missing.append(f"Status is '{req.status}' (not yet Approved)")

    items_met = sum([has_test, has_design, has_measurable, is_approved])
    score = round((items_met / 4.0) * 100.0, 1)

    return RequirementCompleteness(
        req_id=req.id,
        has_test=has_test,
        has_design=has_design,
        has_measurable=has_measurable,
        is_approved=is_approved,
        score=score,
        missing=missing,
    )


def calculate_all_completeness(project: Project) -> Dict[str, RequirementCompleteness]:
    """Calculate completeness for all requirements in the project."""
    return {r.id: calculate_requirement_completeness(project, r) for r in project.requirements}


@dataclass
class ISOQualityFactor:
    """ISO/IEC 25010 software product quality attribute evaluation."""
    factor: str
    score: float
    status: str       # "Optimal" | "Adequate" | "Sub-optimal"
    key_metrics: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert quality factor to dictionary."""
        return {
            "factor": self.factor,
            "score": self.score,
            "status": self.status,
            "key_metrics": self.key_metrics,
            "recommendation": self.recommendation,
        }


@dataclass
class QualityHealthReport:
    """Holistic project quality health score report."""
    composite_score: float
    test_coverage_weighted: float
    avg_clarity_score: float
    stability_score: float
    volatility_index: float
    design_link_coverage: float
    verdict: str
    iso_factors: List[ISOQualityFactor]

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "composite_score": self.composite_score,
            "test_coverage_weighted": self.test_coverage_weighted,
            "avg_clarity_score": self.avg_clarity_score,
            "stability_score": self.stability_score,
            "volatility_index": self.volatility_index,
            "design_link_coverage": self.design_link_coverage,
            "verdict": self.verdict,
            "iso_factors": [f.to_dict() for f in self.iso_factors],
        }


PRIORITY_WEIGHTS = {
    "High": 3,
    "Medium": 2,
    "Low": 1,
}


def calculate_quality_health(project: Project) -> QualityHealthReport:
    """
    Calculate the project health score (0-100) and ISO 25010 8-factor quality evaluation.
    """
    reqs = project.requirements
    if not reqs:
        return QualityHealthReport(
            composite_score=0.0,
            test_coverage_weighted=0.0,
            avg_clarity_score=0.0,
            stability_score=100.0,
            volatility_index=0.0,
            design_link_coverage=0.0,
            verdict="No requirements defined in project.",
            iso_factors=[],
        )

    # 1. Weighted Test Coverage (0.40)
    tested_req_ids = {t.linked_req for t in project.test_cases if t.linked_req}
    total_weight = 0
    covered_weight = 0

    for r in reqs:
        w = PRIORITY_WEIGHTS.get(r.priority, 2)
        total_weight += w
        if r.id in tested_req_ids:
            covered_weight += w

    test_coverage_weighted = round((covered_weight / total_weight) * 100.0, 1) if total_weight > 0 else 0.0

    # 2. Average Clarity Score (0.30)
    clarity_scores = [lint_requirement(r).score for r in reqs]
    avg_clarity = round(sum(clarity_scores) / len(clarity_scores), 1)

    # 3. Stability Score (0.20)
    total_changes = sum(r.change_count for r in reqs)
    avg_change_per_req = total_changes / len(reqs)
    volatility_index = round(min(100.0, avg_change_per_req * 25.0), 1)
    stability_score = round(max(0.0, 100.0 - volatility_index), 1)

    # 4. Design-Link Coverage (0.10)
    design_linked_reqs = set()
    for d in project.design_elements:
        design_linked_reqs.update(d.linked_reqs)

    linked_count = sum(1 for r in reqs if r.id in design_linked_reqs)
    design_link_coverage = round((linked_count / len(reqs)) * 100.0, 1)

    # 5. Composite Score
    composite = round(
        (0.40 * test_coverage_weighted)
        + (0.30 * avg_clarity)
        + (0.20 * stability_score)
        + (0.10 * design_link_coverage),
        1,
    )
    composite = max(0.0, min(100.0, composite))

    # Verdict
    if composite >= 85.0:
        verdict = "Excellent: Production-ready traceability, robust verification coverage, and strong architectural cohesion."
    elif composite >= 70.0:
        verdict = "Good: Solid baseline with moderate coverage gaps; recommend adding automated tests for uncovered high-priority requirements."
    elif composite >= 50.0:
        verdict = "Fair: Significant test gaps and clarity deficiencies detected. High risk of defect leakage during release."
    else:
        verdict = "Critical: High volatility, deficient test verification, and vague requirement specifications. Immediate remediation required."

    def factor_status(s: float) -> str:
        if s >= 80.0:
            return "Optimal"
        if s >= 60.0:
            return "Adequate"
        return "Sub-optimal"

    # Conflicts impact compatibility and functional correctness
    conflicts = detect_conflicts(reqs)
    conflict_penalty = min(30.0, len(conflicts) * 15.0)

    # Completeness breakdown
    all_comp = [calculate_requirement_completeness(project, r).score for r in reqs]
    avg_completeness = round(sum(all_comp) / len(all_comp), 1)

    # Calculate scores for all 8 ISO/IEC 25010 characteristics:
    # 1. Functional Suitability (§4.2.1)
    func_reqs = [r for r in reqs if r.type == "Functional"]
    func_tested = sum(1 for r in func_reqs if r.id in tested_req_ids)
    func_coverage = (func_tested / len(func_reqs) * 100.0) if func_reqs else test_coverage_weighted
    functional_suitability = round(max(0.0, (0.50 * func_coverage + 0.30 * avg_completeness + 0.20 * avg_clarity) - conflict_penalty * 0.5), 1)

    # 2. Performance Efficiency (§4.2.2)
    nfr_perf = [r for r in reqs if any(k in r.text.lower() for k in ("fast", "second", "latency", "response", "throughput", "concurrent", "load", "scale"))]
    perf_tested = sum(1 for r in nfr_perf if r.id in tested_req_ids)
    perf_ratio = (perf_tested / len(nfr_perf) * 100.0) if nfr_perf else test_coverage_weighted
    performance_efficiency = round(max(0.0, min(100.0, 0.60 * perf_ratio + 0.40 * avg_clarity)), 1)

    # 3. Compatibility (§4.2.3)
    api_elements = sum(1 for d in project.design_elements if d.kind in ("API", "Module"))
    comp_design_score = min(100.0, api_elements * 20.0)
    compatibility_score = round(max(0.0, min(100.0, (0.60 * comp_design_score + 0.40 * design_link_coverage) - conflict_penalty)), 1)

    # 4. Usability (§4.2.5)
    ui_reqs = [r for r in reqs if any(k in r.text.lower() for k in ("interface", "screen", "button", "view", "user", "display", "mobile", "app"))]
    ui_clarity = [lint_requirement(r).score for r in ui_reqs]
    avg_ui_clarity = (sum(ui_clarity) / len(ui_clarity)) if ui_clarity else avg_clarity
    usability_score = round(max(0.0, min(100.0, 0.55 * avg_ui_clarity + 0.45 * test_coverage_weighted)), 1)

    # 5. Reliability (§4.2.4)
    reliability_score = round(max(0.0, min(100.0, (0.50 * stability_score) + (0.50 * test_coverage_weighted))), 1)

    # 6. Security (§4.2.6)
    sec_reqs = [r for r in reqs if any(k in r.text.lower() for k in ("auth", "password", "token", "encrypt", "payment", "secure", "credential", "session", "gdpr", "privacy"))]
    sec_tested = sum(1 for r in sec_reqs if r.id in tested_req_ids)
    sec_coverage = (sec_tested / len(sec_reqs) * 100.0) if sec_reqs else test_coverage_weighted
    security_score = round(max(0.0, min(100.0, 0.70 * sec_coverage + 0.30 * avg_clarity - (15.0 if any('auth' in c.description.lower() for c in conflicts) else 0.0))), 1)

    # 7. Maintainability (§4.2.8)
    maintainability_score = round(max(0.0, min(100.0, (0.55 * avg_clarity) + (0.45 * design_link_coverage))), 1)

    # 8. Portability (§4.2.9)
    # Measured by design modularity and presence of cross-platform/client requirements
    portability_score = round(max(0.0, min(100.0, 0.50 * design_link_coverage + 0.30 * stability_score + 0.20 * avg_clarity)), 1)

    # 1. Testability (§4.2.7)
    testability_score = round(max(0.0, min(100.0, (0.65 * test_coverage_weighted) + (0.35 * avg_clarity))), 1)

    iso_factors = [
        ISOQualityFactor(
            factor="Testability (ISO 25010 §4.2.7)",
            score=testability_score,
            status=factor_status(testability_score),
            key_metrics=f"Weighted Coverage: {test_coverage_weighted}% | Avg Clarity: {avg_clarity}/100",
            recommendation="Maintain high test density across high-impact requirements." if testability_score >= 80 else "Generate targeted unit/system test cases for uncovered specifications.",
        ),
        ISOQualityFactor(
            factor="Functional Suitability (ISO 25010 §4.2.1)",
            score=functional_suitability,
            status=factor_status(functional_suitability),
            key_metrics=f"Func Coverage: {round(func_coverage, 1)}% | Baseline Completeness: {avg_completeness}%",
            recommendation="Complete approval workflow and link verification test cases to all functional user stories." if functional_suitability < 80 else "Functional baseline covers customer requirements thoroughly.",
        ),
        ISOQualityFactor(
            factor="Performance Efficiency (ISO 25010 §4.2.2)",
            score=performance_efficiency,
            status=factor_status(performance_efficiency),
            key_metrics=f"Perf Coverage: {round(perf_ratio, 1)}% | Clarity: {avg_clarity}/100",
            recommendation="Specify explicit latency SLAs (e.g. <=1.5s) and throughput criteria for data endpoints." if performance_efficiency < 80 else "Explicit response time and scalability thresholds verified.",
        ),
        ISOQualityFactor(
            factor="Compatibility (ISO 25010 §4.2.3)",
            score=compatibility_score,
            status=factor_status(compatibility_score),
            key_metrics=f"API Elements: {api_elements} | Active Conflicts: {len(conflicts)}",
            recommendation="Resolve detected policy conflicts and define integration endpoints for external services." if compatibility_score < 80 else "Interoperability and interface contracts properly defined.",
        ),
        ISOQualityFactor(
            factor="Usability (ISO 25010 §4.2.5)",
            score=usability_score,
            status=factor_status(usability_score),
            key_metrics=f"UI Clarity: {round(avg_ui_clarity, 1)}/100 | Test Coverage: {test_coverage_weighted}%",
            recommendation="Replace vague terms like 'easy' or 'user-friendly' with measurable SUS usability benchmarks." if usability_score < 80 else "User experience and interface requirements meet clarity guidelines.",
        ),
        ISOQualityFactor(
            factor="Reliability (ISO 25010 §4.2.4)",
            score=reliability_score,
            status=factor_status(reliability_score),
            key_metrics=f"Stability Index: {stability_score}/100 | Volatility: {volatility_index}",
            recommendation="Freeze requirement versions and execute regression test suites on recently modified items." if reliability_score < 80 else "Stable requirements baseline with low revision churn.",
        ),
        ISOQualityFactor(
            factor="Security (ISO 25010 §4.2.6)",
            score=security_score,
            status=factor_status(security_score),
            key_metrics=f"Security Req Coverage: {round(sec_coverage, 1)}% | Tested: {sec_tested}/{len(sec_reqs)}",
            recommendation="Add penetration and auth verification tests for sensitive checkout and credential flows." if security_score < 80 else "Authentication and security requirements covered by verification suites.",
        ),
        ISOQualityFactor(
            factor="Maintainability (ISO 25010 §4.2.8)",
            score=maintainability_score,
            status=factor_status(maintainability_score),
            key_metrics=f"Avg Clarity: {avg_clarity}/100 | Design Linkage: {design_link_coverage}%",
            recommendation="Link orphaned requirements to design components and eliminate compound conjunctions." if maintainability_score < 80 else "Strong architectural traceability and clear specifications.",
        ),
        ISOQualityFactor(
            factor="Portability (ISO 25010 §4.2.9)",
            score=portability_score,
            status=factor_status(portability_score),
            key_metrics=f"Design Coverage: {design_link_coverage}% | Modularity Score: {round(design_link_coverage * 0.9, 1)}%",
            recommendation="Decouple platform-specific dependencies into abstract adapter modules." if portability_score < 80 else "Modular design structure supports multi-target deployment.",
        ),
    ]


    return QualityHealthReport(
        composite_score=composite,
        test_coverage_weighted=test_coverage_weighted,
        avg_clarity_score=avg_clarity,
        stability_score=stability_score,
        volatility_index=volatility_index,
        design_link_coverage=design_link_coverage,
        verdict=verdict,
        iso_factors=iso_factors,
    )

