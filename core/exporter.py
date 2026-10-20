"""
Artifact Exporter for TraceLens.
Compiles IEEE-compliant SRS, Test Plan, Traceability Matrix CSV, Quality Health Report,
and packages them into a single downloadable ZIP archive.
"""

from __future__ import annotations
import io
import csv
import zipfile
from datetime import datetime, timezone
from typing import Dict, Any, List

from core.models import Project
from core.linter import lint_requirement, detect_conflicts
from core.scoring import calculate_quality_health
from core.risk import get_prioritized_test_cases, get_uncovered_requirements_by_risk, generate_rmmm_table


def generate_traceability_matrix_csv(project: Project) -> str:
    """
    Generate CSV string representing the Requirements-to-Design-to-Test Traceability Matrix.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Requirement ID",
        "Type",
        "Priority",
        "Impact (1-5)",
        "Complexity (1-5)",
        "Version",
        "Status",
        "Requirement Statement",
        "Linked Design Elements",
        "Linked Test Cases",
        "Total Tests",
        "Coverage Status",
    ])

    for req in project.requirements:
        linked_design = [d.id for d in project.get_design_for_requirement(req.id)]
        linked_tests = [t.id for t in project.get_tests_for_requirement(req.id)]
        coverage_status = "Covered" if linked_tests else "UNCOVERED"

        writer.writerow([
            req.id,
            req.type,
            req.priority,
            req.impact,
            req.complexity,
            f"v{req.version}",
            req.status,
            req.text,
            ", ".join(linked_design) if linked_design else "None",
            ", ".join(linked_tests) if linked_tests else "None",
            len(linked_tests),
            coverage_status,
        ])

    return output.getvalue()


def generate_srs_markdown(project: Project) -> str:
    """
    Generate IEEE 830-style Software Requirements Specification (SRS.md).
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    fr_list = [r for r in project.requirements if r.type == "Functional"]
    nfr_list = [r for r in project.requirements if r.type == "Non-Functional"]

    md = []
    md.append(f"# Software Requirements Specification (SRS)")
    md.append(f"**Project:** {project.name}  ")
    md.append(f"**Version:** {project.version}  ")
    md.append(f"**Generated:** {now}  ")
    md.append(f"**Baseline Tool:** TraceLens Requirements Engineering Suite\n")

    md.append("## 1. Introduction")
    md.append("### 1.1 Purpose")
    md.append(f"This document defines the functional and non-functional requirements for **{project.name}**.")
    md.append("It establishes a verifiable baseline for software design, implementation, and automated test validation.\n")

    md.append("### 1.2 Scope")
    md.append(f"{project.description}\n")

    md.append("## 2. Functional Requirements")
    md.append("| ID | Requirement Statement | Priority | Status | Version | Design Elements | Verified By |")
    md.append("|:---|:----------------------|:--------:|:------:|:-------:|:---------------:|:-----------:|")
    for r in fr_list:
        des = ", ".join([d.id for d in project.get_design_for_requirement(r.id)]) or "None"
        tests = ", ".join([t.id for t in project.get_tests_for_requirement(r.id)]) or "**UNCOVERED**"
        md.append(f"| {r.id} | {r.text} | {r.priority} | {r.status} | v{r.version} | {des} | {tests} |")
    md.append("")

    md.append("## 3. Non-Functional Requirements")
    md.append("| ID | Quality Attribute / Requirement | Priority | Status | Version | Design Elements | Verified By |")
    md.append("|:---|:--------------------------------|:--------:|:------:|:-------:|:---------------:|:-----------:|")
    for r in nfr_list:
        des = ", ".join([d.id for d in project.get_design_for_requirement(r.id)]) or "None"
        tests = ", ".join([t.id for t in project.get_tests_for_requirement(r.id)]) or "**UNCOVERED**"
        md.append(f"| {r.id} | {r.text} | {r.priority} | {r.status} | v{r.version} | {des} | {tests} |")
    md.append("")

    md.append("## 4. Traceability Summary")
    tested_count = sum(1 for r in project.requirements if project.get_tests_for_requirement(r.id))
    total_reqs = len(project.requirements)
    cov_pct = round((tested_count / total_reqs) * 100, 1) if total_reqs else 0
    md.append(f"- **Total Requirements:** {total_reqs}")
    md.append(f"- **Covered by Tests:** {tested_count} ({cov_pct}%)")
    md.append(f"- **Uncovered Requirements:** {total_reqs - tested_count}")
    md.append(f"- **Associated Architectural Elements:** {len(project.design_elements)}")
    md.append(f"- **Total Test Assets:** {len(project.test_cases)}")

    return "\n".join(md)


def generate_test_plan_markdown(project: Project) -> str:
    """
    Generate IEEE 829-style Software Test Plan (TestPlan.md).
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    prioritized_tests = get_prioritized_test_cases(project)

    md = []
    md.append(f"# Software Test Plan & Verification Strategy")
    md.append(f"**Target System:** {project.name}  ")
    md.append(f"**Document Version:** {project.version}  ")
    md.append(f"**Date:** {now}\n")

    md.append("## 1. Test Strategy & Scope")
    md.append("The verification approach incorporates multi-tiered validation across Unit, Integration, System, and Acceptance levels.")
    md.append("TraceLens enforces bi-directional traceability linking each test case directly to its originating requirement specification.\n")

    md.append("## 2. Test Execution Schedule (Risk-Prioritized)")
    md.append("Tests are ordered by requirement risk score `Impact * Complexity * (1 + Change_Count)`:")
    md.append("| Order | Test ID | Target Req | Risk Score | Test Type | Title | Status |")
    md.append("|:-----:|:-------:|:----------:|:----------:|:---------:|:------|:------:|")
    for idx, pt in enumerate(prioritized_tests, start=1):
        md.append(
            f"| {idx} | {pt['test_id']} | {pt['linked_req']} | {pt['risk_score']} | "
            f"{pt['type']} | {pt['title']} | {pt['status']} |"
        )
    md.append("")

    md.append("## 3. Comprehensive Test Specifications")
    for tc in project.test_cases:
        md.append(f"### [{tc.id}] {tc.title}")
        md.append(f"- **Linked Requirement:** {tc.linked_req}")
        md.append(f"- **Test Level / Type:** {tc.type}")
        md.append(f"- **Current Status:** {tc.status}")
        md.append(f"- **Auto-Generated:** {'Yes' if tc.auto_generated else 'No'}")
        md.append("**Execution Steps:**")
        for step in tc.steps:
            md.append(f"  - {step}")
        md.append(f"**Expected Result:** {tc.expected}\n")

    md.append("## 4. Pass / Fail & Exit Criteria")
    md.append("- **Critical Defect Threshold:** Zero open 'Fail' status test cases on High priority requirements.")
    md.append("- **Regression Verification:** All tests marked 'Needs Review' after change simulation must be re-executed.")
    md.append("- **Target Pass Rate:** >= 95% across all system test suites.")

    return "\n".join(md)


def generate_quality_report_markdown(project: Project) -> str:
    """
    Generate Quality and Health Audit Report (quality_report.md).
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    health = calculate_quality_health(project)
    uncovered = get_uncovered_requirements_by_risk(project)
    conflicts = detect_conflicts(project.requirements)
    rmmm_items = generate_rmmm_table(project)

    md = []
    md.append(f"# Quality & Health Audit Report")
    md.append(f"**Project:** {project.name}  ")
    md.append(f"**Date:** {now}  ")
    md.append(f"**Audited By:** TraceLens Quality Engine\n")

    md.append("## 1. Executive Quality Scorecard")
    md.append(f"- **Composite Quality Health Score:** **{health.composite_score} / 100**")
    md.append(f"- **Weighted Test Coverage:** {health.test_coverage_weighted}% (weight: High=3, Med=2, Low=1)")
    md.append(f"- **Average Requirement Clarity:** {health.avg_clarity_score} / 100")
    md.append(f"- **Baseline Stability Index:** {health.stability_score} / 100 (Volatility Index: {health.volatility_index})")
    md.append(f"- **Design-Link Coverage:** {health.design_link_coverage}%")
    md.append(f"\n> **Verdict:** {health.verdict}\n")

    md.append("## 2. ISO/IEC 25010 Quality Factor Evaluation")
    md.append("| Quality Factor | Score | Status | Key Metric | Engineering Recommendation |")
    md.append("|:---------------|:-----:|:------:|:-----------|:---------------------------|")
    for f in health.iso_factors:
        md.append(f"| {f.factor} | {f.score}/100 | {f.status} | {f.key_metrics} | {f.recommendation} |")
    md.append("")

    md.append("## 3. Semantic Requirement Conflicts Detected")
    if conflicts:
        for c in conflicts:
            md.append(f"- **[{c.severity} Severity]** Conflict between **{c.req1_id}** and **{c.req2_id}**: {c.description}")
    else:
        md.append("- *No contradictory requirement statements detected in baseline.*")
    md.append("")

    md.append("## 4. Test Gap Analysis (Uncovered Requirements Ranked by Risk)")
    if uncovered:
        md.append("| Req ID | Priority | Impact | Complexity | Change Count | Risk Score | Requirement Text |")
        md.append("|:------:|:--------:|:------:|:----------:|:------------:|:----------:|:-----------------|")
        for u in uncovered:
            md.append(f"| {u['req_id']} | {u['priority']} | {u['impact']} | {u['complexity']} | {u['change_count']} | **{u['risk_score']}** | {u['text']} |")
    else:
        md.append("- *All requirements currently have at least one verifying test case.*")
    md.append("")

    md.append("## 5. RMMM (Risk Mitigation, Monitoring & Management) Table")
    md.append("| Risk ID | Linked Req | Identified Risk | Prob | Imp | Score | Mitigation Strategy | Monitoring Metric |")
    md.append("|:-------:|:----------:|:----------------|:----:|:---:|:-----:|:--------------------|:------------------|")
    for r in rmmm_items:
        md.append(
            f"| {r.risk_id} | {r.req_id} | {r.risk_title} | {r.probability} | {r.impact} | "
            f"**{r.risk_score}** | {r.mitigation} | {r.monitoring} |"
        )

    return "\n".join(md)


def generate_export_zip(project: Project) -> bytes:
    """
    Generate in-memory ZIP package containing SRS.md, TestPlan.md,
    traceability_matrix.csv, and quality_report.md.
    """
    buffer = io.BytesIO()

    srs_content = generate_srs_markdown(project)
    test_plan_content = generate_test_plan_markdown(project)
    matrix_csv = generate_traceability_matrix_csv(project)
    quality_report_content = generate_quality_report_markdown(project)

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("SRS.md", srs_content)
        zip_file.writestr("TestPlan.md", test_plan_content)
        zip_file.writestr("traceability_matrix.csv", matrix_csv)
        zip_file.writestr("quality_report.md", quality_report_content)

    buffer.seek(0)
    return buffer.getvalue()
