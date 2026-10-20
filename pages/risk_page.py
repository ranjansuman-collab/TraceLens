"""
Risk Prioritizer & RMMM Table Page for TraceLens.
Ranks test execution order by requirement risk formula: Risk = Impact * Complexity * (1 + Change_Count)
and renders an auto-filled RMMM (Risk Mitigation, Monitoring, and Management) table with AI synthesis.
"""

from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from core.models import Project
from core.risk import calculate_requirement_risk, get_prioritized_test_cases, generate_rmmm_table
from core.ai_client import generate_rmmm_mitigation_ai, get_mode_badge


def render_risk_page(project: Project) -> None:
    """Render risk prioritization models and RMMM risk mitigation table."""
    st.markdown("## ⚖️ Risk-Based Prioritizer & RMMM Framework")
    st.caption(
        "Prioritize test execution and engineering vigilance where failure consequences and volatility are highest. "
        "Calculated using standard SE risk formula: **`Risk Score = Impact × Complexity × (1 + Change_Count)`**."
    )

    badge_info = get_mode_badge()
    st.markdown(badge_info["badge_html"], unsafe_allow_html=True)
    st.write("")

    tab_tests, tab_rmmm, tab_reqs = st.tabs([
        "🧪 Risk-Prioritized Test Schedule",
        "🛡️ Top 5 RMMM Risk Matrix",
        "📊 Requirements Risk Ranking",
    ])

    # ---------------- TAB 1: TEST EXECUTION SCHEDULE ----------------
    with tab_tests:
        st.subheader("Test Execution Sequence (Sorted by Requirement Risk)")
        st.caption("Execute tests on volatile, high-impact, and complex components first to maximize early defect detection.")

        prioritized = get_prioritized_test_cases(project)

        if prioritized:
            table_rows = []
            for idx, pt in enumerate(prioritized, start=1):
                status_emoji = (
                    "✅" if pt["status"] == "Pass"
                    else ("❌" if pt["status"] == "Fail" else ("🔄" if pt["status"] == "Needs Review" else "⏸️"))
                )
                table_rows.append({
                    "Seq #": idx,
                    "Test ID": pt["test_id"],
                    "Risk Score": pt["risk_score"],
                    "Linked Req": pt["linked_req"],
                    "Req Priority": pt["req_priority"],
                    "Impact": pt["req_impact"],
                    "Complexity": pt["req_complexity"],
                    "Type": pt["type"],
                    "Status": f"{status_emoji} {pt['status']}",
                    "Test Title": pt["title"],
                })

            df_tests = pd.DataFrame(table_rows)
            st.dataframe(df_tests, use_container_width=True, hide_index=True)
        else:
            st.info("No test cases defined in project.")

    # ---------------- TAB 2: RMMM TABLE ----------------
    with tab_rmmm:
        st.subheader("🛡️ RMMM (Risk Mitigation, Monitoring & Management) Table")
        st.caption("Auto-generated risk mitigation strategies and telemetry monitoring metrics for the top 5 highest risk specifications.")

        rmmm_ctrl_col1, rmmm_ctrl_col2 = st.columns([3, 1])
        with rmmm_ctrl_col2:
            if st.button("🤖 AI Synthesize Strategies", use_container_width=True):
                sorted_reqs = sorted(project.requirements, key=calculate_requirement_risk, reverse=True)[:5]
                custom_db = {}
                with st.spinner("Synthesizing context-aware RMMM strategies..."):
                    for r in sorted_reqs:
                        strat, is_mock = generate_rmmm_mitigation_ai(r)
                        custom_db[r.id] = strat
                    st.session_state["custom_rmmm"] = custom_db
                    st.toast("RMMM strategies synthesized!", icon="✨")
                    st.rerun()

        custom_mitigations = st.session_state.get("custom_rmmm")
        rmmm_items = generate_rmmm_table(project, custom_mitigations=custom_mitigations)

        for item in rmmm_items:
            req_obj = project.get_requirement(item.req_id)
            with st.container():
                st.markdown(
                    f"### `{item.risk_id}`: [{item.req_id}] {item.risk_title} (Risk Score: `{item.risk_score}`)"
                )
                c_p, c_i, c_v = st.columns(3)
                with c_p:
                    st.markdown(f"**Probability:** `{item.probability}`")
                with c_i:
                    st.markdown(f"**Impact:** `{item.impact}/5`")
                with c_v:
                    st.markdown(f"**Volatility:** `{req_obj.change_count if req_obj else 0} revisions`")

                st.markdown(f"**🛡️ Mitigation Strategy:** {item.mitigation}")
                st.markdown(f"**📡 Monitoring Metric:** {item.monitoring}")
                st.markdown("---")

    # ---------------- TAB 3: REQUIREMENTS RISK RANKING ----------------
    with tab_reqs:
        st.subheader("Requirements Risk Distribution")

        sorted_reqs = sorted(project.requirements, key=calculate_requirement_risk, reverse=True)
        req_ids = [r.id for r in sorted_reqs]
        risk_scores = [calculate_requirement_risk(r) for r in sorted_reqs]
        priorities = [r.priority for r in sorted_reqs]

        fig_risk = go.Figure(
            go.Bar(
                x=risk_scores,
                y=req_ids,
                orientation="h",
                text=[f"Score: {s} ({p})" for s, p in zip(risk_scores, priorities)],
                textposition="auto",
                marker=dict(
                    color=risk_scores,
                    colorscale="Reds",
                    showscale=True,
                    colorbar=dict(title=dict(text="Risk Score", font=dict(color="#FFFFFF"))),
                ),
            )
        )
        fig_risk.update_layout(
            xaxis=dict(title="Risk Score (Impact × Complexity × [1 + Changes])", gridcolor="#334155"),
            yaxis=dict(autorange="reversed"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#F8FAFC", "family": "Inter, sans-serif"},
            height=420,
            margin=dict(l=25, r=25, t=20, b=25),
        )
        st.plotly_chart(fig_risk, use_container_width=True)
