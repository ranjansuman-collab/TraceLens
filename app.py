"""
TraceLens - Living Requirements-to-Test Traceability & Quality Intelligence System.
Main Streamlit application entry point.
"""

from __future__ import annotations
import streamlit as st
from pathlib import Path

# Configure page metadata first
st.set_page_config(
    page_title="TraceLens - Requirements Traceability & Quality Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.models import Project
from core.storage import (
    load_project,
    save_project,
    reset_to_sample_data,
    list_available_projects,
    create_new_project,
    DATA_DIR,
)
from core.ai_client import get_mode_badge
from core.scoring import calculate_quality_health

# Page renderers
from pages.dashboard_page import render_dashboard
from pages.requirements_page import render_requirements_page
from pages.design_page import render_design_page
from pages.linter_page import render_linter_page
from pages.tests_page import render_tests_page
from pages.traceability_page import render_traceability_page
from pages.graph_page import render_graph_page
from pages.req_dependency_page import render_req_dependency_page
from pages.impact_page import render_impact_page
from pages.heatmap_page import render_heatmap_page
from pages.risk_page import render_risk_page
from pages.export_page import render_export_page


def inject_custom_styles(dark_mode: bool = True) -> None:
    """Inject modern glassmorphic styling adapted for dark or light mode."""
    if dark_mode:
        st.markdown(
            """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }

            /* Metric cards styling */
            div[data-testid="stMetric"] {
                background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 14px 18px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
                transition: transform 0.2s ease, border-color 0.2s ease;
            }
            div[data-testid="stMetric"]:hover {
                transform: translateY(-2px);
                border-color: rgba(56, 189, 248, 0.4);
            }

            /* Sidebar enhancement */
            section[data-testid="stSidebar"] {
                background-color: #0B1120;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
            }

            /* Primary action button accents */
            button[kind="primary"] {
                background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
                border: none;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.2s ease;
            }
            button[kind="primary"]:hover {
                background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
            }

            /* Expander headers */
            div[data-testid="stExpander"] {
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 10px;
                background-color: rgba(15, 23, 42, 0.5);
                margin-bottom: 8px;
            }

            /* Hide default Streamlit multi-page sidebar navigation */
            [data-testid="stSidebarNav"] {
                display: none !important;
            }

            /* Brand header gradient */
            .brand-badge {
                background: linear-gradient(90deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }

            /* Hide default Streamlit multi-page sidebar navigation */
            [data-testid="stSidebarNav"] {
                display: none !important;
            }

            /* Metric cards light styling */
            div[data-testid="stMetric"] {
                background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
                border: 1px solid #CBD5E1;
                border-radius: 12px;
                padding: 14px 18px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }

            /* Sidebar enhancement */
            section[data-testid="stSidebar"] {
                background-color: #F8FAFC;
                border-right: 1px solid #E2E8F0;
            }

            .brand-badge {
                background: linear-gradient(90deg, #0284C7 0%, #4F46E5 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
            }
            </style>

            """,
            unsafe_allow_html=True,
        )


def initialize_session() -> Project:
    """Initialize or load active project into session state."""
    if "active_project_file" not in st.session_state:
        st.session_state.active_project_file = "project.json"

    current_path = DATA_DIR / st.session_state.active_project_file
    if "project" not in st.session_state:
        st.session_state.project = load_project(current_path)

    return st.session_state.project


def main() -> None:
    """Main application loop."""
    # Dark Mode Preference
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True

    inject_custom_styles(dark_mode=st.session_state.dark_mode)
    project = initialize_session()

    # Sidebar
    with st.sidebar:
        st.markdown(
            "## 🔬 <span class='brand-badge'>TraceLens</span>",
            unsafe_allow_html=True,
        )
        st.caption("Living Requirements Traceability & Quality Intelligence")

        # Mode Badge & Dark Mode Switch
        mode_col, theme_col = st.columns([1.6, 1])
        with mode_col:
            badge_info = get_mode_badge()
            st.markdown(badge_info["badge_html"], unsafe_allow_html=True)
        with theme_col:
            dark_toggle = st.toggle("🌙 Dark", value=st.session_state.dark_mode)
            if dark_toggle != st.session_state.dark_mode:
                st.session_state.dark_mode = dark_toggle
                st.rerun()

        st.write("")

        # Multi-Project Selector
        st.markdown("##### 📁 Project Baseline")
        available_projects = list_available_projects()
        cur_idx = available_projects.index(st.session_state.active_project_file) if st.session_state.active_project_file in available_projects else 0
        selected_file = st.selectbox("Active Workspace File", available_projects, index=cur_idx, label_visibility="collapsed")
        
        if selected_file != st.session_state.active_project_file:
            st.session_state.active_project_file = selected_file
            st.session_state.project = load_project(DATA_DIR / selected_file)
            st.rerun()

        # Quick Actions Popover
        with st.popover("⚡ Quick Actions & New Project"):
            st.markdown("#### Quick Shortcuts")
            if st.button("➕ Jump to Requirements", width="stretch"):
                st.session_state["nav_page"] = "📋 Requirements Manager"
                st.rerun()
            if st.button("🔍 Run Quality Linter", width="stretch"):
                st.session_state["nav_page"] = "🔍 Quality Linter & AI Refactoring"
                st.rerun()
            if st.button("💥 Simulate Change Blast Radius", width="stretch"):
                st.session_state["nav_page"] = "💥 Change Impact Simulator"
                st.rerun()
            
            st.markdown("---")
            st.markdown("#### Create New Project File")
            new_p_name = st.text_input("Project Name", placeholder="e.g. Telemedicine App")
            new_p_file = st.text_input("File Name", placeholder="e.g. telemedicine.json")
            if st.button("Create Project", type="primary", width="stretch"):
                if new_p_name and new_p_file:
                    safe_file = new_p_file if new_p_file.endswith(".json") else f"{new_p_file}.json"
                    created_proj = create_new_project(new_p_name, safe_file)
                    st.session_state.active_project_file = safe_file
                    st.session_state.project = created_proj
                    st.toast(f"Created project {new_p_name}!", icon="📁")
                    st.rerun()

        st.write("")

        # Navigation menu
        pages = {
            "📊 Dashboard": render_dashboard,
            "📋 Requirements Manager": render_requirements_page,
            "🏛️ Design Elements": render_design_page,
            "🔍 Quality Linter & AI Refactoring": render_linter_page,
            "🧪 Test Generator & Runner": render_tests_page,
            "🔗 Traceability Matrix": render_traceability_page,
            "🕸️ Live Full Graph": render_graph_page,
            "🧬 Req Dependencies & Conflicts": render_req_dependency_page,
            "💥 Change Impact Simulator": render_impact_page,
            "🗺️ Test Gap Heatmap": render_heatmap_page,
            "⚖️ Risk Prioritizer & RMMM": render_risk_page,
            "📦 Export Pack": render_export_page,
        }

        # Handle programmed navigation jumps
        default_nav_idx = 0
        if "nav_page" in st.session_state and st.session_state["nav_page"] in pages:
            default_nav_idx = list(pages.keys()).index(st.session_state["nav_page"])
            del st.session_state["nav_page"]

        selected_page = st.radio(
            "Navigation",
            list(pages.keys()),
            index=default_nav_idx,
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Quick Baseline Metrics in Sidebar
        health = calculate_quality_health(project)
        st.markdown("#### Baseline Summary")
        st.markdown(
            f"- **Composite Health:** `{health.composite_score}/100`\n"
            f"- **Requirements:** `{len(project.requirements)}`\n"
            f"- **Design Elements:** `{len(project.design_elements)}`\n"
            f"- **Test Cases:** `{len(project.test_cases)}`\n"
            f"- **Weighted Coverage:** `{health.test_coverage_weighted}%`"
        )

        st.markdown("---")
        st.markdown("#### Demo Controls")
        if st.button("🔄 Reset Demo Data", type="secondary", width="stretch"):
            fresh_project = reset_to_sample_data(DATA_DIR / st.session_state.active_project_file)
            st.session_state.project = fresh_project
            if "current_impact" in st.session_state:
                del st.session_state["current_impact"]
            if "pending_rewrites" in st.session_state:
                del st.session_state["pending_rewrites"]
            st.toast("Project restored to sample baseline!", icon="🔄")
            st.rerun()

        # Student Onboarding Tour
        with st.expander("🎓 SE Course Student Tour"):
            st.markdown(
                """
                **Welcome to TraceLens!**
                - **1. Dashboard:** Monitor ISO 25010 health and live Pytest coverage.
                - **2. Requirements:** Author IEEE 830 user stories with AI completions.
                - **3. Design Elements:** Realize modules, APIs, and database tables.
                - **4. Quality Linter:** Detect vague words, contradictions, and duplicates.
                - **5. Test Runner:** Execute verification tests and log defect notes.
                - **6. Impact Simulator:** Run BFS blast-radius analysis before committing changes.
                """
            )

        st.caption("University SE Course Demo Project • TraceLens v2.0.0")

    # Render selected page
    render_func = pages[selected_page]
    render_func(project)


if __name__ == "__main__":
    main()
