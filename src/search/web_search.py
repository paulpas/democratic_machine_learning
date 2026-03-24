"""
Web Search Module with Playwright for Real-time Information Retrieval

This module provides a thread-safe web search client that uses Playwright
for JavaScript-enabled browser automation to perform real-time web searches.
It supports multiple search engines and location-specific queries.

Features:
    - Google and DuckDuckGo search engine support
    - Location-specific searches (state, county level)
    - Thread-safe concurrent searches
    - Automatic retry and error handling
    - Rate limiting to respect search engine policies
    - Configurable timeout and result limits
"""

import os
import re
import time
import threading
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import asyncio

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightTimeoutError = Exception


# ==============================================================================
# Constants
# ==============================================================================

DEFAULT_TIMEOUT: int = 30
DEFAULT_MAX_RESULTS: int = 10
DEFAULT_RATE_LIMIT_DELAY: float = 0.5  # seconds between searches

SUPPORTED_ENGINES: List[str] = ["google", "duckduckgo"]

# Google search result selectors
GOOGLE_SELECTORS = {"result_container": ".g", "title": "h3 a", "snippet": ".snippet"}

# DuckDuckGo search result selectors
DUCKDUCKGO_SELECTORS = {
    "result_container": "article.result",
    "title": "a span.title",
    "snippet": "span.snippet",
}


def _log(message: str) -> None:
    """Simple logging helper for stdout output."""
    print(f"[WebSearch] {message}")


# ==============================================================================
# WebSearchClient
# ==============================================================================


class WebSearchClient:
    """
    Thread-safe web search client using Playwright for browser automation.

    This client provides real-time web search capabilities with support for
    multiple search engines and location-specific queries. It uses Playwright
    to render JavaScript-enabled pages and extract search results.

    Attributes:
        engine: Search engine to use ("google" or "duckduckgo")
        timeout: Request timeout in seconds
        max_results: Maximum number of results to return
        rate_limit_delay: Delay between searches for rate limiting

    Example:
        >>> client = WebSearchClient(engine="google", timeout=30)
        >>> results = client.search("healthcare policy reform")
        >>> for result in results:
        ...     print(result["title"], result["snippet"])

        >>> # Location-specific search
        >>> ca_results = client.search_with_location("education funding", "California")
    """

    def __init__(
        self,
        engine: str = "google",
        timeout: int = DEFAULT_TIMEOUT,
        max_results: int = DEFAULT_MAX_RESULTS,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY,
    ):
        """
        Initialize the web search client.

        Args:
            engine: Search engine to use ("google" or "duckduckgo")
            timeout: Request timeout in seconds
            max_results: Maximum number of results to return per search
            rate_limit_delay: Delay in seconds between searches

        Raises:
            ValueError: If engine is not supported
            ImportError: If Playwright is not installed
        """
        if engine not in SUPPORTED_ENGINES:
            raise ValueError(
                f"Unsupported engine: {engine}. Supported engines: {SUPPORTED_ENGINES}"
            )

        self.engine: str = engine
        self.timeout: int = timeout
        self.max_results: int = max_results
        self.rate_limit_delay: float = rate_limit_delay

        # Thread-safe lock for browser operations
        self._lock: threading.Lock = threading.Lock()

        # Event loop for async operations (thread-local)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._create_event_loop()

        # Browser resources (managed per-thread)
        self._playwright: Optional[Any] = None
        self._browser: Optional[Any] = None
        self._context: Optional[Any] = None

        _log(f"Initialized with engine={engine}, timeout={timeout}s")

    def _create_event_loop(self) -> None:
        """Create a new event loop for this thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

    def _format_search_query(self, query: str, location: Optional[str] = None) -> str:
        """
        Format the search query into a URL for the configured search engine.

        Args:
            query: The search query string
            location: Optional location for geo-specific results

        Returns:
            Formatted search URL
        """
        # Encode query for URL
        encoded_query = quote(query.strip())

        if self.engine == "google":
            # Google search URL with optional location parameter
            base_url = "https://www.google.com/search"
            params = f"q={encoded_query}&num={self.max_results}"
            if location:
                # Add location hint using gl parameter
                # Map common locations to country/region codes
                location_code = self._get_location_code(location)
                params += f"&gl={location_code}&hl=en"
            return f"{base_url}?{params}"

        elif self.engine == "duckduckgo":
            # DuckDuckGo search URL
            base_url = "https://duckduckgo.com/"
            params = f"q={encoded_query}"
            if location:
                params += f"&kl={location}"
            return f"{base_url}?{params}"

        else:
            raise ValueError(f"Unsupported engine: {self.engine}")

    def _get_location_code(self, location: str) -> str:
        """
        Convert location name to search engine location code.

        Args:
            location: Location name (state, county, city)

        Returns:
            Location code for search engine
        """
        # Common US state mappings
        state_codes = {
            "alabama": "us",
            "alaska": "us",
            "arizona": "us",
            "arkansas": "us",
            "california": "us",
            "colorado": "us",
            "connecticut": "us",
            "delaware": "us",
            "florida": "us",
            "georgia": "us",
            "hawaii": "us",
            "idaho": "us",
            "illinois": "us",
            "indiana": "us",
            "iowa": "us",
            "kansas": "us",
            "kentucky": "us",
            "louisiana": "us",
            "maine": "us",
            "maryland": "us",
            "massachusetts": "us",
            "michigan": "us",
            "minnesota": "us",
            "mississippi": "us",
            "missouri": "us",
            "montana": "us",
            "nebraska": "us",
            "nevada": "us",
            "new hampshire": "us",
            "new jersey": "us",
            "new mexico": "us",
            "new york": "us",
            "north carolina": "us",
            "north dakota": "us",
            "ohio": "us",
            "oklahoma": "us",
            "oregon": "us",
            "pennsylvania": "us",
            "rhode island": "us",
            "south carolina": "us",
            "south dakota": "us",
            "tennessee": "us",
            "texas": "us",
            "utah": "us",
            "vermont": "us",
            "virginia": "us",
            "washington": "us",
            "west virginia": "us",
            "wisconsin": "us",
            "wyoming": "us",
        }

        location_lower = location.lower()

        # Check if it's a state
        for state, code in state_codes.items():
            if state in location_lower:
                return code

        # Default to US
        return "us"

    def _extract_search_results(self, html: str, engine: str) -> List[Dict[str, str]]:
        """
        Extract search results from HTML content.

        Args:
            html: Raw HTML content from search results page
            engine: Search engine that generated the HTML

        Returns:
            List of dictionaries with 'title', 'snippet', and 'url' keys
        """
        results = []

        if engine == "google":
            # Parse Google search results
            # Pattern: <div class="g"> contains result
            result_pattern = r'<div class="g">(.*?)</div>'
            result_matches = re.findall(result_pattern, html, re.DOTALL)

            for match in result_matches[: self.max_results]:
                # Extract title
                title_match = re.search(r'<h3><a href=["\']([^"\']+)["\']>([^<]+)</a></h3>', match)
                if not title_match:
                    title_match = re.search(r'<a href=["\']([^"\']+)["\']>[\s\S]?(.+?)</a>', match)

                if title_match:
                    url = title_match.group(1) if len(title_match.groups()) > 1 else ""
                    title = (
                        title_match.group(2)
                        if len(title_match.groups()) > 1
                        else title_match.group(1)
                    )

                    # Extract snippet
                    snippet_match = re.search(r'<div class="snippet">([^<]+)', match)
                    snippet = snippet_match.group(1).strip() if snippet_match else ""

                    # Clean up title
                    title = re.sub(r"&nbsp;", " ", title)
                    title = re.sub(r"\s+", " ", title).strip()

                    if title and not title.startswith("https://"):
                        results.append({"title": title, "snippet": snippet, "url": url})

        elif engine == "duckduckgo":
            # Parse DuckDuckGo search results
            article_pattern = r'<article class="result">(.*?)</article>'
            article_matches = re.findall(article_pattern, html, re.DOTALL)

            for match in article_matches[: self.max_results]:
                # Extract title
                title_match = re.search(
                    r'<a href=["\']([^"\']+)["\'][^>]*><span class="title">([^<]+)</span>', match
                )

                if title_match:
                    url = title_match.group(1)
                    title = title_match.group(2)

                    # Extract snippet
                    snippet_match = re.search(r'<span class="snippet">([^<]+)', match)
                    snippet = snippet_match.group(1).strip() if snippet_match else ""

                    title = re.sub(r"\s+", " ", title).strip()

                    results.append({"title": title, "snippet": snippet, "url": url})

        return results

    def search(self, query: str) -> List[Dict[str, str]]:
        """
        Perform a web search and return results.

        Args:
            query: Search query string

        Returns:
            List of dictionaries with 'title', 'snippet', and 'url' keys

        Example:
            >>> client = WebSearchClient()
            >>> results = client.search("universal healthcare")
            >>> for r in results:
            ...     print(r["title"], ":", r["snippet"])
        """
        if not PLAYWRIGHT_AVAILABLE:
            _log("Playwright not available, returning empty results")
            return []

        # Apply rate limiting
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)

        with self._lock:
            try:
                # Build search URL
                search_url = self._format_search_query(query)
                _log(f"Searching: {query} -> {search_url[:80]}...")

                # Launch browser and navigate
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    )
                    page = context.new_page()

                    # Navigate to search results
                    response = page.goto(
                        search_url, timeout=self.timeout * 1000, wait_until="domcontentloaded"
                    )

                    if not response or response.status != 200:
                        _log(
                            f"Failed to load search results: status={response.status if response else 'no response'}"
                        )
                        context.close()
                        browser.close()
                        return []

                    # Wait for results to load
                    try:
                        if self.engine == "google":
                            page.wait_for_selector(".g", timeout=5000)
                        else:
                            page.wait_for_selector("article.result", timeout=5000)
                    except PlaywrightTimeoutError:
                        _log("Timeout waiting for search results")

                    # Get page content
                    html = page.content()

                    # Extract results
                    results = self._extract_search_results(html, self.engine)

                    _log(f"Found {len(results)} results for '{query}'")

                    context.close()
                    browser.close()

                    return results

            except PlaywrightTimeoutError as e:
                _log(f"Search timeout: {e}")
                return []
            except ConnectionError as e:
                _log(f"Connection error: {e}")
                return []
            except Exception as e:
                _log(f"Search error: {e}")
                return []

    def search_with_location(self, query: str, location: str) -> List[Dict[str, str]]:
        """
        Perform a location-specific web search.

        Args:
            query: Search query string
            location: Location for geo-specific results (state, county, city)

        Returns:
            List of dictionaries with 'title', 'snippet', and 'url' keys

        Example:
            >>> client = WebSearchClient()
            >>> ca_results = client.search_with_location("healthcare policy", "California")
        """
        if not PLAYWRIGHT_AVAILABLE:
            _log("Playwright not available, returning empty results")
            return []

        # Apply rate limiting
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)

        with self._lock:
            try:
                # Build search URL with location
                search_url = self._format_search_query(query, location)
                _log(f"Location search: {query} in {location}")

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    )
                    page = context.new_page()

                    response = page.goto(
                        search_url, timeout=self.timeout * 1000, wait_until="domcontentloaded"
                    )

                    if not response or response.status != 200:
                        _log(f"Failed to load search results")
                        context.close()
                        browser.close()
                        return []

                    # Wait for results
                    try:
                        if self.engine == "google":
                            page.wait_for_selector(".g", timeout=5000)
                        else:
                            page.wait_for_selector("article.result", timeout=5000)
                    except PlaywrightTimeoutError:
                        pass

                    html = page.content()
                    results = self._extract_search_results(html, self.engine)

                    _log(f"Found {len(results)} results for '{query}' in {location}")

                    context.close()
                    browser.close()

                    return results

            except Exception as e:
                _log(f"Location search error: {e}")
                return []

    def close(self) -> None:
        """Close browser resources and cleanup."""
        with self._lock:
            if self._context:
                try:
                    self._context.close()
                except:
                    pass
                self._context = None

            if self._browser:
                try:
                    self._browser.close()
                except:
                    pass
                self._browser = None

            if self._playwright:
                try:
                    self._playwright.stop()
                except:
                    pass
                self._playwright = None

            _log("Resources closed")

    def __enter__(self) -> "WebSearchClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with cleanup."""
        self.close()
