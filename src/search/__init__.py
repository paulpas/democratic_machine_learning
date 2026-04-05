"""Search module for web-based information retrieval."""

from src.search.web_search import (
    DEFAULT_MAX_RESULTS,
    DEFAULT_TIMEOUT,
    SUPPORTED_ENGINES,
    WebSearchClient,
)

__all__ = [
    "WebSearchClient",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RESULTS",
    "SUPPORTED_ENGINES",
]
