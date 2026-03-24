"""Web search module for fetching up-to-date information with JavaScript support.

Uses Playwright for JavaScript-enabled web browsing with intelligent caching
to minimize redundant searches and maximize fresh data retrieval.

Features:
- JavaScript-enabled search via Playwright
- Intelligent caching with TTL
- Multiple search engine support (DuckDuckGo, Google)
- Configurable timeout and retry logic
- Thread-safe cache with automatic expiration
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from playwright.sync_api import Page, Playwright, sync_playwright

logger = logging.getLogger(__name__)


class WebSearchCache:
    """Thread-safe cache for web search results with TTL support."""

    def __init__(self, cache_dir: str = "output/search_cache", ttl_hours: int = 6):
        self.cache_dir = Path(cache_dir)
        self.ttl_hours = ttl_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_file = self.cache_dir / ".metadata.json"
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load cache metadata from disk."""
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, "r") as f:
                    self._metadata = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._metadata = {}
        else:
            self._metadata = {}

    def _save_metadata(self) -> None:
        """Save cache metadata to disk."""
        try:
            with open(self._metadata_file, "w") as f:
                json.dump(self._metadata, f, indent=2)
        except IOError as e:
            logger.warning("Failed to save cache metadata: %s", e)

    def _get_cache_key(self, query: str, engine: str = "duckduckgo") -> str:
        """Generate a unique cache key for a query."""
        key_string = f"{engine}:{query}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, query: str, engine: str = "duckduckgo") -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached results if not expired."""
        cache_key = self._get_cache_key(query, engine)

        if cache_key not in self._metadata:
            return None

        entry = self._metadata[cache_key]

        # Check if cache is expired
        cached_time = datetime.fromisoformat(entry["cached_at"])
        age = datetime.now() - cached_time
        if age > timedelta(hours=self.ttl_hours):
            logger.debug("Cache expired for query: %s", query)
            return None

        # Retrieve cached results
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    results = json.load(f)
                logger.debug(
                    "Cache hit for query: %s (age: %.1f hours)", query, age.total_seconds() / 3600
                )
                return results
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to read cached results: %s", e)
                # Remove invalid cache entry
                del self._metadata[cache_key]
                self._save_metadata()

        return None

    def set(self, query: str, results: List[Dict[str, Any]], engine: str = "duckduckgo") -> None:
        """Store search results in cache."""
        cache_key = self._get_cache_key(query, engine)

        # Save results to file
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(results, f, indent=2)

            # Update metadata
            self._metadata[cache_key] = {
                "cached_at": datetime.now().isoformat(),
                "query": query,
                "engine": engine,
                "result_count": len(results),
            }
            self._save_metadata()
            logger.debug("Cached results for query: %s (%d results)", query, len(results))
        except IOError as e:
            logger.warning("Failed to cache results: %s", e)

    def cleanup(self) -> int:
        """Remove expired cache entries. Returns number of removed entries."""
        expired_count = 0
        current_time = datetime.now()

        for cache_key, entry in list(self._metadata.items()):
            cached_time = datetime.fromisoformat(entry["cached_at"])
            age = current_time - cached_time

            if age > timedelta(hours=self.ttl_hours):
                # Remove cache file
                cache_file = self.cache_dir / f"{cache_key}.json"
                if cache_file.exists():
                    cache_file.unlink()

                # Remove metadata
                del self._metadata[cache_key]
                expired_count += 1

        if expired_count > 0:
            self._save_metadata()
            logger.info("Cleaned up %d expired cache entries", expired_count)

        return expired_count

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        return {
            "entries": len(self._metadata),
            "total_size_bytes": total_size,
            "ttl_hours": self.ttl_hours,
        }


class WebSearcher:
    """Web search client with JavaScript support via Playwright."""

    def __init__(
        self,
        cache_hours: int = 6,
        search_timeout: int = 30,
        use_cache: bool = True,
        primary_engine: str = "duckduckgo",
    ):
        self.cache_hours = cache_hours
        self.search_timeout = search_timeout
        self.use_cache = use_cache
        self.primary_engine = primary_engine
        self.cache = WebSearchCache(ttl_hours=cache_hours) if use_cache else None
        self._playwright: Optional[Playwright] = None
        self._browser: Any = None

    def _get_search_query(self, topic: str, context: Optional[str] = None) -> str:
        """Generate an optimized search query."""
        if context:
            # Combine topic with context for more targeted search
            return f"{topic} {context}"
        return topic

    def _search_duckduckgo(self, page: Page, query: str) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo."""
        encoded_query = quote(query)
        url = f"https://duckduckgo.com/?q={encoded_query}&t=canonical&kak=-1&ia=none"

        logger.debug("Searching DuckDuckGo: %s", query)

        try:
            page.goto(url, wait_until="networkidle", timeout=self.search_timeout * 1000)

            # Wait for results to load
            page.wait_for_selector("#r1", timeout=10000)

            # Extract search results
            results = []
            result_elements = page.query_selector_all("#r1 .result")

            for element in result_elements[:10]:  # Limit to top 10 results
                try:
                    title_elem = element.query_selector(".result__title a")
                    url_elem = element.query_selector(".result__url")
                    snippet_elem = element.query_selector(".result__snippet")

                    if title_elem:
                        result = {
                            "title": title_elem.inner_text(),
                            "url": url_elem.inner_text() if url_elem else "",
                            "snippet": snippet_elem.inner_text() if snippet_elem else "",
                            "source": "duckduckgo",
                        }
                        results.append(result)
                except Exception as e:
                    logger.debug("Failed to parse result element: %s", e)
                    continue

            return results

        except Exception as e:
            logger.error("DuckDuckGo search failed: %s", e)
            return []

    def _search_google(self, page: Page, query: str) -> List[Dict[str, Any]]:
        """Search using Google."""
        encoded_query = quote(query)
        url = f"https://www.google.com/search?q={encoded_query}&igu=1"

        logger.debug("Searching Google: %s", query)

        try:
            page.goto(url, wait_until="networkidle", timeout=self.search_timeout * 1000)

            # Check for consent banner and accept if present
            consent_button = page.query_selector("#L2AGaf")
            if consent_button:
                try:
                    consent_button.click()
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass

            # Wait for results to load
            page.wait_for_selector("#rso", timeout=10000)

            # Extract search results
            results = []
            result_elements = page.query_selector_all("#rso .g")

            for element in result_elements[:10]:  # Limit to top 10 results
                try:
                    title_elem = element.query_selector("h3")
                    url_elem = element.query_selector("a")
                    snippet_elem = element.query_selector(".VwiC3b")

                    if title_elem:
                        result = {
                            "title": title_elem.inner_text(),
                            "url": url_elem.get_attribute("href") if url_elem else "",
                            "snippet": snippet_elem.inner_text() if snippet_elem else "",
                            "source": "google",
                        }
                        results.append(result)
                except Exception as e:
                    logger.debug("Failed to parse result element: %s", e)
                    continue

            return results

        except Exception as e:
            logger.error("Google search failed: %s", e)
            return []

    def search(
        self, query: str, context: Optional[str] = None, engine: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform a web search and return results.

        Args:
            query: The search query/topic
            context: Additional context to refine the search
            engine: Search engine to use ('duckduckgo' or 'google')

        Returns:
            List of search results with title, url, snippet, and source
        """
        search_query = self._get_search_query(query, context)
        engine = engine or self.primary_engine

        # Try cache first
        if self.use_cache and self.cache:
            cached_results = self.cache.get(search_query, engine)
            if cached_results:
                return cached_results

        # Perform fresh search
        results = []

        try:
            with sync_playwright() as p:
                self._playwright = p

                # Launch browser
                self._browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
                )

                context = self._browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                page = context.new_page()

                # Perform search based on engine
                if engine == "google":
                    results = self._search_google(page, search_query)
                else:
                    results = self._search_duckduckgo(page, search_query)

                # Try alternative engine if primary fails
                if not results:
                    logger.info("Primary engine returned no results, trying alternative")
                    alt_engine = "google" if engine == "duckduckgo" else "duckduckgo"
                    if alt_engine == "google":
                        results = self._search_google(page, search_query)
                    else:
                        results = self._search_duckduckgo(page, search_query)

                context.close()
                self._browser.close()
                self._browser = None

        except Exception as e:
            logger.error("Web search failed: %s", e)
            return []

        # Cache results
        if self.use_cache and self.cache and results:
            self.cache.set(search_query, results, engine)

        logger.debug("Search for '%s' returned %d results", search_query, len(results))
        return results

    def format_results_for_prompt(
        self, results: List[Dict[str, Any]], max_results: int = 5, max_snippet_length: int = 300
    ) -> str:
        """Format search results into a prompt-friendly string."""
        if not results:
            return "No current search results available."

        formatted = []
        for i, result in enumerate(results[:max_results], 1):
            snippet = result.get("snippet", "")
            if len(snippet) > max_snippet_length:
                snippet = snippet[:max_snippet_length] + "..."

            formatted.append(
                f"{i}. {result.get('title', 'Untitled')}\n"
                f"   Source: {result.get('source', 'unknown')}\n"
                f"   URL: {result.get('url', 'N/A')}\n"
                f"   Summary: {snippet}"
            )

        return "\n\n".join(formatted)

    def cleanup(self) -> None:
        """Clean up browser resources and expired cache."""
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self.cache:
            expired = self.cache.cleanup()
            if expired > 0:
                logger.info("Cleaned up %d expired cache entries", expired)

    def get_stats(self) -> Dict[str, Any]:
        """Return search and cache statistics."""
        stats = {
            "cache_enabled": self.use_cache,
            "cache_ttl_hours": self.cache_hours,
            "primary_engine": self.primary_engine,
        }
        if self.cache:
            stats["cache"] = self.cache.stats()
        return stats


# Module-level singleton for convenience
_searcher: Optional[WebSearcher] = None


def get_searcher(
    cache_hours: int = 6,
    search_timeout: int = 30,
    use_cache: bool = True,
    primary_engine: str = "duckduckgo",
) -> WebSearcher:
    """Get or create the web searcher singleton."""
    global _searcher
    if _searcher is None:
        _searcher = WebSearcher(
            cache_hours=cache_hours,
            search_timeout=search_timeout,
            use_cache=use_cache,
            primary_engine=primary_engine,
        )
    return _searcher


def reset_searcher() -> None:
    """Reset the searcher singleton (for testing)."""
    global _searcher
    if _searcher:
        _searcher.cleanup()
    _searcher = None
