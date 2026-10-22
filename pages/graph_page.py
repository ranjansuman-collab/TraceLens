"""
Live Full Traceability Graph Page for TraceLens.
Renders an interactive multi-tiered network visualization of Requirements, Design Elements, and Test Cases.
"""

from __future__ import annotations
import streamlit as st
import networkx as nx

from core.models import Project
from core.graph import build_traceability_graph, generate_pyvis_html


def render_graph_page(project: Project) -> None:
    """Render the Live Full Traceability Graph page."""
    st.markdown("## 🕸️ Live Full Traceability Graph")
    st.caption("Interactive multi-tiered graph connecting Requirements (Blue), Design Elements (Purple), and Tests (Green/Amber/Red).")

    # Build the full base graph
    base_graph = build_traceability_graph(project)

    # Sidebar / Toolbar filter controls
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([1, 1, 1, 2])
    with ctrl_col1:
        show_reqs = st.checkbox("Requirements (Box)", value=True)
    with ctrl_col2:
        show_design = st.checkbox("Design (Diamond)", value=True)
    with ctrl_col3:
        show_tests = st.checkbox("Tests (Circle)", value=True)
    with ctrl_col4:
        all_nodes = sorted(list(base_graph.nodes()))
        focus_node = st.selectbox(
            "🎯 Focus / Highlight Neighborhood",
            ["None"] + all_nodes,
            help="Select a node to highlight its direct predecessors and successors."
        )

    # Filter subgraph based on selected node types
    active_types = set()
    if show_reqs:
        active_types.add("Requirement")
    if show_design:
        active_types.add("DesignElement")
    if show_tests:
        active_types.add("TestCase")

    filtered_nodes = [
        n for n, attrs in base_graph.nodes(data=True)
        if attrs.get("node_type") in active_types
    ]
    subgraph = base_graph.subgraph(filtered_nodes).copy()

    # Highlight mapping
    highlight_nodes = {}
    if focus_node != "None" and focus_node in subgraph:
        # Focus node gets bright yellow, neighbors get amber
        highlight_nodes[focus_node] = "#FACC15"
        for succ in subgraph.successors(focus_node):
            highlight_nodes[succ] = "#FB923C"
        for pred in subgraph.predecessors(focus_node):
            highlight_nodes[pred] = "#38BDF8"

    # Display Graph Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Nodes", subgraph.number_of_nodes())
    with m2:
        st.metric("Total Edges", subgraph.number_of_edges())
    with m3:
        density = nx.density(subgraph) if subgraph.number_of_nodes() > 1 else 0.0
        st.metric("Graph Density", f"{density:.3f}")
    with m4:
        deg = sum(d for _, d in subgraph.degree()) / max(1, subgraph.number_of_nodes())
        st.metric("Avg Degree", f"{deg:.1f}")
    with m5:
        isolated = sum(1 for _, d in subgraph.degree() if d == 0)
        st.metric("Orphan Nodes", isolated)

    # Visual Legend
    st.markdown(
        """
        <div style="display: flex; gap: 18px; margin: 8px 0 16px 0; font-size: 0.88rem; flex-wrap: wrap;">
            <span>🟦 <strong style="color: #60A5FA;">Requirement</strong> (Level 1)</span>
            <span>🟪 <strong style="color: #C084FC;">Design Element</strong> (Level 2)</span>
            <span>🟩 <strong style="color: #34D399;">Test: Pass</strong></span>
            <span>🟧 <strong style="color: #FBBF24;">Test: Not Run / Review</strong></span>
            <span>🟥 <strong style="color: #F87171;">Test: Fail</strong></span>
            <span>🟡 <strong style="color: #FACC15;">Focused Neighborhood</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if subgraph.number_of_nodes() == 0:
        st.warning("No nodes match the selected layer filters. Please enable at least one node type above.")
    else:
        # Generate PyVis HTML
        html_content = generate_pyvis_html(
            subgraph,
            height="600px",
            width="100%",
            highlight_nodes=highlight_nodes if highlight_nodes else None,
            dark_mode=True,
        )
        st.html(html_content, width="stretch", unsafe_allow_javascript=True)

    # Detailed Node Inspector
    with st.expander("🔍 Node Property Inspector", expanded=False):
        inspect_node = st.selectbox("Inspect Node Details", all_nodes)
        if inspect_node and base_graph.has_node(inspect_node):
            attrs = base_graph.nodes[inspect_node]
            c_left, c_right = st.columns([1, 2])
            with c_left:
                st.write(f"**ID:** `{inspect_node}`")
                st.write(f"**Type:** `{attrs.get('node_type')}`")
                in_degree = base_graph.in_degree(inspect_node)
                out_degree = base_graph.out_degree(inspect_node)
                st.write(f"**Inbound Connections:** `{in_degree}`")
                st.write(f"**Outbound Connections:** `{out_degree}`")
            with c_right:
                data = attrs.get("data", {})
                st.json(data)
