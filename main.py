import sys
import os
import streamlit as st

# Set page config at the very beginning (must be the first Streamlit command)
st.set_page_config(
    page_title="Protein Scraper Suite",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure ProtScrapeAPI is on the Python path
protscrape_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ProtScrapeAPI")
if protscrape_path not in sys.path:
    sys.path.insert(0, protscrape_path)

from ProtScrapeAPI.ui.theme import inject_custom_css
inject_custom_css()

# Sidebar mode toggle
st.sidebar.title("Scraping Mode")
scraping_mode = st.sidebar.radio(
    "Select Engine",
    ["ProtScrape (API-Based)", "ProtScrape (DOM-Based)"],
    help="Choose between the high-performance API scraper and the traditional DOM web scraper."
)
st.sidebar.markdown("---")

if scraping_mode == "ProtScrape (API-Based)":
    # Import ProtScrape components
    from config import APP_NAME, APP_VERSION, APP_DESCRIPTION
    from ui.sidebar import render_sidebar
    from ui.results import render_fetch_status, render_analysis_results
    from ui.export import render_export_buttons
    from sources.fetcher import fetch_all_sources
    from engine.pipeline import run_pipeline

    # Render ProtScrape sidebar
    settings = render_sidebar()
    
    # Hero Header
    st.markdown("""
    <div style="padding: 0.5rem 0 0;">
        <h1 class="hero-title">ProtScrape</h1>
        <p class="hero-subtitle">
            AI-powered protein data extraction from 6 major databases — with RAG retrieval & source attribution
        </p>
    </div>
    """, unsafe_allow_html=True)

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

    if st.button("🚀 Analyze Protein", key="analyze_btn"):
        if not settings["sources"]:
            st.warning("Please select at least one data source.")
            st.stop()

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

    if "source_results" in st.session_state:
        render_fetch_status(st.session_state["source_results"])

    if "analysis" in st.session_state:
        render_analysis_results(st.session_state["analysis"])

        st.markdown("---")
        render_export_buttons(
            st.session_state["analysis"],
            st.session_state.get("protein_name", "protein"),
        )

elif scraping_mode == "ProtScrape (DOM-Based)":
    import json
    from scrape import (
        scrape_website,
        scrape_with_urllib3_proxy,
        scrape_with_proxyscrape_pool,
        scrape_with_requests,
        extract_body_content,
        clean_body_content,
        split_dom_content,
        extract_candidate_detail_links,
    )
    from parse import parse_with_ollama
    from protein import generate_search_urls

    # AIProteinScraper UI
    st.markdown("""
    <div style="padding: 0.5rem 0 1rem;">
        <h1 class="hero-title">ProtScrape</h1>
        <p class="hero-subtitle">
            Traditional DOM Scraping Engine — showcases browser simulation, proxies, and HTML parsing
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    protein_name_dom = st.text_input("Give Protein name:", key="protein_name_dom")
    urls = []

    def fetch_content_for_source(target_url, source_name, method_name):
        dom_content = None
        try:
            if method_name == "Bright Data API":
                dom_content = scrape_website(target_url)
                if not dom_content:
                    st.warning(
                        f"Bright Data API failed for {source_name}. Falling back to direct request."
                    )
                    dom_content = scrape_with_requests(target_url, use_proxy=False)
            elif method_name == "ProxyScrape (rotating proxies)":
                dom_content = scrape_with_proxyscrape_pool(target_url)
                if not dom_content:
                    st.warning(
                        f"ProxyScrape failed for {source_name}. Falling back to direct request."
                    )
                    dom_content = scrape_with_requests(target_url, use_proxy=False)
            elif method_name == "Azure Proxy (urllib3)":
                dom_content = scrape_with_urllib3_proxy(target_url)
            elif method_name == "Azure Proxy (requests)":
                dom_content = scrape_with_requests(target_url, use_proxy=True)
            else:  # Direct Request
                dom_content = scrape_with_requests(target_url, use_proxy=False)
        except Exception as exc:
            st.error(f"Error while scraping {source_name}: {exc}")
            return None

        return dom_content

    def render_parsed_results(parsed_results, protein_query):
        if not parsed_results:
            st.info("No parsed results yet.")
            return

        st.subheader("Validation Summary")
        summary_rows = []
        valid_sources = 0

        for source_name, result in parsed_results.items():
            verdict = result.get("verdict", "Uncertain")
            if verdict == "Valid":
                valid_sources += 1
            extracted_fields = result.get("extracted_fields", {})
            requested_fields = result.get("requested_fields") or list(extracted_fields.keys())
            total_fields = max(1, len(requested_fields))
            model_info = result.get("model", {})
            model_label = (
                f"{model_info.get('provider', 'unknown')}:{model_info.get('name', 'unknown')}"
                if model_info
                else "unknown"
            )
            filled_fields = sum(1 for value in extracted_fields.values() if value)
            summary_rows.append(
                {
                    "Source": source_name,
                    "Model": model_label,
                    "Verdict": verdict,
                    "Confidence": result.get("confidence", 0),
                    "Fields Found": f"{filled_fields}/{total_fields}",
                    "Summary": result.get("summary", ""),
                }
            )

        st.metric("Valid Sources", f"{valid_sources}/{len(parsed_results)}")
        st.dataframe(summary_rows, use_container_width=True)

        st.subheader("Source Details")
        for source_name, result in parsed_results.items():
            verdict = result.get("verdict", "Uncertain")
            confidence = result.get("confidence", 0)
            with st.expander(f"{source_name} | {verdict} ({confidence}%)"):
                st.write(result.get("summary", "No summary."))

                model_info = result.get("model", {})
                if model_info:
                    st.caption(
                        "Model used: "
                        f"{model_info.get('provider', 'unknown')} "
                        f"({model_info.get('name', 'unknown')})"
                    )

                extracted_fields = result.get("extracted_fields", {})
                field_rows = [
                    {"Field": field_name, "Value": field_value}
                    for field_name, field_value in extracted_fields.items()
                ]
                requested_fields = result.get("requested_fields") or list(extracted_fields.keys())
                if requested_fields:
                    st.caption("Requested fields: " + ", ".join(requested_fields))
                st.caption("Extracted fields")
                st.dataframe(field_rows, use_container_width=True)

                evidence = result.get("evidence", [])
                if evidence:
                    st.caption("Evidence snippets")
                    st.dataframe(evidence, use_container_width=True)
                else:
                    st.caption("No evidence snippets were extracted.")

                retrieval = result.get("retrieval", {})
                if retrieval:
                    retrieval_parts = [
                        f"enabled={retrieval.get('enabled')}",
                        f"method={retrieval.get('retrieval_method', 'n/a')}",
                    ]
                    emb_model = retrieval.get("embedding_model")
                    if emb_model:
                        retrieval_parts.append(f"embedding={emb_model}")
                    retrieval_parts.extend([
                        f"chunks_sent={retrieval.get('chunks_sent')}",
                        f"chunks_considered={retrieval.get('chunks_considered')}",
                    ])
                    st.caption("Retrieval: " + " | ".join(retrieval_parts))

                source_url = result.get("source_url")
                if source_url:
                    st.markdown(f"Source URL: {source_url}")

                detail_urls = result.get("detail_urls", [])
                if detail_urls:
                    st.caption("Detail pages used for context")
                    st.dataframe([{"URL": url} for url in detail_urls], use_container_width=True)

        st.download_button(
            "Download JSON Report",
            data=json.dumps(
                {
                    "protein_query": protein_query,
                    "results": parsed_results,
                },
                indent=2,
            ),
            file_name=f"{(protein_query or 'protein').strip().replace(' ', '_')}_report.json",
            mime="application/json",
        )

    st.markdown('<h4>Scraping Options</h4>', unsafe_allow_html=True)
    # Add a dropdown to select scraping method
    scraping_method = st.selectbox(
        "Select Scraping Method",
        [
            "ProxyScrape (rotating proxies)",
            "Bright Data API",
            "Azure Proxy (urllib3)",
            "Azure Proxy (requests)",
            "Direct Request",
        ]
    )
    follow_detail_pages = st.checkbox(
        "Follow likely detail pages (recommended for sequence extraction)",
        value=True,
    )
    max_detail_pages = st.slider("Detail pages per source", min_value=0, max_value=5, value=2)

    # Step 1: Scrape dbs for protein information
    if st.button("Scrape Now"):
        if protein_name_dom:
            st.write("Scraping the databases for protein information...")
            urls = generate_search_urls(protein_name_dom)
            st.session_state.dom_content = {}
            st.session_state.parsed_results_dom = {}
            for url in urls:
                st.write(f"Scraping {url['name']}...")

                dom_content = fetch_content_for_source(url["url"], url["name"], scraping_method)
                    
                if dom_content:
                    body_content = extract_body_content(dom_content)
                    cleaned_content = clean_body_content(body_content)

                    detail_urls = []
                    if follow_detail_pages and max_detail_pages > 0:
                        candidate_links = extract_candidate_detail_links(
                            dom_content,
                            url["url"],
                            protein_name_dom,
                            max_links=max_detail_pages,
                        )
                        for detail_url in candidate_links:
                            detail_dom = fetch_content_for_source(
                                detail_url,
                                f"{url['name']} detail",
                                scraping_method,
                            )
                            if not detail_dom:
                                continue
                            detail_body = extract_body_content(detail_dom)
                            detail_clean = clean_body_content(detail_body)
                            if detail_clean:
                                detail_urls.append(detail_url)
                                cleaned_content += "\n\n" + detail_clean

                    # Store the DOM content in Streamlit session state
                    st.session_state.dom_content[url['name']] = {
                        "url": url["url"],
                        "detail_urls": detail_urls,
                        "content": cleaned_content,
                    }
                else:
                    st.error(f"Failed to fetch content from {url['name']}")

    # Step 2: Iterate through dbs
    if 'dom_content' in st.session_state and st.session_state.dom_content:
        st.markdown('<h4>Parse Options</h4>', unsafe_allow_html=True)
        parse_description = st.text_area(
            "Describe anything specific to parse",
            value="ORGANISM, REFERENCE, AUTHOR and TITLE",
        )
        llm_provider_label = st.selectbox(
            "Inference provider",
            ["Gemini (free tier)", "OpenAI API", "Ollama (local)"],
            index=0,
        )
        if llm_provider_label == "OpenAI API":
            llm_provider = "openai"
            llm_model = st.text_input("OpenAI model", value="gpt-4o-mini")
            st.caption("Requires OPENAI_API_KEY in .env")
        elif llm_provider_label == "Gemini (free tier)":
            llm_provider = "gemini"
            llm_model = st.text_input("Gemini model", value="gemini-2.5-flash")
            st.caption("Requires GOOGLE_API_KEY in .env — uses free tier lightweight models")
        else:
            llm_provider = "ollama"
            llm_model = st.text_input("Ollama model", value="gemma2:2b")

        use_rag_dom = st.checkbox(
            "Enable RAG mode (semantic embedding retrieval via ChromaDB)",
            value=True,
            key="rag_toggle_dom"
        )
        rag_top_k_dom = st.slider("Chunks sent to model", min_value=1, max_value=16, value=6, key="rag_top_k_dom")

        if st.button("Parse Content"):
            st.write("Parsing the content from all the databases...")
            st.session_state.parsed_results_dom = {}
            for name, payload in st.session_state.dom_content.items():
                dom_chunks = split_dom_content(payload["content"])
                parsed_result = parse_with_ollama(
                    dom_chunks,
                    parse_description,
                    protein_name_dom,
                    name,
                    use_rag=use_rag_dom,
                    rag_top_k=rag_top_k_dom,
                    llm_provider=llm_provider,
                    llm_model=llm_model,
                )
                parsed_result["source_url"] = payload["url"]
                parsed_result["detail_urls"] = payload.get("detail_urls", [])
                st.session_state.parsed_results_dom[name] = parsed_result

    if 'parsed_results_dom' in st.session_state:
        render_parsed_results(st.session_state.parsed_results_dom, protein_name_dom)
