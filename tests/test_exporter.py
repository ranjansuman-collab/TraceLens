"""
Unit tests for document exports and ZIP archive pack generation.
"""

import io
import zipfile
import csv
from core.models import Project, Requirement, DesignElement, TestCase
from core.exporter import (
    generate_traceability_matrix_csv,
    generate_srs_markdown,
    generate_test_plan_markdown,
    generate_quality_report_markdown,
    generate_export_zip,
)


def sample_fixture_project() -> Project:
    """Fixture with requirements, design, and tests."""
    return Project(
        name="TestPlatform",
        version="1.0.0",
        requirements=[
            Requirement(id="R1", text="The system shall filter menus.", type="Functional", priority="High"),
            Requirement(id="R2", text="The system shall maintain 99.9% uptime.", type="Non-Functional", priority="Medium"),
        ],
        design_elements=[
            DesignElement(id="D1", name="CatalogService", kind="Module", linked_reqs=["R1"]),
        ],
        test_cases=[
            TestCase(id="T1", title="Filter test", steps=["Step 1"], expected="200 OK", linked_req="R1", status="Pass"),
        ]
    )


def test_generate_traceability_matrix_csv():
    """Verify CSV matrix format and contents."""
    proj = sample_fixture_project()
    csv_str = generate_traceability_matrix_csv(proj)
    reader = csv.reader(io.StringIO(csv_str))
    rows = list(reader)
    assert len(rows) == 3  # Header + 2 requirements
    assert "Requirement ID" in rows[0]
    assert rows[1][0] == "R1"
    assert rows[1][11] == "Covered"
    assert rows[2][0] == "R2"
    assert rows[2][11] == "UNCOVERED"


def test_generate_srs_markdown():
    """Verify SRS Markdown structure."""
    proj = sample_fixture_project()
    srs = generate_srs_markdown(proj)
    assert "# Software Requirements Specification" in srs
    assert "## 2. Functional Requirements" in srs
    assert "## 3. Non-Functional Requirements" in srs
    assert "R1" in srs
    assert "R2" in srs


def test_generate_test_plan_markdown():
    """Verify Test Plan Markdown structure."""
    proj = sample_fixture_project()
    tp = generate_test_plan_markdown(proj)
    assert "# Software Test Plan" in tp
    assert "## 2. Test Execution Schedule" in tp
    assert "T1" in tp


def test_generate_quality_report_markdown():
    """Verify Quality Report Markdown structure."""
    proj = sample_fixture_project()
    qr = generate_quality_report_markdown(proj)
    assert "# Quality & Health Audit Report" in qr
    assert "Composite Quality Health Score" in qr
    assert "ISO/IEC 25010 Quality Factor Evaluation" in qr
    assert "RMMM" in qr


def test_generate_export_zip():
    """Verify ZIP archive contains all 4 required files."""
    proj = sample_fixture_project()
    zip_bytes = generate_export_zip(proj)
    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 0

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
        names = z.namelist()
        assert "SRS.md" in names
        assert "TestPlan.md" in names
        assert "traceability_matrix.csv" in names
        assert "quality_report.md" in names
