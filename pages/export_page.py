"""
Export Pack Page for TraceLens.
Generates one-click downloadable ZIP archive containing SRS.md, TestPlan.md,
traceability_matrix.csv, and quality_report.md, with live in-app artifact previews.
"""

from __future__ import annotations
import streamlit as st
import io
import pandas as pd

from core.models import Project
from core.exporter import (
    generate_export_zip,
    generate_srs_markdown,
    generate_test_plan_markdown,
    generate_traceability_matrix_csv,
    generate_quality_report_markdown,
)


def render_export_page(project: Project) -> None:
    """Render export generator and live documentation previews."""
    st.markdown("## 📦 Engineering Artifact Export Pack")
    st.markdown(
        "Generate and download the complete software engineering documentation bundle in one click. "
        "Contains standard IEEE specifications, test plans, traceability matrix, and quality audits."
    )

    zip_bytes = generate_export_zip(project)

    st.download_button(
        label="📦 Download Complete Export Pack (.ZIP)",
        data=zip_bytes,
        file_name="tracelens_export_pack.zip",
        mime="application/zip",
        type="primary",
        width="stretch",
    )

    st.markdown("---")
    st.subheader("👁️ Live In-App Artifact Previews")

    tab_srs, tab_tp, tab_matrix, tab_qr = st.tabs([
        "📄 SRS.md (IEEE 830)",
        "🧪 TestPlan.md (IEEE 829)",
        "📊 traceability_matrix.csv",
        "📈 quality_report.md",
    ])

    # ---------------- TAB 1: SRS.MD ----------------
    with tab_srs:
        srs_content = generate_srs_markdown(project)
        st.download_button(
            "Download SRS.md",
            data=srs_content,
            file_name="SRS.md",
            mime="text/markdown",
        )
        st.markdown(srs_content)

    # ---------------- TAB 2: TESTPLAN.MD ----------------
    with tab_tp:
        tp_content = generate_test_plan_markdown(project)
        st.download_button(
            "Download TestPlan.md",
            data=tp_content,
            file_name="TestPlan.md",
            mime="text/markdown",
        )
        st.markdown(tp_content)

    # ---------------- TAB 3: TRACEABILITY MATRIX CSV ----------------
    with tab_matrix:
        csv_content = generate_traceability_matrix_csv(project)
        st.download_button(
            "Download traceability_matrix.csv",
            data=csv_content,
            file_name="traceability_matrix.csv",
            mime="text/csv",
        )
        try:
            df_csv = pd.read_csv(io.StringIO(csv_content))
            st.dataframe(df_csv, width="stretch", hide_index=True)
        except Exception:
            st.code(csv_content, language="csv")

    # ---------------- TAB 4: QUALITY REPORT ----------------
    with tab_qr:
        qr_content = generate_quality_report_markdown(project)
        st.download_button(
            "Download quality_report.md",
            data=qr_content,
            file_name="quality_report.md",
            mime="text/markdown",
        )
        st.markdown(qr_content)
