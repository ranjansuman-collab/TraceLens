"""
Traceability Matrix Page for TraceLens.
Renders bi-directional requirements-to-design and requirements-to-test cross-reference
matrices with checkmarks, filters, and CSV export.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd

from core.models import Project
from core.exporter import generate_traceability_matrix_csv


def render_traceability_page(project: Project) -> None:
    """Render the traceability matrix views and CSV export."""
    st.markdown("## 🔗 Bi-Directional Traceability Matrix")
    st.markdown(
        "Trace requirements to architectural design elements and verifying test assets. "
        "Filter by priority or type and export the certified verification matrix to CSV."
    )

    # Filter Bar
    fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1.2])
    with fc1:
        f_prio = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
    with fc2:
        f_type = st.selectbox("Type", ["All", "Functional", "Non-Functional"])
    with fc3:
        f_cov = st.selectbox("Coverage", ["All", "Covered Only", "Uncovered Only"])
    with fc4:
        st.write("")
        csv_data = generate_traceability_matrix_csv(project)
        st.download_button(
            label="📥 Export Matrix (CSV)",
            data=csv_data,
            file_name="traceability_matrix.csv",
            mime="text/csv",
            type="primary",
            width="stretch",
        )

    # Filtered Requirements
    reqs = project.requirements
    if f_prio != "All":
        reqs = [r for r in reqs if r.priority == f_prio]
    if f_type != "All":
        reqs = [r for r in reqs if r.type == f_type]
    if f_cov == "Covered Only":
        reqs = [r for r in reqs if project.get_tests_for_requirement(r.id)]
    elif f_cov == "Uncovered Only":
        reqs = [r for r in reqs if not project.get_tests_for_requirement(r.id)]

    tab_tests, tab_design, tab_ledger = st.tabs([
        "🧪 Requirements ⟷ Tests Matrix",
        "🏛️ Requirements ⟷ Design Matrix",
        "📑 Comprehensive Traceability Ledger",
    ])

    # ---------------- TAB 1: REQ X TESTS ----------------
    with tab_tests:
        st.subheader("Requirements × Tests Verification Grid")
        test_ids = [t.id for t in project.test_cases]

        grid_rows = []
        for r in reqs:
            linked_tests = {t.id for t in project.get_tests_for_requirement(r.id)}
            row = {
                "Req ID": r.id,
                "Priority": r.priority,
                "Statement": r.text[:55] + "...",
            }
            for tid in test_ids:
                row[tid] = "✔" if tid in linked_tests else "·"
            grid_rows.append(row)

        df_grid = pd.DataFrame(grid_rows)
        if not df_grid.empty:
            st.dataframe(df_grid, width="stretch", hide_index=True)
            st.caption("✔ indicates requirement is directly verified by the test case column.")
        else:
            st.info("No requirements match current filter.")

    # ---------------- TAB 2: REQ X DESIGN ----------------
    with tab_design:
        st.subheader("Requirements × Design Architecture Grid")
        design_elements = project.design_elements

        design_rows = []
        for r in reqs:
            row = {
                "Req ID": r.id,
                "Type": r.type,
                "Priority": r.priority,
                "Statement": r.text[:55] + "...",
            }
            for des in design_elements:
                row[f"{des.id} ({des.kind})"] = "✔" if r.id in des.linked_reqs else "·"
            design_rows.append(row)

        df_des_grid = pd.DataFrame(design_rows)
        if not df_des_grid.empty:
            st.dataframe(df_des_grid, width="stretch", hide_index=True)
            st.caption("✔ indicates requirement is realized by the architectural design element column.")
        else:
            st.info("No requirements match current filter.")

    # ---------------- TAB 3: COMPREHENSIVE LEDGER ----------------
    with tab_ledger:
        st.subheader("Complete Bi-Directional Traceability Ledger")
        ledger_rows = []
        for r in reqs:
            linked_d = [f"{d.id}: {d.name}" for d in project.get_design_for_requirement(r.id)]
            linked_t = [f"{t.id} [{t.status}]" for t in project.get_tests_for_requirement(r.id)]
            cov_badge = "✅ Covered" if linked_t else "⚠️ UNCOVERED"

            ledger_rows.append({
                "ID": r.id,
                "Type": r.type,
                "Priority": r.priority,
                "Version": f"v{r.version}",
                "Status": r.status,
                "Requirement Text": r.text,
                "Design Realization": ", ".join(linked_d) if linked_d else "None",
                "Verification Tests": ", ".join(linked_t) if linked_t else "None",
                "Coverage Status": cov_badge,
            })

        df_ledger = pd.DataFrame(ledger_rows)
        if not df_ledger.empty:
            st.dataframe(df_ledger, width="stretch", hide_index=True)
        else:
            st.info("No requirements match current filter.")
