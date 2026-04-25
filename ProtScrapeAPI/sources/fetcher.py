"""
sources/fetcher.py
──────────────────
Orchestrator: runs all (or selected) database fetchers concurrently.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from sources.base import SourceResult, make_result
from sources.uniprot import fetch_uniprot
from sources.pdb import fetch_pdb
from sources.ncbi import fetch_ncbi
from sources.interpro import fetch_interpro
from sources.kegg import fetch_kegg
from sources.string_db import fetch_string

logger = logging.getLogger(__name__)

# ── Registry ─────────────────────────────────────────────────────────────────

ALL_SOURCES = {
    "UniProt": fetch_uniprot,
    "PDB": fetch_pdb,
    "NCBI Protein": fetch_ncbi,
    "InterPro": fetch_interpro,
    "KEGG": fetch_kegg,
    "STRING": fetch_string,
}

SOURCE_DESCRIPTIONS = {
    "UniProt": "Protein sequences, functions & annotations",
    "PDB": "3D protein structures with experimental data",
    "NCBI Protein": "NCBI protein records, references & sequences",
    "InterPro": "Protein families, domains & functional sites",
    "KEGG": "Genes, pathways & metabolic networks",
    "STRING": "Protein-protein interaction networks",
}

SOURCE_ICONS = {
    "UniProt": "🧬",
    "PDB": "🔬",
    "NCBI Protein": "📚",
    "InterPro": "🏷️",
    "KEGG": "🗺️",
    "STRING": "🕸️",
}


def fetch_all_sources(
    protein_name: str,
    sources: Optional[List[str]] = None,
    max_results: int = 5,
) -> Dict[str, SourceResult]:
    """
    Run selected (or all) database API fetchers concurrently.

    Parameters
    ----------
    protein_name : str
        The protein to search for.
    sources : list[str] or None
        Which sources to query. None = all 6.
    max_results : int
        Max entries per source.

    Returns
    -------
    dict[str, SourceResult]
    """
    selected = sources or list(ALL_SOURCES.keys())
    results: Dict[str, SourceResult] = {}

    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_name = {}
        for name in selected:
            fetcher = ALL_SOURCES.get(name)
            if not fetcher:
                logger.warning("Unknown source: %s", name)
                continue
            future = executor.submit(fetcher, protein_name, max_results=max_results)
            future_to_name[future] = name

        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                results[name] = future.result()
            except Exception as exc:
                logger.error("Fetcher %s crashed: %s", name, exc)
                results[name] = make_result(name, "", error=str(exc))

    return results
