"""
engine/prompts.py
─────────────────
Prompt templates for LLM-based protein data extraction.
All prompts require source attribution in the output.
"""

import re
from typing import List

from langchain_core.prompts import ChatPromptTemplate

# ── Field parsing ────────────────────────────────────────────────────────────

DEFAULT_FIELDS = ["ORGANISM", "FUNCTION", "SEQUENCE", "GENE", "REFERENCE", "AUTHOR", "TITLE"]

KNOWN_ALIASES = {
    "organism": "ORGANISM",
    "species": "ORGANISM",
    "reference": "REFERENCE",
    "citation": "REFERENCE",
    "author": "AUTHOR",
    "authors": "AUTHOR",
    "title": "TITLE",
    "protein sequence": "SEQUENCE",
    "sequence": "SEQUENCE",
    "amino acid sequence": "SEQUENCE",
    "accession": "ACCESSION",
    "uniprot id": "UNIPROT_ID",
    "gene": "GENE",
    "gene name": "GENE",
    "function": "FUNCTION",
    "length": "LENGTH",
    "subcellular location": "SUBCELLULAR_LOCATION",
    "structure": "STRUCTURE",
    "interactions": "INTERACTIONS",
    "pathways": "PATHWAYS",
    "domains": "DOMAINS",
}


def parse_requested_fields(description: str) -> List[str]:
    """Parse user's field description into canonical field names."""
    if not description or not description.strip():
        return DEFAULT_FIELDS.copy()

    fields = []
    lower_text = description.lower().strip()

    for alias, canonical in KNOWN_ALIASES.items():
        if alias in lower_text and canonical not in fields:
            fields.append(canonical)

    parts = re.split(r"[,;\n]|\band\b", description, flags=re.IGNORECASE)
    for part in parts:
        key = re.sub(r"[^a-zA-Z0-9]+", "_", part.strip()).strip("_").upper()
        if key and key not in fields:
            fields.append(key)

    return fields[:15] if fields else DEFAULT_FIELDS.copy()


def format_field_schema(fields: List[str]) -> str:
    """Generate JSON schema fragment for the prompt."""
    return "\n".join([f'    "{f}": string or null,' for f in fields]).rstrip(",")


# ── Main extraction prompt ───────────────────────────────────────────────────

EXTRACTION_TEMPLATE = """\
You are a biomedical data extraction assistant specialized in protein databases.

Protein query: {protein_name}
User requested fields: {fields_display}

Read ALL the context below carefully. The context comes from multiple protein databases.
Each section has a [Source: ...] tag indicating which database it came from.

IMPORTANT: For every extracted field, you MUST specify which database source it came from.

Return ONLY one JSON object (no markdown fences, no explanation) with this exact schema:
{{
  "verdict": "Valid" | "Invalid" | "Uncertain",
  "confidence": integer 0-100,
  "summary": "Brief summary of findings about this protein",
  "extracted_fields": {{
{field_schema}
  }},
  "source_attribution": {{
    "field_name": "Database name where this field was found"
  }},
  "evidence": [
    {{"quote": "exact short quote from context", "source": "database name", "why_relevant": "short reason"}}
  ]
}}

Rules:
1) Return raw JSON only. No markdown code fences.
2) confidence is an integer from 0 to 100.
3) For each field in extracted_fields, add a corresponding entry in source_attribution.
4) Keep evidence list small (1-5 items). Each evidence item must include "source".
5) If the query protein is not found in the context, use verdict "Invalid".
6) For sequence fields, return the actual amino acid sequence when available.
7) Prefer information from primary databases (UniProt, NCBI) over secondary ones.

Context from protein databases:
{context}
"""

EXTRACTION_PROMPT = ChatPromptTemplate.from_template(EXTRACTION_TEMPLATE)
