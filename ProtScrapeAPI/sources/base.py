"""
sources/base.py
───────────────
Shared utilities: HTTP session, throttling, and the standardised SourceResult.
"""

import time
import random
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import requests

logger = logging.getLogger(__name__)

# ── Shared HTTP session ──────────────────────────────────────────────────────

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "ProtScrape/1.0 (academic protein research tool)",
    "Accept": "application/json",
})


# ── Throttle ─────────────────────────────────────────────────────────────────

def throttle(low: float = 0.3, high: float = 0.8):
    """Small random delay to respect API rate limits."""
    time.sleep(random.uniform(low, high))


# ── Standardised result ──────────────────────────────────────────────────────

@dataclass
class SourceResult:
    """Standardised result from any protein database fetch."""
    source: str
    url: str
    entries: List[Dict[str, Any]] = field(default_factory=list)
    raw_text: str = ""
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.entries)

    @property
    def entry_count(self) -> int:
        return len(self.entries)


def make_result(
    source: str,
    url: str,
    entries: list = None,
    raw_text: str = "",
    error: Optional[str] = None,
) -> SourceResult:
    """Factory for SourceResult."""
    return SourceResult(
        source=source,
        url=url,
        entries=entries or [],
        raw_text=raw_text,
        error=error,
    )
