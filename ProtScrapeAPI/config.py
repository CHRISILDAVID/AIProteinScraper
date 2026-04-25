"""
config.py
─────────
Central configuration for ProtScrape.
Loads environment variables from .env and exposes them as module-level constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ────────────────────────────────────────────────────────────────
_ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

# ── LLM Inference ────────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")

# ── Embedding Models ─────────────────────────────────────────────────────────
EMBEDDING_MODEL_GEMINI = os.getenv("EMBEDDING_MODEL_GEMINI", "models/gemini-embedding-001")
EMBEDDING_MODEL_OPENAI = os.getenv("EMBEDDING_MODEL_OPENAI", "text-embedding-3-small")
EMBEDDING_MODEL_OLLAMA = os.getenv("EMBEDDING_MODEL_OLLAMA", "nomic-embed-text")

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_PROVIDER = "gemini"
DEFAULT_MAX_RESULTS = 5
DEFAULT_RAG_TOP_K = 6
DEFAULT_CHUNK_SIZE = 4000

# ── App Metadata ──────────────────────────────────────────────────────────────
APP_NAME = "ProtScrape"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "AI-Powered Protein Data Scraper with RAG & Source Attribution"
