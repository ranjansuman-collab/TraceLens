"""
Unit tests for NetworkX graph construction and PyVis network rendering.
"""

from core.models import Project, Requirement, DesignElement, TestCase
from core.graph import build_traceability_graph, generate_pyvis_html


def test_build_traceability_graph():
    """Verify directed graph contains all requirements, design elements, and tests."""
    proj = Project(
        requirements=[Requirement(id="R1", text="The system shall process payments.")],
        design_elements=[DesignElement(id="D1", name="PaymentService", kind="Module", linked_reqs=["R1"])],
        test_cases=[TestCase(id="T1", title="Payment unit test", steps=["Step 1"], expected="200 OK", linked_req="R1")]
    )
    g = build_traceability_graph(proj)
    assert g.number_of_nodes() == 3
    assert g.has_node("R1")
    assert g.has_node("D1")
    assert g.has_node("T1")
    assert g.has_edge("R1", "D1")
    assert g.has_edge("R1", "T1")


def test_pyvis_html_generation():
    """Verify pyvis returns valid embeddable HTML string."""
    proj = Project(
        requirements=[Requirement(id="R1", text="Req 1")],
        design_elements=[DesignElement(id="D1", name="Mod 1", kind="Module", linked_reqs=["R1"])],
        test_cases=[TestCase(id="T1", title="Test 1", steps=["S1"], expected="E1", linked_req="R1")]
    )
    g = build_traceability_graph(proj)
    html = generate_pyvis_html(g, highlight_nodes={"R1": "#EF4444"})
    assert isinstance(html, str)
    assert len(html) > 100
    assert "vis" in html.lower() or "network" in html.lower() or "html" in html.lower()
