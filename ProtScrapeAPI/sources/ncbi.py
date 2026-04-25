"""
sources/ncbi.py
───────────────
Fetch protein data from NCBI via E-Utilities (esearch → efetch).
"""

import logging
from sources.base import SESSION, throttle, make_result, SourceResult

logger = logging.getLogger(__name__)


def fetch_ncbi(protein_name: str, max_results: int = 5) -> SourceResult:
    """Search NCBI Protein via esearch → efetch (GenPept + FASTA)."""
    source = "NCBI Protein"
    url = f"https://www.ncbi.nlm.nih.gov/protein/?term={protein_name}"

    # Step 1: esearch
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    esearch_params = {
        "db": "protein",
        "term": protein_name,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
    }

    try:
        throttle()
        search_resp = SESSION.get(esearch_url, params=esearch_params, timeout=30)
        search_resp.raise_for_status()
        search_data = search_resp.json()
    except Exception as exc:
        logger.warning("NCBI esearch failed: %s", exc)
        return make_result(source, url, error=str(exc))

    id_list = search_data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return make_result(source, url, raw_text=f"No NCBI Protein entries found for '{protein_name}'.")

    # Step 2: efetch GenPept
    efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    genpept_text = ""
    try:
        throttle()
        gp_params = {
            "db": "protein",
            "id": ",".join(id_list),
            "rettype": "gp",
            "retmode": "text",
        }
        fetch_resp = SESSION.get(efetch_url, params=gp_params, timeout=45)
        fetch_resp.raise_for_status()
        genpept_text = fetch_resp.text
    except Exception as exc:
        logger.warning("NCBI efetch (gp) failed: %s", exc)

    # Step 3: efetch FASTA
    fasta_text = ""
    try:
        throttle(0.3, 0.6)
        fasta_params = {
            "db": "protein",
            "id": ",".join(id_list),
            "rettype": "fasta",
            "retmode": "text",
        }
        fasta_resp = SESSION.get(efetch_url, params=fasta_params, timeout=30)
        fasta_resp.raise_for_status()
        fasta_text = fasta_resp.text
    except Exception as exc:
        logger.warning("NCBI efetch (fasta) failed: %s", exc)

    # Parse FASTA
    fasta_entries = {}
    if fasta_text:
        current_header = ""
        current_seq = []
        for line in fasta_text.strip().splitlines():
            if line.startswith(">"):
                if current_header and current_seq:
                    fasta_entries[current_header] = "".join(current_seq)
                current_header = line[1:].strip()
                current_seq = []
            else:
                current_seq.append(line.strip())
        if current_header and current_seq:
            fasta_entries[current_header] = "".join(current_seq)

    # Parse GenPept records
    entries = []
    text_blocks = [f"=== NCBI Protein Results for '{protein_name}' ===\n"]

    if genpept_text:
        records = genpept_text.split("//\n")
        for record in records:
            if not record.strip():
                continue

            accession = ""
            definition = ""
            organism = ""
            authors_list = []
            title = ""
            journal = ""

            for line in record.splitlines():
                if line.startswith("ACCESSION"):
                    accession = line.replace("ACCESSION", "").strip().split()[0]
                elif line.startswith("DEFINITION"):
                    definition = line.replace("DEFINITION", "").strip()
                elif line.startswith("  ORGANISM"):
                    organism = line.replace("ORGANISM", "").strip()
                elif line.startswith("  AUTHORS"):
                    authors_list.append(line.replace("AUTHORS", "").strip())
                elif line.startswith("  TITLE"):
                    title = line.replace("TITLE", "").strip()
                elif line.startswith("  JOURNAL"):
                    journal = line.replace("JOURNAL", "").strip()

            # Match FASTA sequence
            sequence = ""
            for header, seq in fasta_entries.items():
                if accession and accession in header:
                    sequence = seq
                    break

            if not accession:
                continue

            entry = {
                "accession": accession,
                "definition": definition,
                "organism": organism,
                "authors": authors_list,
                "title": title,
                "journal": journal,
                "sequence": sequence,
                "length": len(sequence) if sequence else None,
            }
            entries.append(entry)

            block = f"\n--- NCBI Protein: {accession} ---\n"
            block += f"[Source: NCBI | https://www.ncbi.nlm.nih.gov/protein/{accession}]\n"
            block += f"Definition: {definition}\n"
            if organism:
                block += f"Organism: {organism}\n"
            if title:
                block += f"Reference Title: {title}\n"
            if authors_list:
                block += f"Authors: {'; '.join(authors_list[:3])}\n"
            if journal:
                block += f"Journal: {journal}\n"
            if sequence:
                block += f"Sequence Length: {len(sequence)} aa\n"
                display_seq = sequence[:200] + ("..." if len(sequence) > 200 else "")
                block += f"Protein Sequence: {display_seq}\n"
            text_blocks.append(block)

    # Fallback to FASTA if GenPept failed
    if not entries and fasta_entries:
        for header, seq in fasta_entries.items():
            acc = header.split()[0] if header else ""
            entry = {
                "accession": acc,
                "definition": header,
                "organism": "",
                "sequence": seq,
                "length": len(seq),
            }
            entries.append(entry)

            block = f"\n--- NCBI Protein: {acc} ---\n"
            block += f"[Source: NCBI | https://www.ncbi.nlm.nih.gov/protein/{acc}]\n"
            block += f"Header: {header}\n"
            block += f"Sequence Length: {len(seq)} aa\n"
            display_seq = seq[:200] + ("..." if len(seq) > 200 else "")
            block += f"Protein Sequence: {display_seq}\n"
            text_blocks.append(block)

    raw_text = "\n".join(text_blocks)
    return make_result(source, url, entries=entries, raw_text=raw_text)
