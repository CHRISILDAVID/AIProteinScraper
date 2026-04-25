"""
sources/string_db.py
────────────────────
Fetch protein interaction data from STRING-db REST API.
"""

import logging
from sources.base import SESSION, throttle, make_result, SourceResult

logger = logging.getLogger(__name__)


def fetch_string(protein_name: str, species: int = 9606, max_results: int = 5) -> SourceResult:
    """Search STRING-db for protein interactions and functional enrichment."""
    source = "STRING"
    url = f"https://string-db.org/network/{protein_name}"
    base_url = "https://string-db.org/api"

    # Step 1: Resolve protein name to STRING identifiers
    resolve_url = f"{base_url}/json/get_string_ids"
    resolve_params = {
        "identifiers": protein_name,
        "species": species,
        "limit": max_results,
        "caller_identity": "ProtScrape",
    }

    try:
        throttle()
        resolve_resp = SESSION.get(resolve_url, params=resolve_params, timeout=30)
        resolve_resp.raise_for_status()
        resolved = resolve_resp.json()
    except Exception as exc:
        logger.warning("STRING resolve failed: %s", exc)
        return make_result(source, url, error=str(exc))

    if not resolved:
        return make_result(
            source, url,
            raw_text=f"No STRING entries found for '{protein_name}' (species={species}).",
        )

    entries = []
    text_blocks = [f"=== STRING Results for '{protein_name}' (taxid={species}) ===\n"]

    string_ids = []
    for item in resolved[:max_results]:
        string_id = item.get("stringId", "")
        preferred_name = item.get("preferredName", "")
        annotation = item.get("annotation", "")

        string_ids.append(string_id)

        entry = {
            "string_id": string_id,
            "preferred_name": preferred_name,
            "annotation": annotation,
        }
        entries.append(entry)

        block = f"\n--- STRING Protein: {preferred_name} ({string_id}) ---\n"
        block += f"[Source: STRING | https://string-db.org/network/{preferred_name}]\n"
        if annotation:
            block += f"Annotation: {annotation}\n"
        text_blocks.append(block)

    # Step 2: Interaction network
    if string_ids:
        try:
            throttle()
            network_url = f"{base_url}/json/network"
            network_params = {
                "identifiers": string_ids[0],
                "species": species,
                "limit": 10,
                "caller_identity": "ProtScrape",
            }
            net_resp = SESSION.get(network_url, params=network_params, timeout=30)
            if net_resp.status_code == 200:
                network = net_resp.json()
                if network:
                    text_blocks.append(f"\n--- Interaction Network for {string_ids[0]} ---\n")
                    partners = set()
                    for interaction in network[:10]:
                        pref_a = interaction.get("preferredName_A", "")
                        pref_b = interaction.get("preferredName_B", "")
                        score = interaction.get("score", 0)
                        partners.add(
                            pref_b if pref_a == resolved[0].get("preferredName") else pref_a
                        )
                        text_blocks.append(
                            f"  Interaction: {pref_a} ↔ {pref_b} (score: {score:.3f})\n"
                        )
                    if entries:
                        entries[0]["interaction_partners"] = list(partners)[:10]
        except Exception as exc:
            logger.warning("STRING network failed: %s", exc)

        # Step 3: Functional enrichment
        try:
            throttle()
            enrich_url = f"{base_url}/json/enrichment"
            enrich_params = {
                "identifiers": string_ids[0],
                "species": species,
                "caller_identity": "ProtScrape",
            }
            enrich_resp = SESSION.get(enrich_url, params=enrich_params, timeout=30)
            if enrich_resp.status_code == 200:
                enrichment = enrich_resp.json()
                if enrichment:
                    text_blocks.append(f"\n--- Functional Enrichment ---\n")
                    for term in enrichment[:5]:
                        category = term.get("category", "")
                        description = term.get("description", "")
                        p_value = term.get("p_value", "")
                        text_blocks.append(
                            f"  [{category}] {description} (p={p_value})\n"
                        )
        except Exception as exc:
            logger.warning("STRING enrichment failed: %s", exc)

    raw_text = "\n".join(text_blocks)
    return make_result(source, url, entries=entries, raw_text=raw_text)
