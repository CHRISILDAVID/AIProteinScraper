"""
sources — Protein database API fetchers.

Each module exposes a single fetch function that returns a SourceResult.
"""

from sources.fetcher import fetch_all_sources

__all__ = ["fetch_all_sources"]
