"""
Test Case Generator and Test Run Tracker Page for TraceLens.
Supports AI/mock test synthesis, bulk test generation for uncovered specifications,
defect tracking, tester comments, and interactive test status updates.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd

from core.models import Project, TestCase
from core.ai_client import generate_tests_for_requirement, get_mode_badge
from core.storage import save_project


def render_tests_page(project: Project) -> None:
    """Render test generator and test run tracking controls."""
    st.markdown("## 🧪 Test Case Generator & Execution Tracker")
    st.caption(
        "Synthesize comprehensive test suites (positive, negative, boundary, security/performance) "
        "and track test execution outcomes with live defect and observation logging."
    )

    badge_info = get_mode_badge()
    st.markdown(badge_info["badge_html"], unsafe_allow_html=True)
    st.write("")

    total_tests = len(project.test_cases)
    passed_tests = sum(1 for t in project.test_cases if t.status == "Pass")
    failed_tests = sum(1 for t in project.test_cases if t.status == "Fail")
    review_tests = sum(1 for t in project.test_cases if t.status == "Needs Review")
    not_run_tests = sum(1 for t in project.test_cases if t.status == "Not Run")
    pass_rate = round((passed_tests / total_tests * 100), 1) if total_tests > 0 else 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Tests", f"{total_tests}")
    with col2:
        st.metric("Pass Rate", f"{pass_rate}%")
    with col3:
        st.metric("Passed", f"{passed_tests}")
    with col4:
        st.metric("Failed (Defects)", f"{failed_tests}", delta=f"{failed_tests} fails", delta_color="inverse")
    with col5:
        st.metric("Needs Review", f"{review_tests}")

    st.markdown("---")

    tab_gen, tab_track = st.tabs(["⚡ Automated Test Generator", "📋 Test Execution & Runner"])

    # ---------------- TAB 1: TEST GENERATOR ----------------
    with tab_gen:
        st.subheader("Automated Test Case Generation")

        covered_req_ids = {t.linked_req for t in project.test_cases if t.linked_req}
        uncovered_reqs = [r for r in project.requirements if r.id not in covered_req_ids]

        st.markdown(
            f"Currently **{len(uncovered_reqs)} of {len(project.requirements)}** requirements lack test coverage."
        )

        col_b1, col_b2 = st.columns([1, 1.2])

        with col_b1:
            st.markdown("#### Single Requirement Test Generator")
            req_choices = {f"[{r.id}] ({r.priority}) {r.text[:60]}...": r.id for r in project.requirements}
            selected_label = st.selectbox("Select Target Requirement", list(req_choices.keys()))
            selected_req_id = req_choices[selected_label]
            target_req = project.get_requirement(selected_req_id)

            if target_req:
                st.caption(f"Full text: *\"{target_req.text}\"*")
                btn_single_gen = st.button(f"Generate 3-4 Tests for {target_req.id}", type="primary")

                if btn_single_gen:
                    with st.spinner("Generating positive, negative, boundary, and security test cases..."):
                        numeric_tids = [int(t.id[1:]) for t in project.test_cases if t.id.startswith("T") and t.id[1:].isdigit()]
                        next_tid = max(numeric_tids) + 1 if numeric_tids else 1

                        new_tests, is_mock = generate_tests_for_requirement(target_req, next_tid)
                        project.test_cases.extend(new_tests)
                        save_project(project)
                        mode_str = "Offline Mock Engine" if is_mock else "Claude AI"
                        st.success(f"Generated {len(new_tests)} test cases for {target_req.id} via {mode_str}!")
                        st.rerun()

        with col_b2:
            st.markdown("#### Bulk Test Generator")
            st.markdown("Instantly generate verification suites for all uncovered requirements in a single batch.")
            if uncovered_reqs:
                st.warning(f"Found {len(uncovered_reqs)} uncovered requirements: {', '.join([r.id for r in uncovered_reqs])}")
                if st.button("🚀 Generate Tests for ALL Uncovered Requirements", type="primary"):
                    with st.spinner(f"Synthesizing test suites for {len(uncovered_reqs)} requirements..."):
                        total_added = 0
                        for req in uncovered_reqs:
                            numeric_tids = [int(t.id[1:]) for t in project.test_cases if t.id.startswith("T") and t.id[1:].isdigit()]
                            next_tid = max(numeric_tids) + 1 if numeric_tids else 1
                            new_tests, _ = generate_tests_for_requirement(req, next_tid)
                            project.test_cases.extend(new_tests)
                            total_added += len(new_tests)
                        save_project(project)
                        st.balloons()
                        st.success(f"Successfully generated and linked {total_added} test cases across all {len(uncovered_reqs)} uncovered requirements!")
                        st.rerun()
            else:
                st.success("🎉 Excellent! 100% of requirements have at least one verifying test case.")

    # ---------------- TAB 2: TEST RUN TRACKER ----------------
    with tab_track:
        st.subheader("Test Execution Suite & Status Manager")

        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            filter_status = st.selectbox(
                "Filter by Execution Status",
                ["All", "Pass", "Fail", "Needs Review", "Not Run"],
            )
        with filter_col2:
            filter_type = st.selectbox(
                "Filter by Test Level",
                ["All", "Unit", "Integration", "System", "Acceptance"],
            )

        display_tests = project.test_cases
        if filter_status != "All":
            display_tests = [t for t in display_tests if t.status == filter_status]
        if filter_type != "All":
            display_tests = [t for t in display_tests if t.type == filter_type]

        st.caption(f"Showing {len(display_tests)} of {len(project.test_cases)} tests.")

        status_colors = {
            "Pass": "green",
            "Fail": "red",
            "Needs Review": "orange",
            "Not Run": "gray",
        }

        for tc in display_tests:
            status_color = status_colors.get(tc.status, "gray")
            defect_tag = f" | ⚠️ {tc.defect_severity}" if tc.defect_severity != "None" else ""

            with st.expander(f"[{tc.id}] {tc.title} (:{status_color}[{tc.status}]{defect_tag}) - {tc.type}"):
                c_details, c_actions = st.columns([2, 1.2])

                with c_details:
                    st.markdown(f"**Linked Requirement:** `{tc.linked_req}` | **Level:** `{tc.type}` | **Auto-Generated:** `{tc.auto_generated}`")
                    st.markdown("**Execution Steps:**")
                    for s in tc.steps:
                        st.markdown(f"  - {s}")
                    st.markdown(f"**Expected Outcome:** {tc.expected}")

                    if tc.defect_notes:
                        st.markdown(f"🐞 **Defect Notes:** {tc.defect_notes}")
                    if tc.execution_comment:
                        st.markdown(f"💬 **Comment:** {tc.execution_comment}")

                with c_actions:
                    st.markdown("**Update Status:**")
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("✅ Pass", key=f"pass_{tc.id}", width="stretch"):
                            tc.status = "Pass"
                            if tc.defect_severity == "Critical":
                                tc.defect_severity = "None"
                            save_project(project)
                            st.rerun()
                        if st.button("❌ Fail", key=f"fail_{tc.id}", width="stretch"):
                            tc.status = "Fail"
                            if tc.defect_severity == "None":
                                tc.defect_severity = "High"
                            save_project(project)
                            st.rerun()
                    with b2:
                        if st.button("🔄 Review", key=f"rev_{tc.id}", width="stretch"):
                            tc.status = "Needs Review"
                            save_project(project)
                            st.rerun()
                        if st.button("⏸️ Reset", key=f"rst_{tc.id}", width="stretch"):
                            tc.status = "Not Run"
                            save_project(project)
                            st.rerun()

                # Defect notes & comment editing form
                with st.form(f"defect_form_{tc.id}"):
                    st.markdown("##### 📝 Defect & Execution Notes")
                    f1, f2 = st.columns([1, 2])
                    with f1:
                        sev_options = ["None", "Low", "Medium", "High", "Critical"]
                        cur_sev_idx = sev_options.index(tc.defect_severity) if tc.defect_severity in sev_options else 0
                        new_sev = st.selectbox("Defect Severity", sev_options, index=cur_sev_idx, key=f"sev_{tc.id}")
                    with f2:
                        new_comment = st.text_input("Execution Observation / Comment", value=tc.execution_comment, key=f"comm_{tc.id}")
                    new_defect = st.text_area("Bug Details / Root Cause / Reproduction Steps", value=tc.defect_notes, height=70, key=f"def_{tc.id}")

                    if st.form_submit_button("💾 Save Defect Notes", type="secondary"):
                        tc.defect_severity = new_sev
                        tc.execution_comment = new_comment.strip()
                        tc.defect_notes = new_defect.strip()
                        save_project(project)
                        st.toast(f"Notes saved for {tc.id}!", icon="💾")
                        st.rerun()
