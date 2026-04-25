"""
main.py
───────
ProtScrape — AI-Powered Protein Data Scraper with RAG & Source Attribution.

Streamlit entry point. Run with:
    streamlit run main.py
"""

import sys
import os

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="ProtScrape — AI Protein Data Scraper",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import after page config
from config import APP_NAME, APP_VERSION, APP_DESCRIPTION
from ui.theme import inject_custom_css
from ui.sidebar import render_sidebar
from ui.results import render_fetch_status, render_analysis_results
from ui.export import render_export_buttons
from sources.fetcher import fetch_all_sources
from engine.pipeline import run_pipeline

# ── Theme ────────────────────────────────────────────────────────────────────
inject_custom_css()

# ── Sidebar ──────────────────────────────────────────────────────────────────
settings = render_sidebar()

# ── Hero Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 0.5rem 0 0;">
    <h1 class="hero-title">ProtScrape</h1>
    <p class="hero-subtitle">
        AI-powered protein data extraction from 6 major databases — with RAG retrieval & source attribution
    </p>
</div>
""", unsafe_allow_html=True)

# ── Main Action ──────────────────────────────────────────────────────────────
protein_name = settings["protein_name"]

if not protein_name:
    st.markdown("""
    <div class="glass-card" style="text-align: center; padding: 3rem;">
        <span style="font-size: 4rem; display: block; margin-bottom: 1rem;">🧬</span>
        <h3 style="
            font-family: 'Inter', sans-serif;
            color: var(--text-primary);
            font-weight: 600;
            margin-bottom: 0.5rem;
        ">Enter a protein name to begin</h3>
        <p style="
            color: var(--text-muted);
            font-family: 'Inter', sans-serif;
            font-size: 0.95rem;
            max-width: 500px;
            margin: 0 auto;
        ">
            ProtScrape will query UniProt, PDB, NCBI, InterPro, KEGG, and STRING
            simultaneously, then use RAG + LLM to extract the exact fields you need
            — with full source attribution.
        </p>
        <div style="margin-top: 1.5rem;">
            <span class="metric-chip"><span class="label">Try</span><span class="value">hemoglobin</span></span>
            <span class="metric-chip"><span class="label">Try</span><span class="value">insulin</span></span>
            <span class="metric-chip"><span class="label">Try</span><span class="value">p53</span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Analyze Button ───────────────────────────────────────────────────────────
if st.button("🚀 Analyze Protein", key="analyze_btn"):
    if not settings["sources"]:
        st.warning("Please select at least one data source.")
        st.stop()

    # ── Phase 1: Fetch from APIs ─────────────────────────────────────
    with st.status("🔄 Fetching protein data from databases...", expanded=True) as status:
        st.write(f"Querying {len(settings['sources'])} databases for **{protein_name}**...")

        source_results = fetch_all_sources(
            protein_name=protein_name,
            sources=settings["sources"],
            max_results=settings["max_results"],
        )

        ok_count = sum(1 for r in source_results.values() if r.ok)
        total_entries = sum(r.entry_count for r in source_results.values())

        for name, result in source_results.items():
            if result.ok:
                st.write(f"✅ **{name}**: {result.entry_count} entries")
            elif result.error:
                st.write(f"❌ **{name}**: {result.error[:80]}")
            else:
                st.write(f"⚠️ **{name}**: No results")

        status.update(
            label=f"✅ Fetched {total_entries} entries from {ok_count}/{len(source_results)} sources",
            state="complete",
        )

    st.session_state["source_results"] = source_results
    st.session_state["protein_name"] = protein_name

    # ── Phase 2: RAG + LLM Pipeline ─────────────────────────────────
    if ok_count > 0:
        with st.status("🧠 Running RAG + LLM extraction pipeline...", expanded=True) as status:
            st.write(f"Provider: **{settings['provider']}** | Model: **{settings['model']}**")
            st.write(f"RAG: **{'enabled' if settings['use_rag'] else 'disabled'}** | Top-K: **{settings['rag_top_k']}**")

            analysis = run_pipeline(
                protein_name=protein_name,
                query=settings["query"],
                source_results=source_results,
                provider=settings["provider"],
                model=settings["model"],
                use_rag=settings["use_rag"],
                top_k=settings["rag_top_k"],
            )

            verdict = analysis.get("verdict", "Uncertain")
            confidence = analysis.get("confidence", 0)
            status.update(
                label=f"✅ Analysis complete — {verdict} ({confidence}% confidence)",
                state="complete",
            )

        st.session_state["analysis"] = analysis
    else:
        st.error("No data retrieved from any source. Cannot run analysis.")

# ── Display Results ──────────────────────────────────────────────────────────
if "source_results" in st.session_state:
    render_fetch_status(st.session_state["source_results"])

if "analysis" in st.session_state:
    render_analysis_results(st.session_state["analysis"])

    st.markdown("---")
    render_export_buttons(
        st.session_state["analysis"],
        st.session_state.get("protein_name", "protein"),
    )
