"""
Requirements Manager Page for TraceLens.
Provides CRUD operations, configuration management (CM), version history tracking,
version rollback, completeness scoring, and volatility timeline analytics.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from core.models import Project, Requirement
from core.storage import save_project
from core.scoring import calculate_requirement_completeness
from core.ai_client import suggest_requirement_ai


def render_requirements_page(project: Project) -> None:
    """Render requirement management view, CM controls, and volatility timeline."""
    st.markdown("## 📋 Requirements Baseline Manager")
    st.caption("Maintain requirements baseline, audit version history, evaluate completeness, and track volatility.")

    tab_list, tab_add, tab_edit, tab_history, tab_volatility = st.tabs([
        "📑 Requirements Catalog",
        "➕ Add Requirement",
        "✏️ Edit / Delete",
        "⏳ Configuration Management & History",
        "📈 Volatility Timeline",
    ])

    # ---------------- TAB 1: CATALOG ----------------
    with tab_list:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_type = st.selectbox("Filter Type", ["All", "Functional", "Non-Functional"])
        with col_f2:
            filter_prio = st.selectbox("Filter Priority", ["All", "High", "Medium", "Low"])
        with col_f3:
            filter_status = st.selectbox("Filter Status", ["All", "Draft", "Approved", "Changed"])

        filtered_reqs = project.requirements
        if filter_type != "All":
            filtered_reqs = [r for r in filtered_reqs if r.type == filter_type]
        if filter_prio != "All":
            filtered_reqs = [r for r in filtered_reqs if r.priority == filter_prio]
        if filter_status != "All":
            filtered_reqs = [r for r in filtered_reqs if r.status == filter_status]

        rows = []
        for r in filtered_reqs:
            des_count = len(project.get_design_for_requirement(r.id))
            tests = project.get_tests_for_requirement(r.id)
            test_count = len(tests)
            
            # Coverage breakdown
            pass_c = sum(1 for t in tests if t.status == "Pass")
            fail_c = sum(1 for t in tests if t.status == "Fail")
            if test_count == 0:
                coverage_str = "⚠️ 0 (Uncovered)"
            else:
                coverage_str = f"✅ {test_count} ({pass_c}P / {fail_c}F)"

            # Completeness evaluation
            comp = calculate_requirement_completeness(project, r)
            comp_badge = f"{int(comp.score)}%"

            rows.append({
                "ID": r.id,
                "Type": r.type,
                "Priority": r.priority,
                "Status": r.status,
                "Completeness": comp_badge,
                "Test Coverage": coverage_str,
                "Design Elements": des_count,
                "Ver": f"v{r.version}",
                "Changes": r.change_count,
                "Requirement Statement": r.text,
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Displaying {len(df)} of {len(project.requirements)} requirements.")
        else:
            st.info("No requirements match the selected filter criteria.")

        # Detailed item completeness inspector
        with st.expander("🔍 Inspect Requirement Completeness Checklist"):
            inspect_req_id = st.selectbox("Select Requirement", [r.id for r in project.requirements])
            target_r = project.get_requirement(inspect_req_id)
            if target_r:
                c_info = calculate_requirement_completeness(project, target_r)
                ic1, ic2, ic3, ic4 = st.columns(4)
                with ic1:
                    st.markdown(f"**Verification Test:** {'✅ Linked' if c_info.has_test else '❌ Missing'}")
                with ic2:
                    st.markdown(f"**Design Element:** {'✅ Linked' if c_info.has_design else '❌ Missing'}")
                with ic3:
                    st.markdown(f"**Quantifiable Criteria:** {'✅ Found' if c_info.has_measurable else '❌ Missing'}")
                with ic4:
                    st.markdown(f"**Approval Status:** {'✅ Approved' if c_info.is_approved else f'⚠️ {target_r.status}'}")

                if c_info.missing:
                    st.warning("Gaps to resolve: " + "; ".join(c_info.missing))
                else:
                    st.success("Requirement meets all 4 engineering completeness criteria (100%).")

    # ---------------- TAB 2: ADD REQUIREMENT ----------------
    with tab_add:
        st.subheader("Add New Requirement Specification")

        # Propose next auto ID
        existing_ids = [r.id for r in project.requirements]
        numeric_ids = []
        for rid in existing_ids:
            if rid.startswith("R") and rid[1:].isdigit():
                numeric_ids.append(int(rid[1:]))
        next_num = max(numeric_ids, default=0) + 1
        default_id = f"R{next_num}"

        # AI Statement Assistant
        st.markdown("##### 🤖 IEEE 830 Requirement Auto-Completion")
        ai_col1, ai_col2 = st.columns([3, 1])
        with ai_col1:
            seed_topic = st.text_input(
                "Draft topic or rough notes",
                placeholder="e.g. driver GPS location refresh on map every 3 seconds",
                key="seed_topic_input",
            )
        with ai_col2:
            seed_type = st.selectbox("Spec Type", ["Functional", "Non-Functional"], key="seed_type_select")
            if st.button("✨ Suggest Statement", use_container_width=True):
                if seed_topic.strip():
                    suggested, is_mock = suggest_requirement_ai(seed_topic, seed_type)
                    st.session_state["suggested_req_text"] = suggested
                    mode_note = "Mock Engine" if is_mock else "Claude AI"
                    st.toast(f"Statement generated via {mode_note}!", icon="✨")
                else:
                    st.warning("Please type a topic or draft keywords above first.")

        initial_text = st.session_state.get("suggested_req_text", "")

        with st.form("add_req_form", clear_on_submit=True):
            col_id, col_type, col_prio = st.columns(3)
            with col_id:
                new_id = st.text_input("Requirement ID", value=default_id)
            with col_type:
                new_type = st.selectbox("Type", ["Functional", "Non-Functional"])
            with col_prio:
                new_prio = st.selectbox("Priority", ["High", "Medium", "Low"])

            new_text = st.text_area(
                "Requirement Text (Normative Statement)",
                value=initial_text,
                placeholder="The system shall validate customer inputs within 200ms...",
                help="Follow IEEE standards: use 'shall', identify an actor, specify measurable criteria.",
            )

            col_imp, col_comp = st.columns(2)
            with col_imp:
                new_impact = st.slider("Impact Score (1-5)", min_value=1, max_value=5, value=3)
            with col_comp:
                new_complexity = st.slider("Complexity Score (1-5)", min_value=1, max_value=5, value=3)

            submit_add = st.form_submit_button("➕ Create Requirement", type="primary")

            if submit_add:
                if not new_id.strip() or not new_text.strip():
                    st.error("Requirement ID and Text are required fields.")
                elif any(r.id == new_id.strip() for r in project.requirements):
                    st.error(f"Requirement with ID '{new_id.strip()}' already exists.")
                else:
                    new_req = Requirement(
                        id=new_id.strip(),
                        text=new_text.strip(),
                        type=new_type,
                        priority=new_prio,
                        impact=new_impact,
                        complexity=new_complexity,
                        version=1,
                        change_count=0,
                        status="Draft",
                    )
                    project.requirements.append(new_req)
                    save_project(project)
                    if "suggested_req_text" in st.session_state:
                        del st.session_state["suggested_req_text"]
                    st.success(f"Requirement **{new_req.id}** created successfully!")
                    st.rerun()

    # ---------------- TAB 3: EDIT / DELETE ----------------
    with tab_edit:
        st.subheader("Edit or Remove Requirement")
        req_options = {f"[{r.id}] ({r.priority}) {r.text[:60]}...": r.id for r in project.requirements}

        if not req_options:
            st.warning("No requirements available to modify.")
        else:
            selected_label = st.selectbox("Select Requirement to Edit", list(req_options.keys()))
            selected_id = req_options[selected_label]
            target_req = project.get_requirement(selected_id)

            if target_req:
                st.markdown(
                    f"**Current Status:** `{target_req.status}` | **Version:** `v{target_req.version}` | **Change Count:** `{target_req.change_count}`"
                )

                with st.form("edit_req_form"):
                    edit_text = st.text_area("Requirement Statement", value=target_req.text, height=120)
                    col_e1, col_e2, col_e3 = st.columns(3)
                    with col_e1:
                        edit_type = st.selectbox(
                            "Type",
                            ["Functional", "Non-Functional"],
                            index=0 if target_req.type == "Functional" else 1,
                        )
                    with col_e2:
                        edit_prio = st.selectbox(
                            "Priority",
                            ["High", "Medium", "Low"],
                            index=["High", "Medium", "Low"].index(target_req.priority),
                        )
                    with col_e3:
                        edit_status = st.selectbox(
                            "Status",
                            ["Draft", "Approved", "Changed"],
                            index=["Draft", "Approved", "Changed"].index(target_req.status),
                        )

                    col_i1, col_i2 = st.columns(2)
                    with col_i1:
                        edit_impact = st.slider("Impact (1-5)", 1, 5, value=target_req.impact)
                    with col_i2:
                        edit_comp = st.slider("Complexity (1-5)", 1, 5, value=target_req.complexity)

                    submit_save = st.form_submit_button("💾 Save Changes (Bump Version)", type="primary")

                    if submit_save:
                        target_req.type = edit_type
                        target_req.priority = edit_prio
                        target_req.impact = edit_impact
                        target_req.complexity = edit_comp
                        target_req.status = edit_status

                        target_req.update_text(edit_text, mark_changed=True)
                        save_project(project)
                        st.success(f"Requirement **{target_req.id}** updated to version v{target_req.version}!")
                        st.rerun()

                st.markdown("---")
                st.markdown("#### Danger Zone")
                with st.expander("🗑️ Delete This Requirement"):
                    st.warning(f"Are you sure you want to delete **{target_req.id}**? This cannot be undone.")
                    linked_tests = project.get_tests_for_requirement(target_req.id)
                    linked_design = project.get_design_for_requirement(target_req.id)
                    if linked_tests or linked_design:
                        st.info(
                            f"Notice: This requirement has {len(linked_design)} linked design element(s) and {len(linked_tests)} linked test case(s)."
                        )

                    if st.button("Permanently Delete Requirement", type="secondary"):
                        project.requirements = [r for r in project.requirements if r.id != target_req.id]
                        for d in project.design_elements:
                            if target_req.id in d.linked_reqs:
                                d.linked_reqs.remove(target_req.id)
                        save_project(project)
                        st.success(f"Requirement {target_req.id} removed from project.")
                        st.rerun()

    # ---------------- TAB 4: CM & VERSION HISTORY ----------------
    with tab_history:
        st.subheader("Configuration Management (CM) & Version Rollback")
        st.caption("TraceLens automatically records an immutable snapshot whenever a requirement changes.")

        history_req_options = {f"[{r.id}] v{r.version} - {r.text[:60]}...": r.id for r in project.requirements}
        sel_hist_label = st.selectbox("Select Requirement to Inspect History", list(history_req_options.keys()))
        sel_hist_id = history_req_options[sel_hist_label]
        hist_req = project.get_requirement(sel_hist_id)

        if hist_req:
            st.markdown(f"### Version History for **{hist_req.id}** (Current: `v{hist_req.version}`)")
            history_rows = []
            for h in hist_req.history:
                history_rows.append({
                    "Version": f"v{h.version}",
                    "Timestamp": h.timestamp,
                    "Requirement Text": h.text,
                    "Is Current": "✅ Current" if h.version == hist_req.version else "Historical",
                })
            df_hist = pd.DataFrame(history_rows)
            st.dataframe(df_hist, use_container_width=True, hide_index=True)

            if len(hist_req.history) > 1:
                st.markdown("#### ⏪ Rollback / Restore Revision")
                historical_versions = [h.version for h in hist_req.history if h.version != hist_req.version]
                selected_v = st.selectbox("Choose version to restore", historical_versions)

                target_snapshot = next((h for h in hist_req.history if h.version == selected_v), None)
                if target_snapshot:
                    st.text_area("Preview of Historical Text", value=target_snapshot.text, disabled=True)

                    if st.button(f"Restore Version v{selected_v}", type="primary"):
                        success = hist_req.restore_version(selected_v)
                        if success:
                            save_project(project)
                            st.success(f"Successfully restored v{selected_v}! New version is v{hist_req.version}.")
                            st.rerun()
            else:
                st.info("This requirement is currently at initial version (v1) with no prior revisions.")

    # ---------------- TAB 5: VOLATILITY TIMELINE ----------------
    with tab_volatility:
        st.subheader("📈 Requirement Volatility & Revision Timeline")
        st.caption("Chronological audit of requirement changes across project history to identify churning hotspots.")

        timeline_data = []
        for r in project.requirements:
            for h in r.history:
                timeline_data.append({
                    "Requirement": r.id,
                    "Version": f"v{h.version}",
                    "Timestamp": h.timestamp,
                    "Change Count": r.change_count,
                    "Priority": r.priority,
                    "Text Snapshot": h.text,
                })

        if timeline_data:
            df_time = pd.DataFrame(timeline_data)
            fig_vol = px.scatter(
                df_time,
                x="Timestamp",
                y="Requirement",
                color="Priority",
                size=[max(8, int(c) * 4 + 8) for c in df_time["Change Count"]],
                hover_data=["Version", "TextSnapshot" if "TextSnapshot" in df_time.columns else "Version"],
                title="Requirement Revision Events Over Time",
                color_discrete_map={"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"},
            )
            fig_vol.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15, 23, 42, 0.5)",
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_vol, use_container_width=True)

            # Volatility Leaderboard
            st.markdown("##### 🔥 Most Volatile Requirements (Churn Hotspots)")
            churners = sorted(project.requirements, key=lambda x: x.change_count, reverse=True)
            top_churners = [
                {
                    "ID": r.id,
                    "Revisions": r.version,
                    "Total Changes": r.change_count,
                    "Priority": r.priority,
                    "Status": r.status,
                    "Text": r.text,
                }
                for r in churners[:5]
            ]
            st.dataframe(pd.DataFrame(top_churners), use_container_width=True, hide_index=True)
        else:
            st.info("No revision history recorded yet.")
