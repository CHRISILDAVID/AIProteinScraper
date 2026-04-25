"""
sources/interpro.py
───────────────────
Fetch protein family/domain annotations from InterPro REST API.
"""

import logging
from sources.base import SESSION, throttle, make_result, SourceResult

logger = logging.getLogger(__name__)


def fetch_interpro(protein_name: str, max_results: int = 5) -> SourceResult:
    """Search InterPro for protein family/domain entries."""
    source = "InterPro"
    url = f"https://www.ebi.ac.uk/interpro/search/text/{protein_name}"

    search_url = "https://www.ebi.ac.uk/interpro/api/entry/interpro"
    params = {
        "search": protein_name,
        "page_size": max_results,
        "format": "json",
    }

    try:
        throttle()
        resp = SESSION.get(search_url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("InterPro API failed: %s", exc)
        return make_result(source, url, error=str(exc))

    results = data.get("results", [])
    if not results:
        return make_result(source, url, raw_text=f"No InterPro entries found for '{protein_name}'.")

    entries = []
    text_blocks = [f"=== InterPro Results for '{protein_name}' ===\n"]

    for item in results[:max_results]:
        metadata = item.get("metadata", {})
        accession = metadata.get("accession", "")
        name = metadata.get("name", {})
        entry_name = name.get("name", "") if isinstance(name, dict) else str(name)
        entry_type = metadata.get("type", "")
        source_db = metadata.get("source_database", "")

        # Description
        description = ""
        desc_list = metadata.get("description", [])
        if desc_list and isinstance(desc_list, list):
            for para in desc_list:
                if isinstance(para, dict):
                    for text_item in para.get("text", []):
                        if isinstance(text_item, str):
                            description += text_item + " "
                elif isinstance(para, str):
                    description += para + " "

        # GO terms
        go_terms = metadata.get("go_terms", [])

        entry = {
            "accession": accession,
            "name": entry_name,
            "type": entry_type,
            "source_database": source_db,
            "description": description.strip(),
            "go_terms": go_terms[:5] if go_terms else [],
        }
        entries.append(entry)

        block = f"\n--- InterPro Entry: {accession} ---\n"
        block += f"[Source: InterPro | https://www.ebi.ac.uk/interpro/entry/InterPro/{accession}]\n"
        block += f"Name: {entry_name}\n"
        block += f"Type: {entry_type}\n"
        if source_db:
            block += f"Source Database: {source_db}\n"
        if description:
            block += f"Description: {description.strip()[:500]}\n"
        if go_terms:
            go_strs = [
                f"{gt.get('identifier', '')}: {gt.get('name', '')}"
                for gt in go_terms[:5]
                if isinstance(gt, dict)
            ]
            if go_strs:
                block += f"GO Terms: {'; '.join(go_strs)}\n"
        text_blocks.append(block)

    raw_text = "\n".join(text_blocks)
    return make_result(source, url, entries=entries, raw_text=raw_text)
