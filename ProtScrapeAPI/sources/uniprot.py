"""
sources/uniprot.py
──────────────────
Fetch protein data from UniProt REST API.
Endpoint: https://rest.uniprot.org/uniprotkb/search
"""

import logging
from sources.base import SESSION, throttle, make_result, SourceResult

logger = logging.getLogger(__name__)

API_BASE = "https://rest.uniprot.org/uniprotkb/search"


def fetch_uniprot(protein_name: str, max_results: int = 5) -> SourceResult:
    """Search UniProtKB and return structured protein entries."""
    source = "UniProt"
    url = f"https://www.uniprot.org/uniprotkb?query={protein_name}"

    params = {
        "query": protein_name,
        "format": "json",
        "size": max_results,
        "fields": (
            "accession,id,protein_name,gene_names,organism_name,"
            "organism_id,sequence,length,cc_function,cc_subcellular_location,"
            "lit_pubmed_id,xref_pdb"
        ),
    }

    try:
        throttle()
        resp = SESSION.get(API_BASE, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("UniProt API failed: %s", exc)
        return make_result(source, url, error=str(exc))

    results = data.get("results", [])
    if not results:
        return make_result(source, url, raw_text=f"No UniProt entries found for '{protein_name}'.")

    entries = []
    text_blocks = [f"=== UniProt Search Results for '{protein_name}' ===\n"]

    for item in results:
        # Protein name
        prot_desc = item.get("proteinDescription", {})
        rec_name = prot_desc.get("recommendedName", {})
        full_name = ""
        if rec_name:
            full_name = rec_name.get("fullName", {}).get("value", "")
        elif prot_desc.get("submissionNames"):
            full_name = prot_desc["submissionNames"][0].get("fullName", {}).get("value", "")

        # Organism
        organism_info = item.get("organism", {})
        organism = organism_info.get("scientificName", "")
        common_name = organism_info.get("commonName", "")

        # Sequence
        seq_info = item.get("sequence", {})
        sequence = seq_info.get("value", "")
        seq_length = seq_info.get("length", "")

        # Gene names
        gene_entries = item.get("genes", [])
        gene_names = []
        for g in gene_entries:
            if g.get("geneName"):
                gene_names.append(g["geneName"].get("value", ""))

        # Function
        function_text = ""
        comments = item.get("comments", [])
        for c in comments:
            if c.get("commentType") == "FUNCTION":
                texts = c.get("texts", [])
                if texts:
                    function_text = texts[0].get("value", "")

        # Subcellular location
        location_text = ""
        for c in comments:
            if c.get("commentType") == "SUBCELLULAR LOCATION":
                locations = c.get("subcellularLocations", [])
                loc_parts = []
                for loc in locations:
                    loc_val = loc.get("location", {}).get("value", "")
                    if loc_val:
                        loc_parts.append(loc_val)
                location_text = "; ".join(loc_parts)

        accession = item.get("primaryAccession", "")
        entry_id = item.get("uniProtkbId", "")

        entry = {
            "accession": accession,
            "entry_id": entry_id,
            "protein_name": full_name,
            "gene_names": gene_names,
            "organism": organism,
            "common_name": common_name,
            "sequence": sequence,
            "length": seq_length,
            "function": function_text,
            "subcellular_location": location_text,
        }
        entries.append(entry)

        # Human-readable text
        block = f"\n--- Entry: {accession} ({entry_id}) ---\n"
        block += f"[Source: UniProt | https://www.uniprot.org/uniprotkb/{accession}]\n"
        block += f"Protein Name: {full_name}\n"
        if gene_names:
            block += f"Gene Names: {', '.join(gene_names)}\n"
        block += f"Organism: {organism}"
        if common_name:
            block += f" ({common_name})"
        block += "\n"
        if seq_length:
            block += f"Sequence Length: {seq_length} aa\n"
        if function_text:
            block += f"Function: {function_text}\n"
        if location_text:
            block += f"Subcellular Location: {location_text}\n"
        if sequence:
            display_seq = sequence[:200] + ("..." if len(sequence) > 200 else "")
            block += f"Protein Sequence: {display_seq}\n"
        text_blocks.append(block)

    raw_text = "\n".join(text_blocks)
    return make_result(source, url, entries=entries, raw_text=raw_text)
