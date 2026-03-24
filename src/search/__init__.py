"""Search module for web-based information retrieval."""

from src.search.web_search import (
    WebSearchClient,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RESULTS,
    SUPPORTED_ENGINES,
)

__all__ = [
    "WebSearchClient",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RESULTS",
    "SUPPORTED_ENGINES",
]
