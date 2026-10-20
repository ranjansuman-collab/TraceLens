"""
Change Impact Simulator Page for TraceLens.
Executes BFS blast radius graph analysis, renders interactive PyVis visualization,
estimates engineering rework effort, and commits changes with automated regression tagging.
"""

from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from core.models import Project
from core.graph import build_traceability_graph, generate_pyvis_html
from core.impact import simulate_change_impact, apply_change_commit
from core.storage import save_project


def render_impact_page(project: Project) -> None:
    """Render change impact simulation, blast radius graph, and rework estimator."""
    st.markdown("## 💥 Change Impact Simulator & Blast Radius")
    st.markdown(
        "Simulate the ripple effects of modifying a requirement. Runs graph BFS to identify all "
        "impacted architectural design elements, verifying tests, and sibling requirements, "
        "estimating engineering rework effort before applying changes."
    )

    req_options = {f"[{r.id}] ({r.priority}) {r.text[:65]}...": r.id for r in project.requirements}
    if not req_options:
        st.warning("No requirements in project.")
        return

    col_sel, col_btn = st.columns([2.5, 1])
    with col_sel:
        selected_label = st.selectbox("Select Target Requirement to Modify", list(req_options.keys()))
        selected_req_id = req_options[selected_label]
        target_req = project.get_requirement(selected_req_id)

    if not target_req:
        return

    # Text area for proposed change
    edit_key = f"impact_edit_text_{target_req.id}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = target_req.text

    new_text = st.text_area(
        "Proposed Requirement Modification",
        value=st.session_state[edit_key],
        height=100,
        help="Modify the requirement statement to simulate downstream rework.",
    )
    st.session_state[edit_key] = new_text

    col_sim, col_reset = st.columns([1, 4])
    with col_sim:
        btn_simulate = st.button("⚡ Simulate Change Impact", type="primary")

    if btn_simulate:
        with st.spinner("Executing BFS graph traversal and calculating blast radius..."):
            impact_res = simulate_change_impact(project, target_req.id)
            st.session_state["current_impact"] = impact_res

    # Check if impact result is available in session state
    if "current_impact" in st.session_state:
        impact: ImpactAnalysisResult = st.session_state["current_impact"]

        st.markdown("---")
        st.subheader(f"🔍 Blast Radius Analysis for [{impact.changed_req_id}]")

        # Color Legend
        st.markdown(
            """
            <div style="display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 12px; font-size: 0.9rem;">
                <span style="color: #EF4444; font-weight: bold;">🔴 Changed Req</span>
                <span style="color: #F97316; font-weight: bold;">🟠 Impacted Design</span>
                <span style="color: #FACC15; font-weight: bold;">🟡 Impacted Tests</span>
                <span style="color: #FB7185; font-weight: bold;">🌸 Sibling Reqs (Regression Risk)</span>
                <span style="color: #94A3B8; font-weight: bold;">⚪ Unaffected</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # PyVis Interactive Graph
        nx_graph = build_traceability_graph(project)
        pyvis_html = generate_pyvis_html(
            nx_graph,
            height="520px",
            highlight_nodes=impact.node_color_map,
            dark_mode=True,
        )
        components.html(pyvis_html, height=540, scrolling=False)

        st.markdown("---")

        # Metrics and Effort Breakdown
        col_eff1, col_eff2 = st.columns([1.2, 2])

        with col_eff1:
            st.subheader("⏱️ Engineering Effort Estimation")
            st.metric(
                "Total Rework Estimate",
                f"{impact.total_effort_hours} Hours",
                help="Sum of design updates (4h), source implementation (6h), and test updates (1.5h) adjusted for complexity.",
            )
            st.markdown(
                f"- **Target Complexity:** `{target_req.complexity}/5` (Factor: `{round(target_req.complexity / 3.0, 2)}x`)\n"
                f"- **Impacted Design Elements:** `{len(impact.impacted_design_elements)}`\n"
                f"- **Impacted Test Cases:** `{len(impact.impacted_test_cases)}`\n"
                f"- **Sibling Reqs Affected:** `{len(impact.impacted_requirements)}`"
            )

        with col_eff2:
            st.subheader("📊 Rework Breakdown Summary")
            breakdown_rows = []
            for b in impact.effort_breakdown:
                breakdown_rows.append({
                    "Engineering Activity": b.activity,
                    "Count": b.affected_count,
                    "Base Unit Rate": f"{b.base_unit_hours} hrs",
                    "Complexity Factor": f"{b.complexity_factor}x",
                    "Total Hours": f"{b.total_hours} hrs",
                })
            df_breakdown = pd.DataFrame(breakdown_rows)
            st.dataframe(df_breakdown, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Detailed affected components
        c_des, c_tst, c_sib = st.columns(3)
        with c_des:
            st.markdown(f"**Impacted Design ({len(impact.impacted_design_elements)}):**")
            for did in impact.impacted_design_elements:
                d_obj = project.get_design_element(did)
                name = d_obj.name if d_obj else did
                st.markdown(f"- 🟠 `{did}`: {name}")
        with c_tst:
            st.markdown(f"**Impacted Tests ({len(impact.impacted_test_cases)}):**")
            for tid in impact.impacted_test_cases:
                t_obj = project.get_test_case(tid)
                title = t_obj.title if t_obj else tid
                st.markdown(f"- 🟡 `{tid}`: {title}")
        with c_sib:
            st.markdown(f"**Sibling Reqs ({len(impact.impacted_requirements)}):**")
            for rid in impact.impacted_requirements:
                r_obj = project.get_requirement(rid)
                txt = r_obj.text[:40] if r_obj else rid
                st.markdown(f"- 🌸 `{rid}`: {txt}...")

        st.markdown("---")

        # Commit button
        st.subheader("🚀 Commit & Propagate Changes")
        st.info(
            f"Clicking **'Apply Change'** will:\n"
            f"1. Update `{target_req.id}` to version `v{target_req.version + 1}`, append audit history, and set status to **Changed**.\n"
            f"2. Automatically flag all **{len(impact.impacted_test_cases)}** impacted test cases as **'Needs Review'** for regression testing."
        )

        if st.button("Apply Change & Flag Impacted Tests", type="primary"):
            apply_change_commit(project, target_req.id, new_text, impact)
            save_project(project)
            del st.session_state["current_impact"]
            st.success(
                f"Change committed successfully! {target_req.id} is now v{target_req.version}. "
                f"{len(impact.impacted_test_cases)} test cases flagged as 'Needs Review'."
            )
            st.rerun()
