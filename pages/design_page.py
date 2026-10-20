"""
Design Elements Manager Page for TraceLens.
Provides CRUD operations, architecture mapping, and coverage metrics for design elements.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px

from core.models import Project, DesignElement
from core.storage import save_project


def render_design_page(project: Project) -> None:
    """Render the Design Elements Manager Page."""
    st.markdown("## 🏛️ Design Elements Manager")
    st.caption("Manage architectural units (Modules, Classes, APIs, DB Tables) and their requirement bindings.")

    design_elements = project.design_elements
    requirements = project.requirements
    all_req_ids = [r.id for r in requirements]

    # Metrics overview
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Elements", len(design_elements))
    with col2:
        modules = sum(1 for d in design_elements if d.kind == "Module")
        st.metric("Modules", modules)
    with col3:
        apis = sum(1 for d in design_elements if d.kind == "API")
        st.metric("APIs", apis)
    with col4:
        db_tables = sum(1 for d in design_elements if d.kind == "DB Table")
        st.metric("DB Tables", db_tables)
    with col5:
        classes = sum(1 for d in design_elements if d.kind == "Class")
        st.metric("Classes", classes)

    st.write("")

    # Tabs for Catalog, Add, Edit/Delete, and Analytics
    tab_catalog, tab_add, tab_edit, tab_analytics = st.tabs([
        "📋 Design Catalog",
        "➕ Add Design Element",
        "✏️ Edit & Manage",
        "📊 Architecture Analytics",
    ])

    # Tab 1: Design Catalog
    with tab_catalog:
        st.subheader("Architectural Baseline Catalog")
        
        filter_col1, filter_col2 = st.columns([2, 1])
        with filter_col1:
            search_query = st.text_input("🔍 Search by ID or Name", "", placeholder="e.g. D1, Payment, Router...")
        with filter_col2:
            kind_filter = st.selectbox("Filter by Kind", ["All", "Module", "Class", "API", "DB Table"])

        filtered = design_elements
        if kind_filter != "All":
            filtered = [d for d in filtered if d.kind == kind_filter]
        if search_query.strip():
            sq = search_query.lower()
            filtered = [d for d in filtered if sq in d.id.lower() or sq in d.name.lower()]

        if not filtered:
            st.info("No design elements match your filter criteria.")
        else:
            table_data = []
            for d in filtered:
                table_data.append({
                    "Element ID": d.id,
                    "Name": d.name,
                    "Kind": d.kind,
                    "Linked Requirements": ", ".join(d.linked_reqs) if d.linked_reqs else "(Orphan)",
                    "Req Count": len(d.linked_reqs),
                })
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # Tab 2: Add Design Element
    with tab_add:
        st.subheader("Register New Architectural Element")

        # Propose next ID
        existing_numbers = []
        for d in design_elements:
            if d.id.startswith("D") and d.id[1:].isdigit():
                existing_numbers.append(int(d.id[1:]))
        next_num = max(existing_numbers, default=0) + 1
        suggested_id = f"D{next_num}"

        with st.form("add_design_element_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns([1, 2])
            with f_col1:
                new_id = st.text_input("Element ID", value=suggested_id)
                new_kind = st.selectbox("Kind", ["Module", "Class", "API", "DB Table"], index=0)
            with f_col2:
                new_name = st.text_input("Element Name", placeholder="e.g. DeliveryDispatchRouter")
                linked_reqs = st.multiselect(
                    "Link to Requirements",
                    options=all_req_ids,
                    help="Select the functional and non-functional requirements implemented or realized by this element."
                )

            submitted = st.form_submit_button("➕ Register Design Element", type="primary")
            if submitted:
                clean_id = new_id.strip()
                clean_name = new_name.strip()
                if not clean_id or not clean_name:
                    st.error("Both Element ID and Name are required.")
                elif any(d.id.lower() == clean_id.lower() for d in design_elements):
                    st.error(f"Design Element ID '{clean_id}' already exists!")
                else:
                    new_elem = DesignElement(
                        id=clean_id,
                        name=clean_name,
                        kind=new_kind,
                        linked_reqs=linked_reqs,
                    )
                    project.design_elements.append(new_elem)
                    save_project(project)
                    st.toast(f"Design Element '{clean_id}' successfully added!", icon="✅")
                    st.rerun()

    # Tab 3: Edit & Manage
    with tab_edit:
        st.subheader("Modify or Delete Existing Element")
        if not design_elements:
            st.info("No design elements available to edit.")
        else:
            element_options = {f"{d.id} - {d.name} ({d.kind})": d.id for d in design_elements}
            selected_label = st.selectbox("Select Element to Modify", list(element_options.keys()))
            target_id = element_options[selected_label]
            target_element = project.get_design_element(target_id)

            if target_element:
                with st.form("edit_design_form"):
                    e_col1, e_col2 = st.columns([1, 2])
                    with e_col1:
                        st.text_input("Element ID (Read-only)", value=target_element.id, disabled=True)
                        edit_kind = st.selectbox(
                            "Kind",
                            ["Module", "Class", "API", "DB Table"],
                            index=["Module", "Class", "API", "DB Table"].index(target_element.kind) if target_element.kind in ["Module", "Class", "API", "DB Table"] else 0,
                        )
                    with e_col2:
                        edit_name = st.text_input("Name", value=target_element.name)
                        edit_linked_reqs = st.multiselect(
                            "Linked Requirements",
                            options=all_req_ids,
                            default=[r for r in target_element.linked_reqs if r in all_req_ids],
                        )

                    save_changes = st.form_submit_button("💾 Save Changes", type="primary")
                    if save_changes:
                        target_element.name = edit_name.strip()
                        target_element.kind = edit_kind
                        target_element.linked_reqs = edit_linked_reqs
                        save_project(project)
                        st.toast(f"Element {target_id} updated!", icon="✅")
                        st.rerun()

                st.write("")
                st.markdown("#### ⚠️ Danger Zone")
                with st.expander(f"Delete Element {target_id}", expanded=False):
                    st.warning(f"Are you sure you want to permanently delete design element **{target_id} - {target_element.name}**? This will remove its references from the traceability graph.")
                    if st.button("🗑️ Confirm Delete Element", type="secondary", key=f"del_{target_id}"):
                        project.design_elements = [d for d in project.design_elements if d.id != target_id]
                        save_project(project)
                        st.toast(f"Element {target_id} deleted.", icon="🗑️")
                        st.rerun()

    # Tab 4: Architecture Analytics
    with tab_analytics:
        st.subheader("Architectural Decomposition & Linkage Density")
        
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            kind_counts = pd.Series([d.kind for d in design_elements]).value_counts().reset_index()
            kind_counts.columns = ["Kind", "Count"]
            fig_kind = px.pie(
                kind_counts,
                names="Kind",
                values="Count",
                title="Design Elements by Kind",
                color_discrete_sequence=["#3B82F6", "#8B5CF6", "#10B981", "#F59E0B"],
                hole=0.45,
            )
            fig_kind.update_layout(template="plotly_dark", margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_kind, use_container_width=True)

        with chart_col2:
            link_counts = pd.DataFrame([
                {"ID": d.id, "Name": d.name, "Linked Reqs": len(d.linked_reqs)}
                for d in design_elements
            ]).sort_values("Linked Reqs", ascending=True)
            
            fig_links = px.bar(
                link_counts,
                x="Linked Reqs",
                y="ID",
                orientation="h",
                title="Requirements per Design Element",
                text="Linked Reqs",
                color="Linked Reqs",
                color_continuous_scale="Purples",
            )
            fig_links.update_layout(template="plotly_dark", margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_links, use_container_width=True)
