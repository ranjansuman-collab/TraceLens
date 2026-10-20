"""
Requirement Dependency Graph Page for TraceLens.
Visualizes requirement-to-requirement coupling via shared architecture, detected conflicts, and semantic overlap.
"""

from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import pandas as pd

from core.models import Project
from core.graph import build_requirement_dependency_graph, generate_pyvis_html
from core.linter import detect_conflicts, detect_duplicates


def render_req_dependency_page(project: Project) -> None:
    """Render the Requirement Dependency Graph page."""
    st.markdown("## 🔗 Requirement Dependency & Conflict Graph")
    st.caption("Analyzes direct requirement-to-requirement couplings: shared architecture, semantic contradictions, and duplicate statements.")

    reqs = project.requirements
    if not reqs:
        st.info("No requirements available to display.")
        return

    # Edge filters
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        show_shared = st.checkbox("Shared Design Coupling", value=True)
    with f_col2:
        show_conflicts = st.checkbox("Detected Conflicts", value=True)
    with f_col3:
        show_overlaps = st.checkbox("Semantic Overlaps (>80%)", value=True)
    with f_col4:
        layout_style = st.selectbox("Graph Physics", ["Standard", "High Repulsion", "Hierarchical"])

    # Build base graph
    raw_graph = build_requirement_dependency_graph(project)

    # Filter edges based on toggles
    filtered_edges = []
    for u, v, data in raw_graph.edges(data=True):
        rel = data.get("relation", "")
        if "Shared Design" in rel and not show_shared:
            continue
        if "CONFLICT" in rel and not show_conflicts:
            continue
        if "OVERLAP" in rel and not show_overlaps:
            continue
        filtered_edges.append((u, v))

    active_graph = nx.Graph()
    for n, attrs in raw_graph.nodes(data=True):
        active_graph.add_node(n, **attrs)
    for u, v in filtered_edges:
        active_graph.add_edge(u, v, **raw_graph.get_edge_data(u, v))

    # Metrics
    conflicts = detect_conflicts(reqs)
    duplicates = detect_duplicates(reqs)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Requirements", len(reqs))
    with c2:
        st.metric("Coupled Relationships", active_graph.number_of_edges())
    with c3:
        st.metric("Detected Conflicts", len(conflicts), delta="Needs Resolution" if conflicts else "Clean", delta_color="inverse")
    with c4:
        st.metric("Overlapping Pairs", len(duplicates), delta="Redundancy Alert" if duplicates else "Unique", delta_color="inverse")

    # Legend
    st.markdown(
        """
        <div style="display: flex; gap: 20px; margin: 10px 0 16px 0; font-size: 0.88rem; flex-wrap: wrap;">
            <span>🟣 <strong style="color: #A5B4FC;">Shared Design</strong> (Coupled via Modules/APIs)</span>
            <span>🔴 <strong style="color: #F87171;">Contradiction / Conflict</strong> (Incompatible directives)</span>
            <span>🟠 <strong style="color: #FB923C;">Semantic Overlap</strong> (Similarity &ge; 80%)</span>
            <span>🟦 <strong style="color: #60A5FA;">Approved</strong></span>
            <span>🟧 <strong style="color: #FBBF24;">Changed / Churned</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render Graph
    html = generate_pyvis_html(active_graph, height="560px", width="100%", dark_mode=True)
    components.html(html, height=580, scrolling=False)

    # Coupling Table
    st.write("")
    st.subheader("📊 Coupling Centrality Analysis")
    st.caption("Requirements with high coupling require rigorous regression testing during change commits.")

    degrees = dict(active_graph.degree())
    table_data = []
    for r in reqs:
        deg = degrees.get(r.id, 0)
        c_count = sum(1 for c in conflicts if c.req1_id == r.id or c.req2_id == r.id)
        d_count = sum(1 for d in duplicates if d.req1_id == r.id or d.req2_id == r.id)
        table_data.append({
            "Requirement ID": r.id,
            "Type": r.type,
            "Priority": r.priority,
            "Total Coupling Degree": deg,
            "Active Conflicts": c_count,
            "Overlaps": d_count,
            "Status": r.status,
            "Statement": r.text,
        })

    df = pd.DataFrame(table_data).sort_values("Total Coupling Degree", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)
