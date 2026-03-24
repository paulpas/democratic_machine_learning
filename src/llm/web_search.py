"""Web search with multiple backends for up-to-date information.

Provides modern web search capabilities with:
- DuckDuckGo JSON API (reliable, no API key required)
- Playwright JavaScript rendering for dynamic content
- Multiple browser types (chromium, firefox, webkit)
- Network idle waiting and scroll support
- Caching to avoid redundant searches
- Fallback mechanisms for reliability
"""

import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import get_config

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Cache management
# ──────────────────────────────────────────────────────────────────────────────


def _get_cache_dir() -> Path:
    """Get cache directory for web search results."""
    cache_dir = Path(os.environ.get("WEB_SEARCH_CACHE_DIR", ""))
    if not cache_dir:
        cache_dir = Path(__file__).resolve().parents[2] / "cache" / "web_search"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_cache_key(query: str) -> str:
    """Generate cache key for a search query."""
    return hashlib.md5(query.encode("utf-8")).hexdigest()


def _load_cache(cache_dir: Path, key: str) -> Optional[Dict[str, Any]]:
    """Load cached results if fresh enough."""
    cache_file = cache_dir / f"{key}.json"
    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        cache_hours = get_config().web_search.cache_hours
        created_at = datetime.fromisoformat(data["created_at"])
        age_hours = (datetime.now() - created_at).total_seconds() / 3600

        if age_hours > cache_hours:
            logger.debug(f"Cache expired for query (age: {age_hours:.1f}h)")
            return None

        return data
    except Exception as exc:
        logger.debug(f"Cache load failed: {exc}")
        return None


def _save_cache(cache_dir: Path, key: str, data: Dict[str, Any]) -> None:
    """Save search results to cache."""
    try:
        data["created_at"] = datetime.now().isoformat()
        cache_file = cache_dir / f"{key}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as exc:
        logger.debug(f"Cache save failed: {exc}")


# ──────────────────────────────────────────────────────────────────────────────
# Web Searcher with Playwright
# ──────────────────────────────────────────────────────────────────────────────


class WebSearcher:
    """Web search with JavaScript rendering using Playwright."""

    def __init__(self):
        """Initialize web searcher."""
        self._cfg = get_config().web_search
        self._cache_dir = _get_cache_dir()
        self._browser = None
        self._context = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Initialize Playwright browser if needed."""
        if self._initialized:
            return

        try:
            import asyncio

            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        try:
            from playwright.sync_api import sync_playwright

            logger.debug("Initializing Playwright browser...")
            self._playwright = sync_playwright().start()

            browser_type = self._cfg.browser_type
            if browser_type == "firefox":
                self._browser = self._playwright.firefox.launch(headless=True)
            elif browser_type == "webkit":
                self._browser = self._playwright.webkit.launch(headless=True)
            else:
                self._browser = self._playwright.chromium.launch(headless=True)

            self._context = self._browser.new_context(
                viewport={
                    "width": self._cfg.viewport_width,
                    "height": self._cfg.viewport_height,
                }
            )
            self._initialized = True
            logger.info("✅ Playwright browser initialized")

        except ImportError:
            logger.warning("Playwright not installed. Install with: pip install playwright")
            logger.warning("Then run: playwright install chromium")
            self._initialized = False
            return
        except Exception as exc:
            logger.warning(f"Playwright initialization failed: {exc}")
            self._initialized = False
            return

    def _scrape_page_with_js(self, url: str, max_attempts: int = 3) -> Optional[str]:
        """Scrape a page with JavaScript rendering and infinite scroll support."""
        if not self._initialized:
            return None

        try:
            page = self._context.new_page()

            for attempt in range(max_attempts):
                try:
                    logger.debug(f"Loading {url} (attempt {attempt + 1})")

                    # Navigate with extended timeout
                    page.goto(url, wait_until="networkidle", timeout=60000)

                    # Wait for network to be idle
                    if self._cfg.wait_for_network_idle > 0:
                        page.wait_for_timeout(int(self._cfg.wait_for_network_idle * 1000))

                    # Handle infinite scroll
                    if self._cfg.max_scroll_attempts > 0:
                        scroll_delay_ms = int(self._cfg.scroll_delay * 1000)
                        for _ in range(self._cfg.max_scroll_attempts):
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            page.wait_for_timeout(scroll_delay_ms)

                        # Final scroll to top to ensure all content loads
                        page.evaluate("window.scrollTo(0, 0)")
                        page.wait_for_timeout(1000)

                    # Get page content
                    content = page.content()

                    # Extract text content (remove scripts, styles, etc.)
                    text_content = self._extract_text_content(content)

                    page.close()
                    return text_content

                except Exception as inner_exc:
                    logger.debug(f"Attempt {attempt + 1} failed: {inner_exc}")
                    if attempt < max_attempts - 1:
                        page.close()
                        time.sleep(2)
                        continue
                    raise

        except Exception as exc:
            logger.warning(f"JavaScript scraping failed for {url}: {exc}")
            return None

    def _extract_text_content(self, html: str) -> str:
        """Extract clean text content from HTML."""

        # Remove scripts and styles
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def _search_duckduckgo_api(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo's JSON API (no API key required).

        This provides reliable structured results without needing JavaScript rendering.
        """
        import urllib.request
        import urllib.parse

        try:
            encoded_query = urllib.parse.quote(query)
            api_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_redirect=1"

            logger.debug(f"Using DuckDuckGo API: {api_url}")

            with urllib.request.urlopen(api_url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            results = []

            # Extract abstract/wikipedia content
            if data.get("AbstractText"):
                results.append(
                    {
                        "url": data.get("AbstractURL", ""),
                        "title": data.get("Heading", query),
                        "snippet": data.get("AbstractText", "")[:300],
                        "content": data.get("AbstractText", ""),
                        "relevance_score": 0.95,
                        "source": "duckduckgo_api",
                        "scraped_at": datetime.now().isoformat(),
                    }
                )

            # Extract related topics
            if data.get("RelatedTopics"):
                for topic in data["RelatedTopics"][: max_results - len(results)]:
                    if isinstance(topic, dict):
                        topic_text = topic.get("Text", "")
                        topic_url = topic.get("FirstURL", "")

                        if topic_text:
                            results.append(
                                {
                                    "url": topic_url,
                                    "title": topic.get("Text", "")[:100],
                                    "snippet": topic_text[:300],
                                    "content": topic_text,
                                    "relevance_score": 0.85,
                                    "source": "duckduckgo_api",
                                    "scraped_at": datetime.now().isoformat(),
                                }
                            )

            # If no results from API, try web search as fallback
            if not results:
                logger.info("No API results, falling back to web scraping")
                return []

            logger.info(f"✅ DuckDuckGo API returned {len(results)} results")
            return results[:max_results]

        except Exception as exc:
            logger.warning(f"DuckDuckGo API search failed: {exc}")
            return []

    def search(
        self,
        query: str,
        max_results: int = 5,
        domain: str = "general",
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """Search the web for information using JavaScript rendering.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            domain: Search domain (general, news, academic, etc.)
            use_cache: Whether to use cached results

        Returns:
            List of search results with metadata
        """
        if not self._cfg.enabled:
            return []

        # Check cache first
        if use_cache:
            cache_key = _get_cache_key(query)
            cached = _load_cache(self._cache_dir, cache_key)
            if cached:
           logger.info(f"🔍 Web search cache hit for query: {query}")
            return cached["results"][:max_results]

        # Try DuckDuckGo API first (reliable, no JavaScript needed)
        logger.info(f"🔍 Web search (API): {query}")
        results = self._search_duckduckgo_api(query, max_results)

        # If API fails or returns empty, try JavaScript fallback
        if not results and self._cfg.use_javascript:
            logger.info("API failed, trying JavaScript rendering")
            self._ensure_initialized()

            if self._initialized:
                search_url = self._build_search_url(query, domain)

                if search_url:
                    try:
                        search_results_html = self._scrape_page_with_js(search_url)

                        if search_results_html:
                            results = self._parse_search_results(
                                search_results_html, query, max_results
                            )
                    except Exception as exc:
                        logger.warning(f"JavaScript search failed: {exc}")

        # Save to cache
        if results:
            cache_key = _get_cache_key(query)
            _save_cache(
                self._cache_dir,
                cache_key,
                {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "results": results,
                },
            )

        return results

    def _build_search_url(self, query: str, domain: str) -> Optional[str]:
        """Build search URL based on configuration."""
        # Augment query with date and location context
        augmented_query = query

        if self._cfg.add_current_date:
            date_str = datetime.now().strftime("%B %d, %Y")
            augmented_query += f" {date_str}"

        if self._cfg.add_location_context and self._cfg.location_bias:
            augmented_query += f" {self._cfg.location_bias}"

        # URL encode the query
        import urllib.parse

        encoded_query = urllib.parse.quote(augmented_query)

        # Build URL based on engine
        engine = self._cfg.primary_engine.lower()

        if engine == "google":
            base_url = "https://www.google.com/search"
            params = f"q={encoded_query}"
        elif engine == "duckduckgo":
            base_url = "https://duckduckgo.com"
            params = f"q={encoded_query}"
        else:
            logger.warning(f"Unknown search engine: {engine}")
            return None

        return f"{base_url}?{params}"

    def _scrape_page_content(self, url: str) -> Optional[str]:
        """Scrape full page content from a URL with JavaScript rendering."""
        if not self._initialized:
            return None

        try:
            page = self._context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for network idle
            if self._cfg.wait_for_network_idle > 0:
                page.wait_for_timeout(int(self._cfg.wait_for_network_idle * 1000))

            # Handle infinite scroll
            if self._cfg.max_scroll_attempts > 0:
                scroll_delay_ms = int(self._cfg.scroll_delay * 1000)
                for _ in range(self._cfg.max_scroll_attempts):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(scroll_delay_ms)
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(1000)

            # Get page content and extract main text
            content = page.content()
            text_content = self._extract_text_content(content)

            page.close()
            return text_content

        except Exception as exc:
            logger.debug(f"Failed to scrape {url}: {exc}")
            return None

    def _parse_search_results(
        self, html: str, query: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Parse search results from HTML content and scrape page content."""

        results = []

        # Extract links
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
        links = re.findall(link_pattern, html)

        # Extract text snippets
        text_pattern = r">([^<]{50,500})<"
        snippets = re.findall(text_pattern, html)

        # Combine into results with full page scraping
        seen_urls = set()
        for i, link in enumerate(links[: max_results * 2]):  # Get extra for filtering
            if not link.startswith(("http://", "https://")):
                continue

            if link in seen_urls:
                continue
            seen_urls.add(link)

            # Extract domain
            domain_match = re.search(r"https?://([^/]+)", link)
            domain = domain_match.group(1) if domain_match else "unknown"

            # Get snippet (fallback to empty)
            snippet = snippets[i] if i < len(snippets) else ""

            # Scrape full page content
            logger.debug(f"Scraping page content: {link}")
            page_content = self._scrape_page_content(link)

            # Combine snippet with scraped content
            full_content = snippet
            if page_content and len(page_content) > 100:
                full_content = page_content[: self._cfg.max_snippet_length * 2]

            results.append(
                {
                    "url": link,
                    "title": domain,
                    "snippet": snippet[:300],
                    "content": full_content[:600],  # Full content for LLM
                    "relevance_score": 0.8 - (i * 0.1),  # Simple scoring
                    "source": "web_search",
                    "scraped_at": datetime.now().isoformat(),
                }
            )

            if len(results) >= max_results:
                break

        logger.debug(f"Parsed {len(results)} results from HTML")
        return results

    def close(self) -> None:
        """Clean up browser resources."""
        if hasattr(self, "_browser") and self._browser:
            self._browser.close()
        if hasattr(self, "_playwright") and self._playwright:
            self._playwright.stop()
        self._initialized = False


# ──────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ──────────────────────────────────────────────────────────────────────────────


_web_searcher: Optional[WebSearcher] = None


def get_web_searcher() -> WebSearcher:
    """Get or create the global web searcher instance."""
    global _web_searcher

    if _web_searcher is None:
        _web_searcher = WebSearcher()

    return _web_searcher


def format_search_results_for_llm(
    results: List[Dict[str, Any]],
    max_snippet_length: int = 300,
    max_results: int = 5,
) -> str:
    """Format search results for LLM consumption."""
    if not results:
        return ""

    formatted = []
    for i, result in enumerate(results[:max_results], 1):
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        snippet = result.get("snippet", "")[:max_snippet_length]

        formatted.append(f"[{i}] {title}")
        formatted.append(f"    URL: {url}")
        formatted.append(f"    {snippet}")
        formatted.append("")

    return "\n".join(formatted)


def close_web_searcher() -> None:
    """Close the global web searcher instance."""
    global _web_searcher

    if _web_searcher:
        _web_searcher.close()
        _web_searcher = None
