"""
ui/sidebar.py
─────────────
Sidebar controls for ProtScrape.
"""

import streamlit as st
from sources.fetcher import ALL_SOURCES, SOURCE_DESCRIPTIONS, SOURCE_ICONS


def render_sidebar() -> dict:
    """
    Render the sidebar and return user selections.

    Returns
    -------
    dict with keys: protein_name, query, sources, provider, model,
    use_rag, rag_top_k, max_results
    """
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 0.5rem 0;">
            <span style="font-size: 2.5rem;">🧬</span>
            <h2 style="
                font-family: 'Inter', sans-serif;
                font-weight: 800;
                background: linear-gradient(135deg, #6366f1, #06b6d4);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0.25rem 0;
                font-size: 1.5rem;
            ">ProtScrape</h2>
            <p style="
                color: #64748b;
                font-size: 0.8rem;
                font-family: 'Inter', sans-serif;
                margin: 0;
            ">AI-Powered Protein Data Scraper</p>
        </div>
        <hr style="border-color: rgba(255,255,255,0.06); margin: 1rem 0;">
        """, unsafe_allow_html=True)

        # ── Protein Input ────────────────────────────────────────────
        st.markdown("##### 🔍 Protein Query")
        protein_name = st.text_input(
            "Protein name",
            placeholder="e.g., hemoglobin, insulin, p53",
            label_visibility="collapsed",
            key="protein_input",
        )

        # ── Field Query ──────────────────────────────────────────────
        st.markdown("##### 📋 Fields to Extract")
        query = st.text_area(
            "What to extract",
            value="ORGANISM, FUNCTION, SEQUENCE, GENE, REFERENCE, AUTHOR, TITLE",
            height=80,
            label_visibility="collapsed",
            key="query_input",
        )

        st.markdown("<hr style='border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

        # ── Database Sources ─────────────────────────────────────────
        st.markdown("##### 🗄️ Data Sources")
        selected_sources = []
        for name in ALL_SOURCES:
            icon = SOURCE_ICONS.get(name, "📦")
            desc = SOURCE_DESCRIPTIONS.get(name, "")
            checked = st.checkbox(
                f"{icon} {name}",
                value=True,
                help=desc,
                key=f"source_{name}",
            )
            if checked:
                selected_sources.append(name)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

        # ── LLM Configuration ────────────────────────────────────────
        st.markdown("##### 🤖 LLM Configuration")
        provider_label = st.selectbox(
            "Inference Provider",
            ["Gemini (free tier)", "OpenAI API", "Ollama (local)"],
            index=0,
            key="provider_select",
        )

        if provider_label == "OpenAI API":
            provider = "openai"
            model = st.text_input("Model", value="gpt-4o-mini", key="model_input")
            st.caption("Requires `OPENAI_API_KEY` in `.env`")
        elif provider_label == "Gemini (free tier)":
            provider = "gemini"
            model = st.text_input("Model", value="gemini-2.0-flash", key="model_input")
            st.caption("Requires `GOOGLE_API_KEY` in `.env`")
        else:
            provider = "ollama"
            model = st.text_input("Model", value="gemma2:2b", key="model_input")
            st.caption("Requires Ollama running locally")

        st.markdown("<hr style='border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

        # ── RAG Configuration ────────────────────────────────────────
        st.markdown("##### 📊 RAG Settings")
        use_rag = st.checkbox(
            "Enable RAG (semantic retrieval via ChromaDB)",
            value=True,
            key="rag_toggle",
        )
        rag_top_k = st.slider(
            "Chunks to retrieve",
            min_value=2,
            max_value=16,
            value=6,
            key="rag_top_k",
        )
        max_results = st.slider(
            "Max entries per source",
            min_value=1,
            max_value=10,
            value=5,
            key="max_results",
        )

        st.markdown("""
        <div style="
            text-align: center;
            padding: 1.5rem 0 0.5rem 0;
            color: #475569;
            font-size: 0.7rem;
            font-family: 'Inter', sans-serif;
        ">
            ProtScrape v1.0 • API-First Architecture
        </div>
        """, unsafe_allow_html=True)

    return {
        "protein_name": protein_name,
        "query": query,
        "sources": selected_sources,
        "provider": provider,
        "model": model,
        "use_rag": use_rag,
        "rag_top_k": rag_top_k,
        "max_results": max_results,
    }
