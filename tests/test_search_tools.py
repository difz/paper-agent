"""
Functional tests for academic paper search tools.
Tests Semantic Scholar and arXiv search APIs.
"""
import pytest
import logging
from agent.search_tools import (
    SemanticScholarSearch,
    ArXivSearch,
    GoogleScholarSearch,
    search_papers
)

# Set up logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("test_search_tools")


class TestSemanticScholarSearch:
    """Test suite for Semantic Scholar search."""

    @pytest.fixture
    def searcher(self):
        """Create SemanticScholarSearch instance."""
        return SemanticScholarSearch()

    def test_searcher_initialization(self, searcher):
        """Test 1: Verify searcher initializes without API key."""
        log.info("TEST 1: Testing Semantic Scholar initialization")
        assert searcher is not None
        assert hasattr(searcher, 'headers')
        assert 'User-Agent' in searcher.headers
        log.info("✓ Semantic Scholar searcher initialized successfully")

    @pytest.mark.integration
    def test_semantic_scholar_search(self, searcher):
        """Test 2: Perform actual Semantic Scholar search."""
        log.info("TEST 2: Testing Semantic Scholar search (live API call)")

        query = "machine learning"
        result = searcher.search(query, limit=2)

        assert isinstance(result, str)
        assert len(result) > 0

        # Check if it contains expected elements (or error message)
        if "Error" not in result and "429" not in result:
            # Successful search
            assert "**" in result  # Markdown formatting
            assert any(word in result for word in ['Authors', 'Year', 'URL'])
            log.info(f"✓ Search returned {len(result)} characters")
            log.info(f"  Preview: {result[:200]}...")
        else:
            # Rate limited or error
            log.warning(f"⚠ Search returned error (likely rate limit): {result[:100]}")
            pytest.skip("Semantic Scholar rate limit or error")

    def test_semantic_scholar_no_results(self, searcher):
        """Test 3: Handle search with no results."""
        log.info("TEST 3: Testing Semantic Scholar search with unlikely query")

        # Use a very specific nonsense query unlikely to return results
        query = "xyzabc123nonexistentpaper999"
        result = searcher.search(query, limit=2)

        assert isinstance(result, str)
        # Should either say "No papers found" or return error
        assert len(result) > 0
        log.info(f"✓ Handled no-results case: {result[:80]}...")


class TestArXivSearch:
    """Test suite for arXiv search."""

    @pytest.fixture
    def searcher(self):
        """Create ArXivSearch instance."""
        return ArXivSearch()

    def test_searcher_initialization(self, searcher):
        """Test 4: Verify arXiv searcher initializes."""
        log.info("TEST 4: Testing arXiv initialization")
        assert searcher is not None
        assert searcher.BASE_URL == "http://export.arxiv.org/api/query"
        log.info("✓ arXiv searcher initialized successfully")

    @pytest.mark.integration
    def test_arxiv_search(self, searcher):
        """Test 5: Perform actual arXiv search."""
        log.info("TEST 5: Testing arXiv search (live API call)")

        query = "neural networks"
        result = searcher.search(query, limit=2)

        assert isinstance(result, str)
        assert len(result) > 0

        # arXiv should return results reliably
        if "Error" not in result:
            assert "**" in result  # Markdown formatting
            assert any(word in result for word in ['Authors', 'Published', 'PDF', 'URL'])
            log.info(f"✓ arXiv search returned {len(result)} characters")
            log.info(f"  Preview: {result[:200]}...")
        else:
            log.error(f"✗ arXiv search failed: {result}")
            pytest.fail("arXiv search should not fail")

    def test_arxiv_specific_topic(self, searcher):
        """Test 6: Search arXiv for specific CS topic."""
        log.info("TEST 6: Testing arXiv search for specific topic")

        query = "transformer attention"
        result = searcher.search(query, limit=1)

        assert isinstance(result, str)
        assert len(result) > 0
        log.info(f"✓ Topic-specific search completed: {len(result)} chars")


class TestSearchPapersFunction:
    """Test suite for the main search_papers function."""

    def test_search_papers_function_exists(self):
        """Test 7: Verify search_papers function exists."""
        log.info("TEST 7: Testing search_papers function existence")
        assert callable(search_papers)
        log.info("✓ search_papers function is callable")

    @pytest.mark.integration
    def test_search_papers_single_source(self):
        """Test 8: Search with single source (arXiv)."""
        log.info("TEST 8: Testing search_papers with single source")

        result = search_papers("deep learning", sources=['arxiv'])

        assert isinstance(result, str)
        assert "ARXIV" in result.upper()
        assert len(result) > 100
        log.info(f"✓ Single source search completed: {len(result)} characters")

    @pytest.mark.integration
    def test_search_papers_multiple_sources(self):
        """Test 9: Search with multiple sources."""
        log.info("TEST 9: Testing search_papers with multiple sources")

        result = search_papers("artificial intelligence", sources=['semantic_scholar', 'arxiv'])

        assert isinstance(result, str)

        # Should have both sections (unless rate limited)
        if "Error" not in result or "ARXIV" in result:
            # At least arXiv should work
            assert len(result) > 100
            log.info(f"✓ Multi-source search completed: {len(result)} characters")

            # Count how many sources returned results
            sources_found = []
            if "SEMANTIC SCHOLAR" in result:
                sources_found.append("Semantic Scholar")
            if "ARXIV" in result:
                sources_found.append("arXiv")

            log.info(f"  Sources that returned results: {', '.join(sources_found)}")
        else:
            log.warning("⚠ Some sources may be rate limited")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
