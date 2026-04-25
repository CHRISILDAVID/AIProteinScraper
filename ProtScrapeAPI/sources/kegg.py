"""
sources/kegg.py
───────────────
Fetch gene/protein data from KEGG REST API.
"""

import re
import logging
import requests
from sources.base import SESSION, throttle, make_result, SourceResult

logger = logging.getLogger(__name__)


def fetch_kegg(protein_name: str, max_results: int = 5) -> SourceResult:
    """Search KEGG genes and fetch detailed entries + sequences."""
    source = "KEGG"
    url = f"https://www.genome.jp/dbget-bin/www_bfind_sub?dbkey=genes&keywords={protein_name}"

    find_url = f"https://rest.kegg.jp/find/genes/{requests.utils.quote(protein_name)}"

    try:
        throttle()
        find_resp = SESSION.get(find_url, timeout=30)
        find_resp.raise_for_status()
        find_text = find_resp.text
    except Exception as exc:
        logger.warning("KEGG find failed: %s", exc)
        return make_result(source, url, error=str(exc))

    if not find_text.strip():
        return make_result(source, url, raw_text=f"No KEGG entries found for '{protein_name}'.")

    # Parse and score results
    lines = find_text.strip().splitlines()
    protein_lower = protein_name.lower().strip()
    scored_lines = []

    for line in lines:
        parts = line.split("\t", 1)
        if len(parts) < 2:
            continue
        kegg_id = parts[0].strip()
        desc = parts[1].strip()
        desc_lower = desc.lower()

        score = 0
        if protein_lower in desc_lower:
            score += 10
            pattern = r'\b' + re.escape(protein_lower) + r'\b'
            if re.search(pattern, desc_lower):
                score += 5
        if "hsa:" in kegg_id:
            score += 2

        scored_lines.append((score, kegg_id, desc))

    scored_lines.sort(key=lambda x: x[0], reverse=True)
    top_entries = scored_lines[:max_results]

    if not top_entries:
        return make_result(source, url, raw_text=f"No KEGG entries found for '{protein_name}'.")

    entries = []
    text_blocks = [f"=== KEGG Results for '{protein_name}' ===\n"]

    for score, kegg_id, desc in top_entries:
        entry_data = {"kegg_id": kegg_id, "description": desc}
        block = f"\n--- KEGG Gene: {kegg_id} ---\n"
        block += f"[Source: KEGG | https://www.genome.jp/entry/{kegg_id}]\n"
        block += f"Description: {desc}\n"

        try:
            throttle(0.3, 0.6)
            get_url = f"https://rest.kegg.jp/get/{kegg_id}"
            get_resp = SESSION.get(get_url, timeout=20)
            if get_resp.status_code == 200:
                entry_text = get_resp.text

                organism = ""
                gene_name = ""
                pathway_lines = []

                for eline in entry_text.splitlines():
                    if eline.startswith("ORGANISM"):
                        organism = eline.replace("ORGANISM", "").strip()
                    elif eline.startswith("NAME"):
                        gene_name = eline.replace("NAME", "").strip()
                    elif eline.startswith("PATHWAY") or (
                        pathway_lines and eline.startswith("            ")
                    ):
                        pathway_lines.append(eline.strip())

                entry_data["organism"] = organism
                entry_data["gene_name"] = gene_name
                entry_data["pathways"] = pathway_lines[:5]

                if organism:
                    block += f"Organism: {organism}\n"
                if gene_name:
                    block += f"Gene Name: {gene_name}\n"
                if pathway_lines:
                    block += f"Pathways: {'; '.join(pathway_lines[:3])}\n"

                # Fetch amino acid sequence
                try:
                    throttle(0.2, 0.4)
                    aaseq_url = f"https://rest.kegg.jp/get/{kegg_id}/aaseq"
                    aaseq_resp = SESSION.get(aaseq_url, timeout=15)
                    if aaseq_resp.status_code == 200:
                        aaseq_text = aaseq_resp.text.strip()
                        seq_lines = aaseq_text.splitlines()
                        sequence = "".join(
                            l.strip() for l in seq_lines[1:] if not l.startswith(">")
                        )
                        entry_data["sequence"] = sequence
                        entry_data["length"] = len(sequence)
                        block += f"Sequence Length: {len(sequence)} aa\n"
                        display_seq = sequence[:200] + ("..." if len(sequence) > 200 else "")
                        block += f"Protein Sequence: {display_seq}\n"
                except Exception:
                    pass

        except Exception as exc:
            logger.warning("KEGG get failed for %s: %s", kegg_id, exc)

        entries.append(entry_data)
        text_blocks.append(block)

    raw_text = "\n".join(text_blocks)
    return make_result(source, url, entries=entries, raw_text=raw_text)
