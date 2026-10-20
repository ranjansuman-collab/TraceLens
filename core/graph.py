"""
Graph construction and PyVis rendering engine for TraceLens.
Builds the multi-tiered requirements-design-test traceability network.
"""

from __future__ import annotations
import json
import networkx as nx
from typing import Dict, Any, Optional, Set
from pyvis.network import Network

from core.models import Project


def build_traceability_graph(project: Project) -> nx.DiGraph:
    """
    Construct a directed NetworkX graph linking requirements, design elements, and tests.
    Edges:
      - Requirement -> DesignElement (implemented_by)
      - Requirement -> TestCase (verified_by)
      - DesignElement -> TestCase (covered_by)
    """
    g = nx.DiGraph()

    # 1. Add Requirement nodes
    for req in project.requirements:
        g.add_node(
            req.id,
            label=f"{req.id}\n{req.priority}",
            title=f"<b>[{req.id}]</b> {req.type}<br><b>Priority:</b> {req.priority}<br><b>Text:</b> {req.text}<br><b>Status:</b> {req.status}",
            node_type="Requirement",
            color="#3B82F6",  # Modern Blue
            shape="box",
            level=1,
            size=25,
            data=req.to_dict(),
        )

    # 2. Add DesignElement nodes
    for des in project.design_elements:
        g.add_node(
            des.id,
            label=f"{des.id}\n({des.kind})",
            title=f"<b>[{des.id}] {des.name}</b><br><b>Kind:</b> {des.kind}<br><b>Linked Reqs:</b> {', '.join(des.linked_reqs)}",
            node_type="DesignElement",
            color="#8B5CF6",  # Modern Purple
            shape="diamond",
            level=2,
            size=22,
            data=des.to_dict(),
        )
        for req_id in des.linked_reqs:
            if g.has_node(req_id):
                g.add_edge(req_id, des.id, relation="implemented_by", color="#93C5FD")

    # 3. Add TestCase nodes
    for tc in project.test_cases:
        status_color = "#10B981" if tc.status == "Pass" else ("#EF4444" if tc.status == "Fail" else "#F59E0B")
        g.add_node(
            tc.id,
            label=f"{tc.id}\n[{tc.status}]",
            title=f"<b>[{tc.id}] {tc.title}</b><br><b>Type:</b> {tc.type}<br><b>Status:</b> {tc.status}<br><b>Verifies:</b> {tc.linked_req}",
            node_type="TestCase",
            color=status_color,
            shape="ellipse",
            level=3,
            size=20,
            data=tc.to_dict(),
        )
        if tc.linked_req and g.has_node(tc.linked_req):
            g.add_edge(tc.linked_req, tc.id, relation="verified_by", color="#A7F3D0")
            # Also derive edge from relevant design elements to this test
            for des in project.get_design_for_requirement(tc.linked_req):
                if g.has_node(des.id):
                    g.add_edge(des.id, tc.id, relation="covered_by", color="#DDD6FE")

    return g


def generate_pyvis_html(
    nx_graph: nx.DiGraph,
    height: str = "550px",
    width: str = "100%",
    highlight_nodes: Optional[Dict[str, str]] = None,
    dark_mode: bool = True,
) -> str:
    """
    Generate interactive HTML embedding string for PyVis network.
    Supports node-specific color overrides (for change impact simulation).
    """
    net = Network(
        height=height,
        width=width,
        directed=True,
        bgcolor="#0F172A" if dark_mode else "#F8FAFC",
        font_color="#F8FAFC" if dark_mode else "#0F172A",
    )

    # Disable default cdn unpkg failures by embedding safe vis options
    net.set_options("""
    {
      "nodes": {
        "font": { "size": 13, "face": "Inter, sans-serif" },
        "borderWidth": 2,
        "shadow": true
      },
      "edges": {
        "color": { "inherit": false },
        "smooth": { "type": "cubicBezier", "roundness": 0.5 },
        "arrows": { "to": { "enabled": true, "scaleFactor": 0.6 } }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -4000,
          "centralGravity": 0.3,
          "springLength": 95,
          "springConstant": 0.04,
          "damping": 0.09,
          "avoidOverlap": 0.2
        },
        "minVelocity": 0.75
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true,
        "zoomView": true
      }
    }
    """)

    highlight_map = highlight_nodes or {}

    for node_id, attrs in nx_graph.nodes(data=True):
        color = highlight_map.get(node_id, attrs.get("color", "#64748B"))
        border_color = "#FFFFFF" if node_id in highlight_map else "#334155"
        size = 32 if node_id in highlight_map else attrs.get("size", 20)

        net.add_node(
            node_id,
            label=attrs.get("label", node_id),
            title=attrs.get("title", node_id),
            shape=attrs.get("shape", "dot"),
            color={
                "background": color,
                "border": border_color,
                "highlight": {"background": color, "border": "#FACC15"},
            },
            size=size,
        )

    for u, v, attrs in nx_graph.edges(data=True):
        edge_color = "#64748B"
        if u in highlight_map and v in highlight_map:
            edge_color = "#F59E0B"
        net.add_edge(u, v, title=attrs.get("relation", ""), color=edge_color)

    # Return pure HTML string
    return net.generate_html()


def build_requirement_dependency_graph(project: Project) -> nx.Graph:
    """
    Construct a requirement-to-requirement relationship network.
    Edges represent:
      - Shared design element coupling (coupling via architecture)
      - Detected specification conflicts (policy/logic contradictions)
      - Redundancy / Overlapping statements (similarity >= 80%)
    """
    g = nx.Graph()
    from core.linter import detect_conflicts, detect_duplicates

    # 1. Add Requirement nodes
    for req in project.requirements:
        status_color = "#3B82F6" if req.status == "Approved" else ("#F59E0B" if req.status == "Changed" else "#94A3B8")
        g.add_node(
            req.id,
            label=f"{req.id}\n({req.priority})",
            title=f"<b>[{req.id}]</b> {req.type}<br><b>Priority:</b> {req.priority}<br><b>Text:</b> {req.text}<br><b>Status:</b> {req.status}",
            node_type="Requirement",
            color=status_color,
            shape="box",
            size=26,
        )

    req_ids = [r.id for r in project.requirements]

    # 2. Shared design element edges
    for i in range(len(req_ids)):
        for j in range(i + 1, len(req_ids)):
            r1_id = req_ids[i]
            r2_id = req_ids[j]
            shared_des = [
                d.id for d in project.design_elements
                if r1_id in d.linked_reqs and r2_id in d.linked_reqs
            ]
            if shared_des:
                g.add_edge(
                    r1_id,
                    r2_id,
                    relation=f"Shared Design: {', '.join(shared_des)}",
                    color="#818CF8",
                    width=len(shared_des) * 2,
                )

    # 3. Conflict edges
    conflicts = detect_conflicts(project.requirements)
    for c in conflicts:
        if g.has_node(c.req1_id) and g.has_node(c.req2_id):
            g.add_edge(
                c.req1_id,
                c.req2_id,
                relation=f"CONFLICT: {c.description}",
                color="#EF4444",
                width=3,
            )

    # 4. Duplicate / Overlap edges
    duplicates = detect_duplicates(project.requirements)
    for d in duplicates:
        if g.has_node(d.req1_id) and g.has_node(d.req2_id):
            if not g.has_edge(d.req1_id, d.req2_id):
                g.add_edge(
                    d.req1_id,
                    d.req2_id,
                    relation=f"OVERLAP ({int(d.similarity * 100)}%): {d.description}",
                    color="#F97316",
                    width=2,
                )

    return g

