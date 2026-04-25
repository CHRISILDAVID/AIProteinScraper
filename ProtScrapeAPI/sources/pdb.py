"""
sources/pdb.py
──────────────
Fetch protein structure data from RCSB PDB Search + Data APIs.
"""

import logging
from sources.base import SESSION, throttle, make_result, SourceResult

logger = logging.getLogger(__name__)


def fetch_pdb(protein_name: str, max_results: int = 5) -> SourceResult:
    """Search RCSB PDB and return structure entries with sequences."""
    source = "PDB"
    url = f"https://www.rcsb.org/search?q={protein_name}"

    search_url = "https://search.rcsb.org/rcsbsearch/v2/query"
    search_payload = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": protein_name},
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": max_results},
            "sort": [{"sort_by": "score", "direction": "desc"}],
            "scoring_strategy": "combined",
        },
    }

    try:
        throttle()
        search_resp = SESSION.post(
            search_url,
            json=search_payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()
    except Exception as exc:
        logger.warning("PDB Search API failed: %s", exc)
        return make_result(source, url, error=str(exc))

    result_set = search_data.get("result_set", [])
    if not result_set:
        return make_result(source, url, raw_text=f"No PDB entries found for '{protein_name}'.")

    pdb_ids = [r["identifier"] for r in result_set[:max_results]]
    entries = []
    text_blocks = [f"=== PDB Search Results for '{protein_name}' ===\n"]

    for pdb_id in pdb_ids:
        try:
            throttle(0.2, 0.5)
            entry_url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
            entry_resp = SESSION.get(entry_url, timeout=20)
            entry_resp.raise_for_status()
            entry_data = entry_resp.json()
        except Exception as exc:
            logger.warning("PDB Data API failed for %s: %s", pdb_id, exc)
            continue

        struct = entry_data.get("struct", {})
        title = struct.get("title", "")

        exptl = entry_data.get("exptl", [])
        method = exptl[0].get("method", "") if exptl else ""

        rcsb_info = entry_data.get("rcsb_entry_info", {})
        resolution = (
            rcsb_info.get("resolution_combined", [None])[0]
            if rcsb_info.get("resolution_combined") else None
        )

        # Citation
        citation = entry_data.get("citation", [])
        primary_citation = {}
        for c in citation:
            if c.get("id") == "primary":
                primary_citation = c
                break
        if not primary_citation and citation:
            primary_citation = citation[0]

        authors = primary_citation.get("rcsb_authors", [])
        cit_title = primary_citation.get("title", "")
        journal = primary_citation.get("journal_abbrev", "")
        year = primary_citation.get("year", "")

        # Polymer entity for sequence + organism
        sequence = ""
        organism = ""
        try:
            poly_url = f"https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb_id}/1"
            poly_resp = SESSION.get(poly_url, timeout=15)
            if poly_resp.status_code == 200:
                poly_data = poly_resp.json()
                entity_poly = poly_data.get("entity_poly", {})
                sequence = entity_poly.get("pdbx_seq_one_letter_code_can", "")
                src = poly_data.get("rcsb_entity_source_organism", [])
                if src:
                    organism = src[0].get("scientific_name", "")
        except Exception:
            pass

        entry = {
            "pdb_id": pdb_id,
            "title": title,
            "method": method,
            "resolution": resolution,
            "organism": organism,
            "sequence": sequence,
            "authors": authors,
            "citation_title": cit_title,
            "journal": journal,
            "year": year,
        }
        entries.append(entry)

        block = f"\n--- PDB Entry: {pdb_id} ---\n"
        block += f"[Source: PDB | https://www.rcsb.org/structure/{pdb_id}]\n"
        block += f"Title: {title}\n"
        block += f"Experimental Method: {method}\n"
        if resolution:
            block += f"Resolution: {resolution} Å\n"
        if organism:
            block += f"Organism: {organism}\n"
        if authors:
            block += f"Authors: {', '.join(authors[:5])}\n"
        if cit_title:
            block += f"Citation: {cit_title}"
            if journal:
                block += f" ({journal}"
                if year:
                    block += f", {year}"
                block += ")"
            block += "\n"
        if sequence:
            display_seq = sequence[:200] + ("..." if len(sequence) > 200 else "")
            block += f"Protein Sequence: {display_seq}\n"
        text_blocks.append(block)

    raw_text = "\n".join(text_blocks)
    return make_result(source, url, entries=entries, raw_text=raw_text)
