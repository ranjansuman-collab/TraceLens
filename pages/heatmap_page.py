"""
Test Gap Heatmap Page for TraceLens.
Renders Plotly heatmap of Requirements x Test Types (Unit/Integration/System/Acceptance)
with 0-count red highlights, and ranks uncovered requirements by risk score.
"""

from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from core.models import Project
from core.risk import get_uncovered_requirements_by_risk
from core.ai_client import generate_tests_for_requirement
from core.storage import save_project


def render_heatmap_page(project: Project) -> None:
    """Render the test gap density heatmap and risk-ranked uncovered requirements."""
    st.markdown("## 🗺️ Verification Gap Heatmap")
    st.markdown(
        "Visualize test coverage density across all verification tiers (Unit, Integration, System, Acceptance). "
        "Red cells indicate verification blind spots requiring immediate test development."
    )

    test_types = ["Unit", "Integration", "System", "Acceptance"]
    reqs = project.requirements
    req_ids = [r.id for r in reqs]

    if not reqs:
        st.warning("No requirements in project.")
        return

    # Build matrix data: requirements as rows, test types as columns
    matrix = []
    text_matrix = []

    tested_req_ids = set()
    for r in reqs:
        row_counts = []
        row_texts = []
        tests_for_r = project.get_tests_for_requirement(r.id)
        if tests_for_r:
            tested_req_ids.add(r.id)

        for tt in test_types:
            count = sum(1 for t in tests_for_r if t.type == tt)
            row_counts.append(count)
            row_texts.append(str(count))
        matrix.append(row_counts)
        text_matrix.append(row_texts)

    uncovered_count = len(reqs) - len(tested_req_ids)
    coverage_pct = round((len(tested_req_ids) / len(reqs)) * 100, 1)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Requirements", f"{len(reqs)}")
    with c2:
        st.metric("Covered by Tests", f"{len(tested_req_ids)} ({coverage_pct}%)")
    with c3:
        st.metric("Uncovered Gaps", f"{uncovered_count}", delta=f"-{uncovered_count} gaps", delta_color="inverse")
    with c4:
        avg_tests = round(len(project.test_cases) / max(1, len(reqs)), 2)
        st.metric("Test Density", f"{avg_tests} tests / req")

    st.markdown("---")

    # Heatmap visualization
    st.subheader("🔥 Test Level Coverage Heatmap (0 = Red Blind Spot)")

    # Custom colorscale: 0 -> Red, 1 -> Amber, 2+ -> Green
    custom_colorscale = [
        [0.0, "#EF4444"],    # 0 = Red
        [0.33, "#F59E0B"],   # 1 = Amber
        [0.66, "#10B981"],   # 2 = Green
        [1.0, "#059669"],    # 3+ = Emerald
    ]

    fig_heat = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=test_types,
            y=[f"{r.id} ({r.priority})" for r in reqs],
            text=text_matrix,
            texttemplate="<b>%{text}</b>",
            textfont={"size": 15, "color": "#FFFFFF"},
            colorscale=custom_colorscale,
            showscale=True,
            colorbar=dict(
                title=dict(text="Test Count", font=dict(color="#FFFFFF")),
                tickfont=dict(color="#FFFFFF"),
            ),
            xgap=4,
            ygap=4,
        )
    )

    fig_heat.update_layout(
        xaxis=dict(title="Verification Level (Test Type)", side="top", tickfont=dict(size=13, color="#F8FAFC")),
        yaxis=dict(title="Requirement Specification", autorange="reversed", tickfont=dict(size=12, color="#F8FAFC")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=max(450, len(reqs) * 38),
        margin=dict(l=80, r=40, t=60, b=40),
    )

    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")

    # Section 2: Uncovered Requirements Ranked by Risk Score
    st.subheader("🚨 Uncovered Requirements (Ranked by Risk Score)")
    st.markdown(
        "Requirements with zero verifying test cases ranked descending by risk formula: `Impact × Complexity × (1 + Change_Count)`."
    )

    uncovered_list = get_uncovered_requirements_by_risk(project)

    if uncovered_list:
        df_uncovered = pd.DataFrame([
            {
                "Req ID": u["req_id"],
                "Priority": u["priority"],
                "Impact": f"{u['impact']}/5",
                "Complexity": f"{u['complexity']}/5",
                "Changes": u["change_count"],
                "Risk Score": u["risk_score"],
                "Requirement Text": u["text"],
            }
            for u in uncovered_list
        ])
        st.dataframe(df_uncovered, use_container_width=True, hide_index=True)

        st.markdown("#### ⚡ Quick Remediation")
        col_act1, col_act2 = st.columns([2, 1])
        with col_act1:
            target_uncovered_id = st.selectbox(
                "Select Uncovered Requirement to Generate Tests",
                [u["req_id"] for u in uncovered_list],
            )
        with col_act2:
            st.write("")
            if st.button(f"Generate Tests for {target_uncovered_id}", type="primary"):
                target_req = project.get_requirement(target_uncovered_id)
                if target_req:
                    with st.spinner(f"Generating test cases for {target_req.id}..."):
                        numeric_tids = [int(t.id[1:]) for t in project.test_cases if t.id.startswith("T") and t.id[1:].isdigit()]
                        next_tid = max(numeric_tids) + 1 if numeric_tids else 1
                        new_tests, is_mock = generate_tests_for_requirement(target_req, next_tid)
                        project.test_cases.extend(new_tests)
                        save_project(project)
                        st.success(f"Generated {len(new_tests)} test cases for {target_req.id}!")
                        st.rerun()
    else:
        st.success("🎉 All requirements have at least one test case! Zero test coverage gaps found.")
