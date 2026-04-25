"""
engine/pipeline.py
──────────────────
End-to-end RAG pipeline: ingest → chunk → embed → retrieve → LLM extract.
"""

import json
import re
import os
import logging
from typing import Dict, List, Optional, Any

from sources.base import SourceResult
from engine.chunker import split_text
from engine.embeddings import get_embedding_function, get_embedding_model_name
from engine.vectorstore import build_vectorstore, query_vectorstore
from engine.llm import get_llm, resolve_provider, resolve_model_name
from engine.prompts import (
    EXTRACTION_PROMPT,
    parse_requested_fields,
    format_field_schema,
)

logger = logging.getLogger(__name__)


def _response_to_text(response) -> str:
    """Extract text from various LLM response types."""
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


def _extract_json_object(text: str) -> str:
    """Pull the first JSON object from text, stripping code fences."""
    cleaned = text.strip()
    # Strip markdown code fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_\-]*\s*", "", cleaned)
    if cleaned.endswith("```"):
        cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start : end + 1]
    return cleaned


def _normalize_result(
    parsed: dict,
    raw_response: str,
    requested_fields: List[str],
) -> dict:
    """Normalize LLM output into a consistent structure."""
    default_fields = {f: None for f in requested_fields}
    default = {
        "verdict": "Uncertain",
        "confidence": 0,
        "summary": "Could not parse model output.",
        "extracted_fields": default_fields,
        "source_attribution": {},
        "evidence": [],
    }

    if not isinstance(parsed, dict):
        default["raw_response"] = (raw_response or "")[:1000]
        return default

    verdict = parsed.get("verdict", "Uncertain")
    if verdict not in {"Valid", "Invalid", "Uncertain"}:
        verdict = "Uncertain"

    confidence = parsed.get("confidence", 0)
    try:
        confidence = max(0, min(100, int(confidence)))
    except (TypeError, ValueError):
        confidence = 0

    extracted = parsed.get("extracted_fields", {})
    if not isinstance(extracted, dict):
        extracted = {}

    attribution = parsed.get("source_attribution", {})
    if not isinstance(attribution, dict):
        attribution = {}

    evidence = parsed.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []
    normalized_evidence = []
    for item in evidence[:5]:
        if isinstance(item, dict):
            normalized_evidence.append({
                "quote": item.get("quote", ""),
                "source": item.get("source", ""),
                "why_relevant": item.get("why_relevant", ""),
            })

    return {
        "verdict": verdict,
        "confidence": confidence,
        "summary": parsed.get("summary") or "No summary provided.",
        "extracted_fields": {f: extracted.get(f) for f in requested_fields},
        "source_attribution": attribution,
        "evidence": normalized_evidence,
    }


def _keyword_score_chunks(
    chunks: List[str],
    protein_name: str,
    query: str,
    top_k: int,
) -> List[str]:
    """Fallback keyword-based chunk scoring when embeddings fail."""
    protein_lower = (protein_name or "").lower().strip()
    query_tokens = set(
        re.findall(r"[a-z0-9]{3,}", (query or "").lower())
    )

    scored = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = sum(chunk_lower.count(t) for t in query_tokens)
        if protein_lower:
            score += chunk_lower.count(protein_lower) * 5
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [c for s, c in scored if s > 0][:top_k]
    return picked if picked else chunks[:top_k]


def run_pipeline(
    protein_name: str,
    query: str,
    source_results: Dict[str, SourceResult],
    provider: str = "gemini",
    model: Optional[str] = None,
    use_rag: bool = True,
    top_k: int = 6,
) -> Dict[str, Any]:
    """
    End-to-end pipeline: ingest API results → RAG retrieve → LLM extract.

    Parameters
    ----------
    protein_name : str
        The protein being queried.
    query : str
        User's field/extraction request (e.g., "ORGANISM, FUNCTION, SEQUENCE").
    source_results : dict[str, SourceResult]
        Results from fetch_all_sources().
    provider : str
        LLM provider: "gemini", "openai", "ollama".
    model : str | None
        Model override.
    use_rag : bool
        Whether to use embedding-based RAG retrieval.
    top_k : int
        Number of chunks to send to the LLM.

    Returns
    -------
    dict with keys: verdict, confidence, summary, extracted_fields,
    source_attribution, evidence, model, retrieval, sources_used
    """
    resolved_provider = resolve_provider(provider)
    resolved_model = resolve_model_name(resolved_provider, model)
    requested_fields = parse_requested_fields(query)
    fields_display = ", ".join(requested_fields)
    field_schema = format_field_schema(requested_fields)

    # ── 1. Collect raw text from all successful sources ──────────────────
    all_chunks = []
    all_metadata = []
    sources_used = {}

    for name, result in source_results.items():
        if not result.ok:
            sources_used[name] = {
                "status": "error",
                "error": result.error,
                "url": result.url,
                "entries": 0,
            }
            continue

        sources_used[name] = {
            "status": "ok",
            "url": result.url,
            "entries": result.entry_count,
        }

        chunks = split_text(result.raw_text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "source": name,
                "url": result.url,
                "chunk_index": i,
                "length": len(chunk),
            })

    if not all_chunks:
        return {
            "verdict": "Invalid",
            "confidence": 0,
            "summary": "No data retrieved from any source.",
            "extracted_fields": {f: None for f in requested_fields},
            "source_attribution": {},
            "evidence": [],
            "requested_fields": requested_fields,
            "model": {"provider": resolved_provider, "name": resolved_model},
            "retrieval": {"enabled": use_rag, "chunks_total": 0, "chunks_sent": 0},
            "sources_used": sources_used,
        }

    # ── 2. RAG retrieval ─────────────────────────────────────────────────
    retrieval_method = "none"
    embedding_model_used = None
    selected_chunks = all_chunks[:top_k]

    if use_rag:
        rag_query = f"{protein_name} {query}"
        try:
            embedding_fn = get_embedding_function(
                resolved_provider,
                api_key=(
                    os.getenv("OPENAI_API_KEY") if resolved_provider == "openai"
                    else os.getenv("GOOGLE_API_KEY") if resolved_provider == "gemini"
                    else None
                ),
            )
            vectorstore = build_vectorstore(all_chunks, all_metadata, embedding_fn)
            retrieved = query_vectorstore(vectorstore, rag_query, top_k=top_k)
            selected_chunks = [r["content"] for r in retrieved]
            retrieval_method = "embedding"
            embedding_model_used = get_embedding_model_name(resolved_provider)
            logger.info(
                "Embedding retrieval succeeded (%s): %d chunks",
                embedding_model_used,
                len(selected_chunks),
            )
        except Exception as exc:
            logger.warning("Embedding retrieval failed, falling back to keywords: %s", exc)
            selected_chunks = _keyword_score_chunks(
                all_chunks, protein_name, query, top_k
            )
            retrieval_method = "keyword_fallback"
    else:
        selected_chunks = all_chunks[:top_k]

    context = "\n\n---\n\n".join(selected_chunks)

    # ── 3. LLM extraction ────────────────────────────────────────────────
    try:
        llm, _, _ = get_llm(resolved_provider, resolved_model)
        chain = EXTRACTION_PROMPT | llm

        response = chain.invoke({
            "protein_name": protein_name,
            "fields_display": fields_display,
            "field_schema": field_schema,
            "context": context,
        })

        response_text = _response_to_text(response)
        parsed = json.loads(_extract_json_object(response_text))
    except Exception as exc:
        logger.error("LLM extraction failed: %s", exc)
        return {
            "verdict": "Uncertain",
            "confidence": 0,
            "summary": f"LLM extraction failed: {exc}",
            "extracted_fields": {f: None for f in requested_fields},
            "source_attribution": {},
            "evidence": [],
            "requested_fields": requested_fields,
            "model": {"provider": resolved_provider, "name": resolved_model},
            "retrieval": {
                "enabled": use_rag,
                "method": retrieval_method,
                "embedding_model": embedding_model_used,
                "chunks_total": len(all_chunks),
                "chunks_sent": len(selected_chunks),
            },
            "sources_used": sources_used,
        }

    # ── 4. Normalize & return ────────────────────────────────────────────
    result = _normalize_result(parsed, response_text, requested_fields)
    result["requested_fields"] = requested_fields
    result["model"] = {"provider": resolved_provider, "name": resolved_model}
    result["retrieval"] = {
        "enabled": use_rag,
        "method": retrieval_method,
        "embedding_model": embedding_model_used,
        "chunks_total": len(all_chunks),
        "chunks_sent": len(selected_chunks),
    }
    result["sources_used"] = sources_used
    return result
