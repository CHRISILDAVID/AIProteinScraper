"""
rag_engine.py
─────────────
Embedding-based retrieval module for AIProteinScraper.

Provides real vector-similarity retrieval using:
  • OpenAI  → text-embedding-3-small        (fast, cheap cloud embeddings)
  • Gemini  → models/text-embedding-004      (free tier Google embeddings)
  • Ollama  → nomic-embed-text               (free, local embeddings)

ChromaDB is used as an ephemeral in-memory vector store — chunks are
re-indexed per scrape/parse session, so no persistence is needed.
"""

import os
import uuid
import logging
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

dotenv_path = Path(".env")
load_dotenv(dotenv_path=dotenv_path)

logger = logging.getLogger(__name__)

# ── Default embedding model names ────────────────────────────────────────────
DEFAULT_EMBEDDING_MODEL_OPENAI = os.getenv(
    "EMBEDDING_MODEL_OPENAI", "text-embedding-3-small"
)
DEFAULT_EMBEDDING_MODEL_GEMINI = os.getenv(
    "EMBEDDING_MODEL_GEMINI", "models/gemini-embedding-001"
)
DEFAULT_EMBEDDING_MODEL_OLLAMA = os.getenv(
    "EMBEDDING_MODEL_OLLAMA", "nomic-embed-text"
)


# ── Embedding function factory ───────────────────────────────────────────────

def get_embedding_function(provider: str, api_key: Optional[str] = None):
    """
    Return a LangChain-compatible embedding function for the given provider.

    Parameters
    ----------
    provider : str
        "openai" or "ollama"
    api_key : str | None
        Required for OpenAI; ignored for Ollama.

    Returns
    -------
    Embeddings instance (OpenAIEmbeddings or OllamaEmbeddings)
    """
    provider = (provider or "ollama").strip().lower()

    if provider == "openai":
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "OPENAI_API_KEY is required for OpenAI embeddings. "
                "Set it in your .env file."
            )
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:
            raise ImportError(
                "langchain-openai is not installed. "
                "Run: pip install langchain-openai"
            ) from exc

        return OpenAIEmbeddings(
            model=DEFAULT_EMBEDDING_MODEL_OPENAI,
            openai_api_key=resolved_key,
        )

    if provider == "gemini":
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not resolved_key:
            raise ValueError(
                "GOOGLE_API_KEY is required for Gemini embeddings. "
                "Set it in your .env file."
            )
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
        except ImportError as exc:
            raise ImportError(
                "langchain-google-genai is not installed. "
                "Run: pip install langchain-google-genai"
            ) from exc

        return GoogleGenerativeAIEmbeddings(
            model=DEFAULT_EMBEDDING_MODEL_GEMINI,
            google_api_key=resolved_key,
        )

    # Default: Ollama
    try:
        from langchain_ollama import OllamaEmbeddings
    except ImportError as exc:
        raise ImportError(
            "langchain_ollama is not installed. "
            "Run: pip install langchain_ollama"
        ) from exc

    return OllamaEmbeddings(
        model=DEFAULT_EMBEDDING_MODEL_OLLAMA,
    )


# ── Vector store helpers ─────────────────────────────────────────────────────

def build_vectorstore(chunks: List[str], embedding_fn, collection_name: Optional[str] = None):
    """
    Build an ephemeral ChromaDB vector store from text chunks.

    Parameters
    ----------
    chunks : list[str]
        The text chunks to index.
    embedding_fn : Embeddings
        A LangChain-compatible embedding function.
    collection_name : str | None
        Optional collection name; a random one is generated if omitted.

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
        collection_name = f"protein_chunks_{uuid.uuid4().hex[:8]}"

    # Create metadata for each chunk (ChromaDB requires it)
    metadatas = [{"chunk_index": i, "length": len(c)} for i, c in enumerate(chunks)]

    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embedding_fn,
        metadatas=metadatas,
        collection_name=collection_name,
    )
    return vectorstore


def retrieve_relevant_chunks(vectorstore, query: str, top_k: int = 4) -> List[str]:
    """
    Perform similarity search on the vector store.

    Parameters
    ----------
    vectorstore : Chroma
        The ChromaDB vector store.
    query : str
        The natural-language query to search for.
    top_k : int
        Number of chunks to retrieve.

    Returns
    -------
    list[str]
        The top-k most relevant text chunks.
    """
    results = vectorstore.similarity_search(query, k=top_k)
    return [doc.page_content for doc in results]


# ── High-level orchestrator ──────────────────────────────────────────────────

def retrieve_with_embeddings(
    dom_chunks: List[str],
    query: str,
    provider: str,
    top_k: int = 4,
    api_key: Optional[str] = None,
) -> dict:
    """
    End-to-end embedding retrieval pipeline.

    1. Create an embedding function for the given provider.
    2. Build an in-memory ChromaDB vector store from dom_chunks.
    3. Retrieve the top-k most similar chunks.

    Parameters
    ----------
    dom_chunks : list[str]
        Raw text chunks from the scraped page.
    query : str
        Combined search query (protein name + fields + source).
    provider : str
        "openai" or "ollama".
    top_k : int
        Number of chunks to return.
    api_key : str | None
        OpenAI API key (read from env if not supplied).

    Returns
    -------
    dict with keys:
        "chunks"  : list[str]   — retrieved chunks
        "method"  : str         — "embedding"
        "model"   : str         — embedding model name used
        "error"   : str | None  — error message if any
    """
    if not dom_chunks:
        return {
            "chunks": [],
            "method": "embedding",
            "model": None,
            "error": "No chunks provided",
        }

    provider_lower = (provider or "ollama").strip().lower()
    if provider_lower == "openai":
        embedding_model = DEFAULT_EMBEDDING_MODEL_OPENAI
    elif provider_lower == "gemini":
        embedding_model = DEFAULT_EMBEDDING_MODEL_GEMINI
    else:
        embedding_model = DEFAULT_EMBEDDING_MODEL_OLLAMA

    try:
        embedding_fn = get_embedding_function(provider_lower, api_key)
        vectorstore = build_vectorstore(dom_chunks, embedding_fn)
        relevant_chunks = retrieve_relevant_chunks(vectorstore, query, top_k=top_k)

        return {
            "chunks": relevant_chunks,
            "method": "embedding",
            "model": embedding_model,
            "error": None,
        }

    except Exception as exc:
        logger.warning(
            "Embedding retrieval failed (%s), returning error: %s",
            provider_lower,
            exc,
        )
        return {
            "chunks": [],
            "method": "embedding",
            "model": embedding_model,
            "error": str(exc),
        }
