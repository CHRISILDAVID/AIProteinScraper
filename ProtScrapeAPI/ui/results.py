"""
ui/results.py
─────────────
Result display components with source attribution.
Uses a mix of Streamlit native components and carefully scoped inline HTML.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from sources.fetcher import SOURCE_ICONS


def render_fetch_status(source_results: dict):
    """Show fetch status cards for each database source."""
    st.markdown('<div class="section-header">📡 Data Sources Status</div>', unsafe_allow_html=True)

    cols = st.columns(3)
    idx = 0
    for name, result in source_results.items():
        icon = SOURCE_ICONS.get(name, "📦")
        with cols[idx % 3]:
            if result.ok:
                status_color = "#10b981"
                status_glow = "rgba(16, 185, 129, 0.5)"
                status_text = f"{result.entry_count} entries"
                text_color = "#10b981"
            elif result.error:
                status_color = "#ef4444"
                status_glow = "rgba(239, 68, 68, 0.5)"
                status_text = "Failed"
                text_color = "#ef4444"
            else:
                status_color = "#f59e0b"
                status_glow = "rgba(245, 158, 11, 0.5)"
                status_text = "No data"
                text_color = "#f59e0b"

            st.markdown(f"""
            <div class="source-card">
                <h4>{icon} {name}</h4>
                <span style="
                    width: 8px; height: 8px; border-radius: 50%;
                    display: inline-block; margin-right: 8px;
                    background: {status_color};
                    box-shadow: 0 0 8px {status_glow};
                "></span>
                <span style="color: {text_color}; font-weight: 500; font-size: 0.85rem;">
                    {status_text}
                </span>
                <br>
                <a class="source-url" href="{result.url}" target="_blank">
                    🔗 View source →
                </a>
            </div>
            """, unsafe_allow_html=True)
        idx += 1


def render_analysis_results(analysis: Dict[str, Any]):
    """Render the full analysis results with source attribution."""
    if not analysis:
        return

    # ── Summary Section ──────────────────────────────────────────────
    st.markdown('<div class="section-header">🧪 Analysis Results</div>', unsafe_allow_html=True)

    verdict = analysis.get("verdict", "Uncertain")
    confidence = analysis.get("confidence", 0)
    summary = analysis.get("summary", "No summary")

    # Verdict badge colors
    badge_colors = {
        "Valid": ("rgba(16, 185, 129, 0.15)", "#34d399", "rgba(16, 185, 129, 0.3)"),
        "Invalid": ("rgba(239, 68, 68, 0.15)", "#f87171", "rgba(239, 68, 68, 0.3)"),
        "Uncertain": ("rgba(245, 158, 11, 0.15)", "#fbbf24", "rgba(245, 158, 11, 0.3)"),
    }
    bg, color, border = badge_colors.get(verdict, badge_colors["Uncertain"])

    st.markdown(f"""
    <div class="glass-card fade-in">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            <span style="
                display: inline-flex; align-items: center;
                padding: 0.35rem 1rem; border-radius: 50px;
                font-family: 'Inter', sans-serif; font-size: 0.85rem;
                font-weight: 600; letter-spacing: 0.3px;
                background: {bg}; color: {color}; border: 1px solid {border};
            ">{verdict}</span>
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #64748b; font-size: 0.8rem; font-family: 'Inter', sans-serif;">
                        CONFIDENCE
                    </span>
                    <span style="color: #f0f4f8; font-weight: 600; font-family: 'Inter', sans-serif;">
                        {confidence}%
                    </span>
                </div>
                <div class="confidence-bar-container">
                    <div class="confidence-bar-fill" style="width: {confidence}%;"></div>
                </div>
            </div>
        </div>
        <p style="color: #94a3b8; font-size: 0.95rem; font-family: 'Inter', sans-serif; margin: 0; line-height: 1.6;">
            {summary}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Metrics Row ──────────────────────────────────────────────────
    model_info = analysis.get("model", {})
    retrieval = analysis.get("retrieval", {})
    sources_used = analysis.get("sources_used", {})

    ok_count = sum(1 for s in sources_used.values() if s.get("status") == "ok")
    total_entries = sum(s.get("entries", 0) for s in sources_used.values())

    st.markdown(f"""
    <div class="metric-row fade-in">
        <div class="metric-chip">
            <span class="label">Model</span>
            <span class="value">{model_info.get('provider', '?')}:{model_info.get('name', '?')}</span>
        </div>
        <div class="metric-chip">
            <span class="label">Sources</span>
            <span class="value">{ok_count}/{len(sources_used)}</span>
        </div>
        <div class="metric-chip">
            <span class="label">Entries</span>
            <span class="value">{total_entries}</span>
        </div>
        <div class="metric-chip">
            <span class="label">RAG</span>
            <span class="value">{retrieval.get('method', 'off')}</span>
        </div>
        <div class="metric-chip">
            <span class="label">Chunks</span>
            <span class="value">{retrieval.get('chunks_sent', 0)}/{retrieval.get('chunks_total', 0)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Extracted Fields Table (native Streamlit) ────────────────────
    extracted = analysis.get("extracted_fields", {})
    attribution = analysis.get("source_attribution", {})

    if extracted:
        st.markdown('<div class="section-header">📋 Extracted Fields</div>', unsafe_allow_html=True)

        rows = []
        for field, value in extracted.items():
            source_tag = attribution.get(field, "—")
            display_val = str(value) if value else "—"
            if len(display_val) > 300:
                display_val = display_val[:300] + "..."
            rows.append({
                "Field": field,
                "Value": display_val,
                "Source": source_tag,
            })

        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            column_config={
                "Field": st.column_config.TextColumn("Field", width="small"),
                "Value": st.column_config.TextColumn("Value", width="large"),
                "Source": st.column_config.TextColumn("Source", width="small"),
            },
        )

    # ── Evidence ─────────────────────────────────────────────────────
    evidence = analysis.get("evidence", [])
    if evidence:
        st.markdown('<div class="section-header">📌 Evidence</div>', unsafe_allow_html=True)
        for item in evidence:
            quote = item.get("quote", "")
            ev_source = item.get("source", "")
            reason = item.get("why_relevant", "")
            st.markdown(f"""
            <div style="
                background: rgba(99, 102, 241, 0.05);
                border-left: 3px solid #6366f1;
                padding: 0.75rem 1rem;
                margin: 0.5rem 0;
                border-radius: 0 10px 10px 0;
                font-size: 0.9rem;
                color: #94a3b8;
            ">
                <em>"{quote}"</em>
                <div style="color: #06b6d4; font-size: 0.75rem; font-weight: 500; margin-top: 0.35rem;">
                    📍 {ev_source} — {reason}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Source Details ────────────────────────────────────────────────
    if sources_used:
        st.markdown('<div class="section-header">🗄️ Source Details</div>', unsafe_allow_html=True)
        for name, info in sources_used.items():
            icon = SOURCE_ICONS.get(name, "📦")
            status = info.get("status", "unknown")
            label = (
                f"{icon} {name} — ✅ {info.get('entries', 0)} entries"
                if status == "ok"
                else f"{icon} {name} — ❌ {(info.get('error', 'No data') or 'No data')[:60]}"
            )
            with st.expander(label, expanded=False):
                if status == "ok":
                    st.markdown(f"**URL:** [{info.get('url', '')}]({info.get('url', '')})")
                    st.markdown(f"**Entries retrieved:** {info.get('entries', 0)}")
                else:
                    st.error(f"Error: {info.get('error', 'Unknown error')}")
                    if info.get("url"):
                        st.markdown(f"**URL:** [{info.get('url', '')}]({info.get('url', '')})")
