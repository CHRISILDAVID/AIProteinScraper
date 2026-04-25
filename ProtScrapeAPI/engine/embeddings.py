"""
engine/embeddings.py
────────────────────
Embedding function factory for RAG retrieval.
Supports Gemini, OpenAI, and Ollama embedding models.
"""

import os
import logging
from typing import Optional

from config import (
    EMBEDDING_MODEL_GEMINI,
    EMBEDDING_MODEL_OPENAI,
    EMBEDDING_MODEL_OLLAMA,
)

logger = logging.getLogger(__name__)


def get_embedding_function(provider: str, api_key: Optional[str] = None):
    """
    Return a LangChain-compatible embedding function.

    Parameters
    ----------
    provider : str
        "gemini", "openai", or "ollama"
    api_key : str | None
        API key (resolved from env if not supplied).

    Returns
    -------
    Embeddings instance
    """
    provider = (provider or "gemini").strip().lower()

    if provider == "gemini":
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not resolved_key:
            raise ValueError(
                "GOOGLE_API_KEY is required for Gemini embeddings. Set it in .env."
            )
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
        except ImportError as exc:
            raise ImportError(
                "langchain-google-genai is not installed. "
                "Run: pip install langchain-google-genai"
            ) from exc

        return GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL_GEMINI,
            google_api_key=resolved_key,
        )

    if provider == "openai":
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "OPENAI_API_KEY is required for OpenAI embeddings. Set it in .env."
            )
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:
            raise ImportError(
                "langchain-openai is not installed. "
                "Run: pip install langchain-openai"
            ) from exc

        return OpenAIEmbeddings(
            model=EMBEDDING_MODEL_OPENAI,
            openai_api_key=resolved_key,
        )

    # Default: Ollama
    try:
        from langchain_ollama import OllamaEmbeddings
    except ImportError as exc:
        raise ImportError(
            "langchain_ollama is not installed. "
            "Run: pip install langchain_ollama"
        ) from exc

    return OllamaEmbeddings(model=EMBEDDING_MODEL_OLLAMA)


def get_embedding_model_name(provider: str) -> str:
    """Return the embedding model name for a given provider."""
    provider = (provider or "gemini").strip().lower()
    if provider == "gemini":
        return EMBEDDING_MODEL_GEMINI
    if provider == "openai":
        return EMBEDDING_MODEL_OPENAI
    return EMBEDDING_MODEL_OLLAMA
