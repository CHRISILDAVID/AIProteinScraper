import json
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

from rag_engine import retrieve_with_embeddings

dotenv_path = Path(".env")
load_dotenv(dotenv_path=dotenv_path)

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_MODEL_CACHE = {}


template = """
You are a biomedical information extraction assistant.

Protein query: {protein_name}
Data source: {source_name}
User requested fields: {requested_fields_display}

Read the context and decide if it is truly about the exact protein query.
Return ONLY one JSON object (no markdown, no code fences) with this schema:
{{
  "verdict": "Valid" | "Invalid" | "Uncertain",
  "confidence": 0,
  "summary": "short summary",
    "extracted_fields": {{
{field_schema}
    }},
  "evidence": [
    {{"quote": "exact short quote from context", "why_relevant": "short reason"}}
  ]
}}

Rules:
1) JSON only.
2) If evidence is weak or conflicting, use "Uncertain".
3) Confidence must be an integer from 0 to 100.
4) Keep evidence list small (0 to 3 items).
5) Prefer exact query matches over related variants.
6) In extracted_fields, use exactly the requested keys and no extras.
7) For sequence-related fields, return the literal amino-acid sequence when available.

Context:
{dom_content}
"""

DEFAULT_REQUESTED_FIELDS = ["ORGANISM", "REFERENCE", "AUTHOR", "TITLE"]

KNOWN_FIELD_ALIASES = {
    "organism": "ORGANISM",
    "species": "ORGANISM",
    "reference": "REFERENCE",
    "citation": "REFERENCE",
    "author": "AUTHOR",
    "authors": "AUTHOR",
    "title": "TITLE",
    "protein sequence": "PROTEIN_SEQUENCE",
    "sequence": "PROTEIN_SEQUENCE",
    "amino acid sequence": "PROTEIN_SEQUENCE",
    "accession": "ACCESSION",
    "uniprot id": "UNIPROT_ID",
    "gene": "GENE",
    "function": "FUNCTION",
    "length": "LENGTH",
    "subcellular location": "SUBCELLULAR_LOCATION",
}


def _resolve_provider(llm_provider):
    provider = (llm_provider or "ollama").strip().lower()
    if provider in {"openai", "openai api", "openai_api"}:
        return "openai"
    if provider in {"gemini", "google", "gemini api", "google_gemini"}:
        return "gemini"
    return "ollama"


def _resolve_model_name(provider, llm_model):
    if llm_model and llm_model.strip():
        return llm_model.strip()
    if provider == "openai":
        return DEFAULT_OPENAI_MODEL
    if provider == "gemini":
        return DEFAULT_GEMINI_MODEL
    return DEFAULT_OLLAMA_MODEL


def _get_llm(llm_provider, llm_model):
    provider = _resolve_provider(llm_provider)
    model_name = _resolve_model_name(provider, llm_model)
    cache_key = (provider, model_name)

    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key], provider, model_name

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in .env.")

        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise ValueError(
                "langchain-openai is not installed. Install dependencies from requirements.txt."
            ) from exc

        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=0,
        )

    elif provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in .env.")

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise ValueError(
                "langchain-google-genai is not installed. "
                "Run: pip install langchain-google-genai"
            ) from exc

        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0,
        )

    else:
        llm = OllamaLLM(model=model_name)

    _MODEL_CACHE[cache_key] = llm
    return llm, provider, model_name


def _response_to_text(response):
    if isinstance(response, str):
        return response

    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    text_parts.append(text)
            elif isinstance(item, str):
                text_parts.append(item)
        if text_parts:
            return "\n".join(text_parts)

    return str(response)


def _tokenize(text):
    return [token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(token) > 2]


def _to_field_key(label):
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", (label or "").strip()).strip("_")
    return normalized.upper() if normalized else ""


def _parse_requested_fields(parse_description):
    if not parse_description or not parse_description.strip():
        return DEFAULT_REQUESTED_FIELDS.copy()

    fields = []
    text = parse_description.strip()
    lower_text = text.lower()

    for alias, canonical in KNOWN_FIELD_ALIASES.items():
        if alias in lower_text and canonical not in fields:
            fields.append(canonical)

    parts = re.split(r"[,;\n]|\band\b", text, flags=re.IGNORECASE)
    for part in parts:
        key = _to_field_key(part)
        if key and key not in fields:
            fields.append(key)

    if not fields:
        return DEFAULT_REQUESTED_FIELDS.copy()

    return fields[:12]


def _format_field_schema(requested_fields):
    return "\n".join([f'    "{field}": string or null,' for field in requested_fields]).rstrip(",")


def _score_chunk(chunk, protein_name, parse_description, source_name):
    chunk_lower = chunk.lower()
    query_tokens = set(
        _tokenize(
            " ".join(
                [
                    protein_name,
                    parse_description,
                    source_name,
                    "protein sequence organism gene reference author title",
                ]
            )
        )
    )

    score = 0
    for token in query_tokens:
        score += chunk_lower.count(token)

    protein_term = (protein_name or "").lower().strip()
    if protein_term:
        score += chunk_lower.count(protein_term) * 5

    return score


def _retrieve_relevant_chunks(dom_chunks, protein_name, parse_description, source_name, top_k):
    if not dom_chunks:
        return []

    scored_chunks = []
    for idx, chunk in enumerate(dom_chunks):
        score = _score_chunk(chunk, protein_name, parse_description, source_name)
        scored_chunks.append((score, idx, chunk))

    scored_chunks.sort(key=lambda item: (item[0], -item[1]), reverse=True)

    picked = [chunk for score, _, chunk in scored_chunks if score > 0][:top_k]
    if picked:
        return picked

    return dom_chunks[:top_k]


def _strip_code_fences(text):
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_\-]*\s*", "", cleaned)
    if cleaned.endswith("```"):
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_json_object(text):
    cleaned = _strip_code_fences(text)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start : end + 1]
    return cleaned


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_response(parsed, raw_response, requested_fields):
    default_fields = {field: None for field in requested_fields}
    default_result = {
        "verdict": "Uncertain",
        "confidence": 0,
        "summary": "Could not parse model output into structured JSON.",
        "extracted_fields": default_fields,
        "evidence": [],
    }

    if not isinstance(parsed, dict):
        default_result["raw_response"] = (raw_response or "")[:1000]
        return default_result

    verdict = parsed.get("verdict", "Uncertain")
    if verdict not in {"Valid", "Invalid", "Uncertain"}:
        verdict = "Uncertain"

    confidence = max(0, min(100, _to_int(parsed.get("confidence", 0), default=0)))

    extracted_fields = parsed.get("extracted_fields", {})
    if not isinstance(extracted_fields, dict):
        extracted_fields = {}

    evidence = parsed.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []

    normalized_evidence = []
    for item in evidence[:3]:
        if isinstance(item, dict):
            normalized_evidence.append(
                {
                    "quote": item.get("quote"),
                    "why_relevant": item.get("why_relevant"),
                }
            )

    return {
        "verdict": verdict,
        "confidence": confidence,
        "summary": parsed.get("summary") or "No summary provided.",
        "extracted_fields": {
            field: extracted_fields.get(field) for field in requested_fields
        },
        "evidence": normalized_evidence,
    }


def parse_with_ollama(
    dom_chunks,
    parse_description,
    protein_name,
    source_name,
    use_rag=True,
    rag_top_k=4,
    llm_provider="ollama",
    llm_model=None,
):
    prompt = ChatPromptTemplate.from_template(template)
    requested_fields = _parse_requested_fields(parse_description)
    requested_fields_display = ", ".join(requested_fields)
    field_schema = _format_field_schema(requested_fields)

    try:
        llm, resolved_provider, resolved_model = _get_llm(llm_provider, llm_model)
    except Exception as exc:
        return {
            "verdict": "Uncertain",
            "confidence": 0,
            "summary": f"Model initialization failed: {exc}",
            "extracted_fields": {field: None for field in requested_fields},
            "evidence": [],
            "requested_fields": requested_fields,
            "model": {
                "provider": _resolve_provider(llm_provider),
                "name": _resolve_model_name(_resolve_provider(llm_provider), llm_model),
            },
            "retrieval": {
                "enabled": bool(use_rag),
                "chunks_considered": len(dom_chunks) if dom_chunks else 0,
                "chunks_sent": 0,
            },
        }

    chain = prompt | llm

    if not dom_chunks:
        return {
            "verdict": "Invalid",
            "confidence": 0,
            "summary": "No content available for parsing.",
            "extracted_fields": {field: None for field in requested_fields},
            "evidence": [],
            "requested_fields": requested_fields,
            "model": {
                "provider": resolved_provider,
                "name": resolved_model,
            },
            "retrieval": {
                "enabled": bool(use_rag),
                "chunks_considered": 0,
                "chunks_sent": 0,
            },
        }

    max_chunks = max(1, rag_top_k)
    retrieval_method = "none"
    embedding_model_used = None

    if use_rag:
        # ── Attempt real embedding-based retrieval ────────────────────
        rag_query = " ".join(
            filter(None, [protein_name, parse_description, source_name])
        )
        rag_result = retrieve_with_embeddings(
            dom_chunks,
            query=rag_query,
            provider=resolved_provider,
            top_k=max_chunks,
            api_key=(
                os.getenv("OPENAI_API_KEY") if resolved_provider == "openai"
                else os.getenv("GOOGLE_API_KEY") if resolved_provider == "gemini"
                else None
            ),
        )

        if rag_result["chunks"] and not rag_result["error"]:
            selected_chunks = rag_result["chunks"]
            retrieval_method = "embedding"
            embedding_model_used = rag_result.get("model")
            logger.info(
                "Embedding retrieval succeeded (%s): %d chunks",
                embedding_model_used,
                len(selected_chunks),
            )
        else:
            # ── Fallback: keyword-based scoring ──────────────────────
            logger.warning(
                "Embedding retrieval failed (%s), falling back to keyword scoring.",
                rag_result.get("error", "unknown"),
            )
            selected_chunks = _retrieve_relevant_chunks(
                dom_chunks,
                protein_name,
                parse_description,
                source_name,
                top_k=max_chunks,
            )
            retrieval_method = "keyword_fallback"
    else:
        selected_chunks = dom_chunks[:max_chunks]

    context = "\n\n---\n\n".join(selected_chunks)

    try:
        response = chain.invoke(
            {
                "dom_content": context,
                "parse_description": parse_description,
                "protein_name": protein_name,
                "source_name": source_name,
                "requested_fields_display": requested_fields_display,
                "field_schema": field_schema,
            }
        )
        response_text = _response_to_text(response)
        parsed = json.loads(_extract_json_object(response_text))
    except Exception as exc:
        return {
            "verdict": "Uncertain",
            "confidence": 0,
            "summary": f"Parsing failed: {exc}",
            "extracted_fields": {field: None for field in requested_fields},
            "evidence": [],
            "requested_fields": requested_fields,
            "model": {
                "provider": resolved_provider,
                "name": resolved_model,
            },
            "retrieval": {
                "enabled": bool(use_rag),
                "retrieval_method": retrieval_method,
                "embedding_model": embedding_model_used,
                "chunks_considered": len(dom_chunks),
                "chunks_sent": len(selected_chunks),
            },
            "raw_response": response_text[:1000] if "response_text" in locals() else None,
        }

    result = _normalize_response(parsed, response_text, requested_fields)
    result["requested_fields"] = requested_fields
    result["model"] = {
        "provider": resolved_provider,
        "name": resolved_model,
    }
    result["retrieval"] = {
        "enabled": bool(use_rag),
        "retrieval_method": retrieval_method,
        "embedding_model": embedding_model_used,
        "chunks_considered": len(dom_chunks),
        "chunks_sent": len(selected_chunks),
    }
    return result
