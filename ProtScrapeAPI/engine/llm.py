"""
engine/llm.py
─────────────
LLM factory: instantiate Gemini, OpenAI, or Ollama models.
"""

import os
import logging
from typing import Optional, Tuple

from config import GEMINI_MODEL, OPENAI_MODEL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

_MODEL_CACHE = {}


def resolve_provider(llm_provider: str) -> str:
    """Normalize provider name."""
    provider = (llm_provider or "gemini").strip().lower()
    if provider in {"openai", "openai api", "openai_api"}:
        return "openai"
    if provider in {"gemini", "google", "gemini api", "google_gemini"}:
        return "gemini"
    return "ollama"


def resolve_model_name(provider: str, llm_model: Optional[str] = None) -> str:
    """Return the model name, falling back to defaults."""
    if llm_model and llm_model.strip():
        return llm_model.strip()
    if provider == "openai":
        return OPENAI_MODEL
    if provider == "gemini":
        return GEMINI_MODEL
    return OLLAMA_MODEL


def get_llm(
    llm_provider: str,
    llm_model: Optional[str] = None,
) -> Tuple:
    """
    Instantiate and cache an LLM.

    Returns
    -------
    (llm, provider, model_name)
    """
    provider = resolve_provider(llm_provider)
    model_name = resolve_model_name(provider, llm_model)
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
                "langchain-openai is not installed. Run: pip install langchain-openai"
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
        try:
            from langchain_ollama import OllamaLLM
        except ImportError as exc:
            raise ValueError(
                "langchain_ollama is not installed. Run: pip install langchain_ollama"
            ) from exc

        llm = OllamaLLM(model=model_name)

    _MODEL_CACHE[cache_key] = llm
    return llm, provider, model_name
