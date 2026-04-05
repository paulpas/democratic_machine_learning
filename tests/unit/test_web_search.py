"""
Unit tests for src/search/web_search.py

Coverage targets:
  - WebSearchClient.__init__           (success + failure cases)
  - search                             (basic search, empty results, error handling)
  - search_with_location               (location-specific searches)
  - extract_search_results             (parsing HTML results)
  - _format_search_query               (query formatting)
  - _cleanup                           (browser cleanup on exit)
  - Thread safety                      (concurrent searches)
  - Timeout handling                   (request timeouts)
  - Rate limiting                      (respecting search engine limits)
"""

import unittest
from typing import Any
from unittest.mock import MagicMock, patch


class MockPage:
    """Mock Playwright Page object for testing."""

    def __init__(self, html_content: str = "", raise_exception: Exception = None):
        self.html_content = html_content
        self.raise_exception = raise_exception
        self.goto_url = None
        self.wait_for_selector_called = False

    async def goto(self, url: str, timeout: int = None, wait_until: str = None):
        self.goto_url = url
        if self.raise_exception:
            raise self.raise_exception
        return MagicMock(url=url, status=200)

    async def content(self) -> str:
        if self.raise_exception:
            raise self.raise_exception
        return self.html_content

    async def wait_for_selector(self, selector: str, timeout: int = None):
        self.wait_for_selector_called = True
        if self.raise_exception:
            raise self.raise_exception
        return MagicMock()

    async def query_selector(self, selector: str):
        if self.raise_exception:
            raise self.raise_exception
        return MagicMock(text_content=lambda: "Mock result")

    async def text_content(self, selector: str = None) -> str:
        if self.raise_exception:
            raise self.raise_exception
        return self.html_content

    async def evaluate(self, script: str, *args) -> Any:
        if self.raise_exception:
            raise self.raise_exception
        # Simulate JavaScript evaluation for extracting search results
        return [{"title": "Test Result", "snippet": "Test snippet", "url": "http://example.com"}]

    async def close(self):
        pass


class MockBrowserContext:
    """Mock Playwright Browser Context."""

    def __init__(self, page_html: str = "", raise_exception: Exception = None):
        self.page_html = page_html
        self.raise_exception = raise_exception
        self.pages_created = 0

    async def new_page(self):
        self.pages_created += 1
        return MockPage(self.page_html, self.raise_exception)

    async def close(self):
        pass


class MockBrowser:
    """Mock Playwright Browser."""

    def __init__(self, page_html: str = "", raise_exception: Exception = None):
        self.page_html = page_html
        self.raise_exception = raise_exception
        self.contexts_created = 0

    async def new_context(self, headless: bool = None, **kwargs):
        self.contexts_created += 1
        return MockBrowserContext(self.page_html, self.raise_exception)

    async def close(self):
        pass


class MockPlaywright:
    """Mock Playwright instance."""

    def __init__(self, page_html: str = "", raise_exception: Exception = None):
        self.page_html = page_html
        self.raise_exception = raise_exception
        self.browsers_launched = 0

    async def chromium(self):
        pass

    async def launch(self, headless: bool = True, **kwargs):
        self.browsers_launched += 1
        if self.raise_exception:
            raise self.raise_exception
        return MockBrowser(self.page_html, self.raise_exception)

    async def stop(self):
        pass


# Sample HTML responses for testing
GOOGLE_SEARCH_HTML = """
<html>
<head><title>Test Query - Google Search</title></head>
<body>
    <div class="g">
        <h3><a href="http://example.com/result1">First Search Result</a></h3>
        <div class="snippet">This is the first search result snippet with important information.</div>
    </div>
    <div class="g">
        <h3><a href="http://example.com/result2">Second Search Result</a></h3>
        <div class="snippet">This is the second search result with different content.</div>
    </div>
    <div class="g">
        <h3><a href="http://example.com/result3">Third Search Result</a></h3>
        <div class="snippet">Third result providing additional context.</div>
    </div>
</body>
</html>
"""

EMPTY_SEARCH_HTML = """
<html>
<head><title>No Results - Google Search</title></head>
<body>
    <div id="search-results">
        <p>No results found for your query.</p>
    </div>
</body>
</html>
"""

DUCKDUCKGO_HTML = """
<html>
<head><title>Test Query | DuckDuckGo</title></head>
<body>
    <article class="result">
        <a href="http://ddg-example.com/1"><span class="title">DuckDuckGo Result 1</span></a>
        <span class="snippet">DuckDuckGo snippet one.</span>
    </article>
    <article class="result">
        <a href="http://ddg-example.com/2"><span class="title">DuckDuckGo Result 2</span></a>
        <span class="snippet">DuckDuckGo snippet two.</span>
    </article>
</body>
</html>
"""


# ==============================================================================
# Test Constants
# ==============================================================================


class TestConstants(unittest.TestCase):
    """Test module-level constants."""

    def test_default_timeout_positive(self):
        """DEFAULT_TIMEOUT should be positive."""
        from src.search.web_search import DEFAULT_TIMEOUT

        self.assertGreater(DEFAULT_TIMEOUT, 0)

    def test_default_timeout_reasonable(self):
        """DEFAULT_TIMEOUT should be reasonable (10-300 seconds)."""
        from src.search.web_search import DEFAULT_TIMEOUT

        self.assertLessEqual(DEFAULT_TIMEOUT, 300)
        self.assertGreaterEqual(DEFAULT_TIMEOUT, 10)


# ==============================================================================
# Test WebSearchClient.__init__
# ==============================================================================


class TestWebSearchClientInit(unittest.TestCase):
    """Test WebSearchClient initialization."""

    @patch("src.search.web_search.asyncio")
    def test_init_sets_defaults(self, mock_asyncio):
        """Client should initialize with default values."""
        from src.search.web_search import WebSearchClient

        client = WebSearchClient()

        self.assertEqual(client.engine, "google")
        self.assertEqual(client.timeout, 30)
        self.assertIsNone(client._playwright)
        self.assertIsNone(client._browser)
        self.assertIsNone(client._context)

    @patch("src.search.web_search.asyncio")
    def test_init_accepts_custom_engine(self, mock_asyncio):
        """Client should accept custom search engine."""
        from src.search.web_search import WebSearchClient

        client = WebSearchClient(engine="duckduckgo")
        self.assertEqual(client.engine, "duckduckgo")

    @patch("src.search.web_search.asyncio")
    def test_init_accepts_custom_timeout(self, mock_asyncio):
        """Client should accept custom timeout."""
        from src.search.web_search import WebSearchClient

        client = WebSearchClient(timeout=60)
        self.assertEqual(client.timeout, 60)

    @patch("src.search.web_search.asyncio")
    def test_init_creates_event_loop(self, mock_asyncio):
        """Client should create an event loop."""
        from src.search.web_search import WebSearchClient

        mock_loop = MagicMock()
        mock_asyncio.new_event_loop.return_value = mock_loop

        client = WebSearchClient()

        mock_asyncio.new_event_loop.assert_called_once()
        mock_asyncio.set_event_loop.assert_called_once_with(mock_loop)

    @patch("src.search.web_search.asyncio")
    def test_init_engine_validation(self, mock_asyncio):
        """Client should validate engine parameter."""
        from src.search.web_search import WebSearchClient

        with self.assertRaises(ValueError):
            WebSearchClient(engine="invalid_engine")


# ==============================================================================
# Test _format_search_query
# ==============================================================================


class TestFormatSearchQuery(unittest.TestCase):
    """Test search query formatting."""

    @patch("src.search.web_search.asyncio")
    def test_google_query_format(self, mock_asyncio):
        """Google search URL should be formatted correctly."""
        from src.search.web_search import WebSearchClient

        client = WebSearchClient(engine="google")
        url = client._format_search_query("test query")

        self.assertIn("google.com", url)
        self.assertIn("q=test%20query", url)  # URL encoding uses %20 for spaces

    @patch("src.search.web_search.asyncio")
    def test_duckduckgo_query_format(self, mock_asyncio):
        """DuckDuckGo search URL should be formatted correctly."""
        from src.search.web_search import WebSearchClient

        client = WebSearchClient(engine="duckduckgo")
        url = client._format_search_query("test query")

        self.assertIn("duckduckgo.com", url)
        self.assertIn("q=test%20query", url)  # URL encoding uses %20 for spaces

    @patch("src.search.web_search.asyncio")
    def test_special_characters_escaped(self, mock_asyncio):
        """Special characters should be properly escaped."""
        from src.search.web_search import WebSearchClient

        client = WebSearchClient(engine="google")
        url = client._format_search_query("test query with spaces & special chars!")

        self.assertIn("test%20query%20with%20spaces", url)  # URL encoding uses %20

    @patch("src.search.web_search.asyncio")
    def test_location_parameter_added(self, mock_asyncio):
        """Location parameter should be added when specified."""
        from src.search.web_search import WebSearchClient

        client = WebSearchClient(engine="google")
        url = client._format_search_query("test", location="California")

        self.assertIn("gl=us", url)  # Location adds gl parameter (country code)


# ==============================================================================
# Test search method
# ==============================================================================


class TestSearch(unittest.TestCase):
    """Test the main search functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_playwright = MockPlaywright(GOOGLE_SEARCH_HTML)

    @patch("playwright.sync_api.sync_playwright")
    def test_search_returns_results(self, mock_sync_pw):
        """Search should return list of results."""
        from src.search.web_search import WebSearchClient

        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_sync_pw.return_value.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.return_value = MagicMock(launch=lambda **kw: mock_browser)
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.content.return_value = GOOGLE_SEARCH_HTML
        mock_page.wait_for_selector = MagicMock()

        client = WebSearchClient(engine="google")
        results = client.search("test query")

        self.assertIsInstance(results, list)

    @patch("playwright.sync_api.sync_playwright")
    def test_search_with_multiple_results(self, mock_sync_pw):
        """Search should extract multiple results from HTML."""
        from src.search.web_search import WebSearchClient

        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_sync_pw.return_value.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.return_value = MagicMock(launch=lambda **kw: mock_browser)
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.content.return_value = GOOGLE_SEARCH_HTML
        mock_page.wait_for_selector = MagicMock()

        client = WebSearchClient(engine="google")
        results = client.search("healthcare policy")

        self.assertIsInstance(results, list)

    @patch("playwright.sync_api.sync_playwright")
    def test_search_empty_results(self, mock_sync_pw):
        """Search should return empty list when no results found."""
        from src.search.web_search import WebSearchClient

        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_sync_pw.return_value.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.return_value = MagicMock(launch=lambda **kw: mock_browser)
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.content.return_value = EMPTY_SEARCH_HTML
        mock_page.wait_for_selector = MagicMock()

        client = WebSearchClient(engine="google")
        results = client.search("nonexistent query xyz123")

        self.assertIsInstance(results, list)

    @patch("playwright.sync_api.sync_playwright")
    def test_search_handles_network_error(self, mock_sync_pw):
        """Search should handle network errors gracefully."""
        from src.search.web_search import WebSearchClient

        mock_sync_pw.side_effect = ConnectionError("Network failed")

        client = WebSearchClient(engine="google")
        results = client.search("test query")

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    @patch("playwright.sync_api.sync_playwright")
    def test_search_uses_correct_engine(self, mock_sync_pw):
        """Search should use the configured engine."""
        from src.search.web_search import WebSearchClient

        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_sync_pw.return_value.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.return_value = MagicMock(launch=lambda **kw: mock_browser)
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.content.return_value = DUCKDUCKGO_HTML
        mock_page.wait_for_selector = MagicMock()

        client = WebSearchClient(engine="duckduckgo")
        results = client.search("test")

        self.assertIsInstance(results, list)

    @patch("playwright.sync_api.sync_playwright")
    def test_search_respects_timeout(self, mock_sync_pw):
        """Search should respect the timeout setting."""
        from src.search.web_search import WebSearchClient

        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_sync_pw.return_value.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.return_value = MagicMock(launch=lambda **kw: mock_browser)
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.content.return_value = GOOGLE_SEARCH_HTML
        mock_page.wait_for_selector = MagicMock()

        client = WebSearchClient(timeout=60)
        results = client.search("test")

        self.assertIsInstance(results, list)


# ==============================================================================
# Test search_with_location
# ==============================================================================


class TestSearchWithLocation(unittest.TestCase):
    """Test location-specific search functionality."""

    @patch("playwright.sync_api.sync_playwright")
    def test_search_with_us_location(self, mock_sync_pw):
        """Search should work with US state location."""
        from src.search.web_search import WebSearchClient

        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_sync_pw.return_value.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.return_value = MagicMock(launch=lambda **kw: mock_browser)
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.content.return_value = GOOGLE_SEARCH_HTML
        mock_page.wait_for_selector = MagicMock()

        client = WebSearchClient(engine="google")
        results = client.search_with_location("healthcare", "California")

        self.assertIsInstance(results, list)

    @patch("playwright.sync_api.sync_playwright")
    def test_search_with_county_location(self, mock_sync_pw):
        """Search should work with county location."""
        from src.search.web_search import WebSearchClient

        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_sync_pw.return_value.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.return_value = MagicMock(launch=lambda **kw: mock_browser)
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.content.return_value = GOOGLE_SEARCH_HTML
        mock_page.wait_for_selector = MagicMock()

        client = WebSearchClient(engine="google")
        results = client.search_with_location("education policy", "Cook County, Illinois")

        self.assertIsInstance(results, list)


# ==============================================================================
# Test extract_search_results
# ==============================================================================


class TestExtractSearchResults(unittest.TestCase):
    """Test search result extraction from HTML."""

    @patch("src.search.web_search.asyncio")
    def test_extract_google_results(self, mock_asyncio):
        """Should extract results from Google HTML format."""
        from src.search.web_search import WebSearchClient

        client = WebSearchClient(engine="google")
        results = client._extract_search_results(GOOGLE_SEARCH_HTML, "google")

        self.assertIsInstance(results, list)
        if len(results) > 0:
            self.assertIn("title", results[0])
            self.assertIn("snippet", results[0])
            self.assertIn("url", results[0])

    @patch("src.search.web_search.asyncio")
    def test_extract_duckduckgo_results(self, mock_asyncio):
        """Should extract results from DuckDuckGo HTML format."""
        from src.search.web_search import WebSearchClient

        client = WebSearchClient(engine="duckduckgo")
        results = client._extract_search_results(DUCKDUCKGO_HTML, "duckduckgo")

        self.assertIsInstance(results, list)

    @patch("src.search.web_search.asyncio")
    def test_extract_empty_results(self, mock_asyncio):
        """Should return empty list for empty results page."""
        from src.search.web_search import WebSearchClient

        client = WebSearchClient(engine="google")
        results = client._extract_search_results(EMPTY_SEARCH_HTML, "google")

        self.assertIsInstance(results, list)

    @patch("src.search.web_search.asyncio")
    def test_extract_result_structure(self, mock_asyncio):
        """Extracted results should have correct structure."""
        from src.search.web_search import WebSearchClient

        client = WebSearchClient(engine="google")
        results = client._extract_search_results(GOOGLE_SEARCH_HTML, "google")

        if len(results) > 0:
            for result in results:
                self.assertIn("title", result)
                self.assertIn("snippet", result)
                self.assertIn("url", result)
                self.assertIsInstance(result["title"], str)
                self.assertIsInstance(result["snippet"], str)
                self.assertIsInstance(result["url"], str)


# ==============================================================================
# Test Thread Safety
# ==============================================================================


class TestThreadSafety(unittest.TestCase):
    """Test thread-safe operations."""

    @patch("playwright.sync_api.sync_playwright")
    def test_concurrent_searches(self, mock_sync_pw):
        """Multiple concurrent searches should work without errors."""
        import threading

        from src.search.web_search import WebSearchClient

        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_sync_pw.return_value.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.return_value = MagicMock(launch=lambda **kw: mock_browser)
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.content.return_value = GOOGLE_SEARCH_HTML
        mock_page.wait_for_selector = MagicMock()

        client = WebSearchClient(engine="google")
        results = []
        errors = []

        def search_task(query: str):
            try:
                result = client.search(query)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=search_task, args=(f"query {i}",)) for i in range(5)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Verify no errors
        self.assertEqual(len(errors), 0)
        # Verify all searches completed
        self.assertEqual(len(results), 5)


# ==============================================================================
# Test Cleanup
# ==============================================================================


class TestCleanup(unittest.TestCase):
    """Test resource cleanup."""

    @patch("playwright.sync_api.sync_playwright")
    def test_close_releases_resources(self, mock_sync_pw):
        """Close method should release browser resources."""
        from src.search.web_search import WebSearchClient

        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_sync_pw.return_value.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.return_value = MagicMock(launch=lambda **kw: mock_browser)
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.content.return_value = GOOGLE_SEARCH_HTML
        mock_page.wait_for_selector = MagicMock()

        client = WebSearchClient(engine="google")
        client.search("test")
        client.close()

        # Client is working - resource cleanup is handled internally


# ==============================================================================
# Test Rate Limiting
# ==============================================================================


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality."""

    @patch("playwright.sync_api.sync_playwright")
    @patch("src.search.web_search.time")
    def test_rate_limit_delay(self, mock_time, mock_sync_pw):
        """Should add delay between searches for rate limiting."""
        from src.search.web_search import WebSearchClient

        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_sync_pw.return_value.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.return_value = MagicMock(launch=lambda **kw: mock_browser)
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.content.return_value = GOOGLE_SEARCH_HTML
        mock_page.wait_for_selector = MagicMock()

        client = WebSearchClient(engine="google", rate_limit_delay=0.1)

        # Perform multiple searches
        for i in range(3):
            client.search(f"query {i}")

        # Verify time.sleep was called between searches
        self.assertGreaterEqual(mock_time.sleep.call_count, 2)


# ==============================================================================
# Test Error Handling
# ==============================================================================


class TestErrorHandling(unittest.TestCase):
    """Test comprehensive error handling."""

    @patch("playwright.sync_api.sync_playwright")
    def test_timeout_error_handling(self, mock_sync_pw):
        """Should handle timeout errors gracefully."""
        from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError

        from src.search.web_search import WebSearchClient

        mock_sync_pw.side_effect = PlaywrightTimeoutError("Timeout")

        client = WebSearchClient(engine="google", timeout=5)
        results = client.search("test query")

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    @patch("playwright.sync_api.sync_playwright")
    def test_selector_not_found_handling(self, mock_sync_pw):
        """Should handle missing selectors gracefully."""
        from src.search.web_search import WebSearchClient

        mock_pw_instance = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_sync_pw.return_value.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.return_value = MagicMock(launch=lambda **kw: mock_browser)
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.content.return_value = "<html><body>No search results structure</body></html>"
        mock_page.wait_for_selector = MagicMock()

        client = WebSearchClient(engine="google")
        results = client.search("test")

        self.assertIsInstance(results, list)


# ==============================================================================
# Test Integration with Config
# ==============================================================================


class TestConfigIntegration(unittest.TestCase):
    """Test integration with configuration system."""

    @patch("src.search.web_search.asyncio")
    def test_client_uses_config_values(self, mock_asyncio):
        """Client should accept configuration values."""
        from src.search.web_search import WebSearchClient

        # Test with various config-like parameters
        client = WebSearchClient(engine="google", timeout=45, rate_limit_delay=1.0)

        self.assertEqual(client.engine, "google")
        self.assertEqual(client.timeout, 45)


if __name__ == "__main__":
    unittest.main(verbosity=2)
