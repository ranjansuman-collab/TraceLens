"""
Requirement Quality Linter & AI Rewrite Page for TraceLens.
Evaluates requirements quality against IEEE/INCOSE criteria, flags semantic contradictions,
detects duplicate/overlapping requirements, and provides automated AI refactoring.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd

from core.models import Project
from core.linter import lint_requirement, detect_conflicts, detect_duplicates, compute_diff
from core.ai_client import rewrite_requirement_ai, analyze_conflict_ai, get_mode_badge
from core.storage import save_project


def render_linter_page(project: Project) -> None:
    """Render the automated quality inspection and AI rewrite interface."""
    st.markdown("## 🔍 Requirement Quality Linter & AI Refactoring")
    st.caption(
        "Automated rule-based quality evaluation against IEEE/INCOSE standards. Detects ambiguity, missing metrics, "
        "syntactic defects, semantic contradictions, and duplicate statements."
    )

    badge_info = get_mode_badge()
    st.markdown(badge_info["badge_html"], unsafe_allow_html=True)
    st.write("")

    # Run linter across all requirements
    results = [lint_requirement(r) for r in project.requirements]
    conflicts = detect_conflicts(project.requirements)
    duplicates = detect_duplicates(project.requirements)

    avg_score = round(sum(r.score for r in results) / len(results), 1) if results else 0.0
    green_count = sum(1 for r in results if r.grade == "Green")
    amber_count = sum(1 for r in results if r.grade == "Amber")
    red_count = sum(1 for r in results if r.grade == "Red")

    col_s1, col_s2, col_s3, col_s4, col_s5, col_s6 = st.columns(6)
    with col_s1:
        st.metric("Avg Clarity Score", f"{avg_score}/100")
    with col_s2:
        st.metric("🟢 High Quality", f"{green_count}")
    with col_s3:
        st.metric("🟡 Needs Work", f"{amber_count}")
    with col_s4:
        st.metric("🔴 Poor Quality", f"{red_count}")
    with col_s5:
        st.metric("⚠️ Contradictions", f"{len(conflicts)}")
    with col_s6:
        st.metric("🔄 Duplicate Pairs", f"{len(duplicates)}")

    st.markdown("---")

    # Section 1: Contradictions & Overlaps
    st.subheader("⚠️ Baseline Contradictions & Overlap Detection")
    tab_conf, tab_dup, tab_ai_analyzer = st.tabs([
        "⚡ Static Contradictions",
        "🔄 Duplicate / Overlap Detection",
        "🤖 Deep AI Conflict Checker",
    ])

    with tab_conf:
        if conflicts:
            for c in conflicts:
                r1 = project.get_requirement(c.req1_id)
                r2 = project.get_requirement(c.req2_id)
                with st.container():
                    st.error(
                        f"**[{c.severity} Severity Contradiction] Between {c.req1_id} and {c.req2_id}**\n\n"
                        f"{c.description}\n\n"
                        f"- **{c.req1_id}:** *\"{r1.text if r1 else ''}\"*\n"
                        f"- **{c.req2_id}:** *\"{r2.text if r2 else ''}\"*"
                    )
        else:
            st.success("✅ Zero contradictory requirements detected in baseline.")

    with tab_dup:
        if duplicates:
            st.info("The following requirements share &ge; 80% vocabulary and semantic structure, indicating potential redundancy:")
            for d in duplicates:
                r1 = project.get_requirement(d.req1_id)
                r2 = project.get_requirement(d.req2_id)
                with st.container():
                    st.warning(
                        f"**[{int(d.similarity * 100)}% Similarity Overlap] {d.req1_id} & {d.req2_id}**\n\n"
                        f"{d.description}\n\n"
                        f"- **{d.req1_id}:** *\"{r1.text if r1 else ''}\"*\n"
                        f"- **{d.req2_id}:** *\"{r2.text if r2 else ''}\"*"
                    )
        else:
            st.success("✅ No duplicate or redundant requirement statements detected (&ge; 80% similarity).")

    with tab_ai_analyzer:
        st.markdown("##### Pairwise Semantic Conflict Analyzer")
        st.caption("Select any two requirements to perform deep contextual conflict analysis using Claude or deterministic semantic heuristics.")
        req_list = [r.id for r in project.requirements]
        
        ca1, ca2 = st.columns(2)
        with ca1:
            req_a_id = st.selectbox("Requirement A", req_list, index=0)
        with ca2:
            default_b_idx = 1 if len(req_list) > 1 else 0
            req_b_id = st.selectbox("Requirement B", req_list, index=default_b_idx)

        if st.button("🔬 Analyze Conflict Probability", type="primary"):
            if req_a_id == req_b_id:
                st.warning("Please choose two different requirements for comparison.")
            else:
                ra = project.get_requirement(req_a_id)
                rb = project.get_requirement(req_b_id)
                if ra and rb:
                    with st.spinner("Analyzing semantic compatibility..."):
                        c_result, is_mock = analyze_conflict_ai(ra, rb)
                        engine = "Offline Mock Engine" if is_mock else "Claude AI"
                        st.markdown(f"**Analysis Report ({engine}):**")
                        
                        if c_result.get("conflict_detected"):
                            sev = c_result.get("severity", "Medium")
                            conf = int(c_result.get("confidence", 0.9) * 100)
                            st.error(f"⚠️ **Conflict Detected! Severity: {sev} (Confidence: {conf}%)**")
                        else:
                            st.success("✅ **Requirements Compatible: No semantic conflict found.**")

                        st.write(f"**Explanation:** {c_result.get('explanation')}")
                        st.write(f"**Resolution Strategy:** {c_result.get('resolution')}")

    st.markdown("---")

    # Section 2: Detailed Requirement Linter & AI Rewrite
    st.subheader("📋 Requirement Quality Assessment & AI Rewriter")

    filter_grade = st.radio(
        "Filter by Quality Grade",
        ["All", "🔴 Poor (<50)", "🟡 Needs Work (50-79)", "🟢 High (>=80)"],
        horizontal=True,
    )

    filtered_pairs = []
    for r in project.requirements:
        res = lint_requirement(r)
        if filter_grade == "🔴 Poor (<50)" and res.grade != "Red":
            continue
        if filter_grade == "🟡 Needs Work (50-79)" and res.grade != "Amber":
            continue
        if filter_grade == "🟢 High (>=80)" and res.grade != "Green":
            continue
        filtered_pairs.append((r, res))

    if not filtered_pairs:
        st.info("No requirements match the selected grade filter.")
        return

    # Initialize rewrite session state if not present
    if "pending_rewrites" not in st.session_state:
        st.session_state.pending_rewrites = {}

    for req, res in filtered_pairs:
        color_emoji = "🟢" if res.grade == "Green" else ("🟡" if res.grade == "Amber" else "🔴")
        header_text = f"{color_emoji} [{req.id}] Score: {res.score}/100 ({res.grade_label}) - {req.text[:75]}..."

        with st.expander(header_text, expanded=(res.grade == "Red")):
            col_info, col_action = st.columns([2.5, 1])

            with col_info:
                st.markdown(f"**Full Text:** *\"{req.text}\"*")
                st.markdown(f"**Type:** `{req.type}` | **Priority:** `{req.priority}` | **Version:** `v{req.version}`")

                if res.issues:
                    st.markdown("**Violated Rules & Deductions:**")
                    for issue in res.issues:
                        st.markdown(
                            f"- ❌ **{issue.rule}** (`-{issue.penalty} pts` | {issue.category}): {issue.message}"
                        )
                else:
                    st.markdown("✅ **Clean Specification:** Fully compliant with INCOSE and IEEE quality standards.")

            with col_action:
                st.write("")
                btn_rewrite = st.button(
                    f"🤖 AI Rewrite {req.id}",
                    key=f"btn_rewrite_{req.id}",
                    type="primary" if res.grade == "Red" else "secondary",
                )
                if btn_rewrite:
                    with st.spinner("Refactoring requirement into testable IEEE specification..."):
                        rewritten_text, is_mock = rewrite_requirement_ai(req)
                        st.session_state.pending_rewrites[req.id] = {
                            "rewritten_text": rewritten_text,
                            "is_mock": is_mock,
                        }
                        st.rerun()

            # If there is a pending rewrite for this requirement, display side-by-side diff
            if req.id in st.session_state.pending_rewrites:
                rewrite_data = st.session_state.pending_rewrites[req.id]
                new_text = rewrite_data["rewritten_text"]
                is_mock = rewrite_data["is_mock"]

                st.markdown("---")
                st.markdown(
                    f"#### 📝 Proposed Revision ({'⚡ Offline Mock Engine' if is_mock else '🤖 Claude AI'})"
                )

                diff_c1, diff_c2 = st.columns(2)
                with diff_c1:
                    st.markdown("**Original Requirement:**")
                    st.info(req.text)
                with diff_c2:
                    st.markdown("**Rewritten Proposal (Specific & Measurable):**")
                    st.success(new_text)

                diff_text = compute_diff(req.text, new_text)
                with st.expander("Show Unified Diff", expanded=False):
                    st.code(diff_text, language="diff")

                btn_accept_col, btn_reject_col = st.columns([1, 1])
                with btn_accept_col:
                    if st.button(f"✅ Accept & Commit {req.id}", key=f"accept_{req.id}", type="primary"):
                        req.update_text(new_text, mark_changed=True)
                        save_project(project)
                        del st.session_state.pending_rewrites[req.id]
                        st.success(f"Requirement {req.id} updated to version v{req.version}!")
                        st.rerun()

                with btn_reject_col:
                    if st.button(f"❌ Reject Proposal", key=f"reject_{req.id}"):
                        del st.session_state.pending_rewrites[req.id]
                        st.info("Proposed rewrite discarded.")
                        st.rerun()
