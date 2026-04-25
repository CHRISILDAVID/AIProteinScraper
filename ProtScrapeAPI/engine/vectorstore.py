"""
engine/vectorstore.py
─────────────────────
ChromaDB vector store: build from chunks + metadata, query by similarity.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def build_vectorstore(
    chunks: List[str],
    metadata_list: List[Dict[str, Any]],
    embedding_fn,
    collection_name: Optional[str] = None,
):
    """
    Build an ephemeral ChromaDB vector store from text chunks.

    Parameters
    ----------
    chunks : list[str]
        Text chunks to index.
    metadata_list : list[dict]
        One metadata dict per chunk (source, url, chunk_index).
    embedding_fn : Embeddings
        LangChain-compatible embedding function.
    collection_name : str | None
        Optional collection name.

    Returns
    -------
    Chroma vector store instance.
    """
    try:
        from langchain_chroma import Chroma
    except ImportError as exc:
        raise ImportError(
            "langchain-chroma is not installed. "
            "Run: pip install langchain-chroma chromadb"
        ) from exc

    if not collection_name:
        collection_name = f"protscrape_{uuid.uuid4().hex[:8]}"

    # Ensure metadata list matches chunks
    if len(metadata_list) != len(chunks):
        metadata_list = [
            {"chunk_index": i, "length": len(c)} for i, c in enumerate(chunks)
        ]

    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embedding_fn,
        metadatas=metadata_list,
        collection_name=collection_name,
    )
    return vectorstore


def query_vectorstore(
    vectorstore,
    query: str,
    top_k: int = 6,
) -> List[Dict[str, Any]]:
    """
    Retrieve the top-k most relevant chunks with metadata.

    Returns
    -------
    list[dict] — each with "content", "metadata", "score"
    """
    results = vectorstore.similarity_search_with_relevance_scores(query, k=top_k)

    retrieved = []
    for doc, score in results:
        retrieved.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": score,
        })

    return retrieved
