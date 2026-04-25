"""
engine/chunker.py
─────────────────
Text splitting utilities for the RAG pipeline.
Splits raw_text from API sources into manageable chunks for embedding.
"""

from typing import List


def split_text(text: str, max_length: int = 4000) -> List[str]:
    """
    Split text into chunks, preserving paragraph boundaries when possible.

    Each chunk carries a [Source: ...] tag if one was found in its section.
    """
    if not text or not text.strip():
        return []

    # Try to split on section boundaries first
    sections = text.split("\n---")
    chunks = []
    current_chunk = ""

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Re-add the delimiter for non-first sections
        if current_chunk:
            candidate = current_chunk + "\n---" + section
        else:
            candidate = section

        if len(candidate) <= max_length:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If a single section is too long, split it further
            if len(section) > max_length:
                sub_chunks = _split_by_length(section, max_length)
                chunks.extend(sub_chunks)
                current_chunk = ""
            else:
                current_chunk = section

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _split_by_length(text: str, max_length: int) -> List[str]:
    """Fallback: split by newlines respecting max_length."""
    lines = text.split("\n")
    chunks = []
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > max_length:
            if current:
                chunks.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line

    if current:
        chunks.append(current)

    return chunks
