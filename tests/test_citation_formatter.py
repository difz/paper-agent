"""
Unit tests for citation formatting.
Tests IEEE, APA, MLA, Chicago, and BibTeX citation styles.
"""
import pytest
import logging
from agent.citation_formatter import CitationFormatter, format_citation

# Set up logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("test_citation_formatter")


class TestCitationFormatter:
    """Test suite for citation formatting."""

    @pytest.fixture
    def sample_metadata(self):
        """Sample bibliographic metadata for testing."""
        return {
            'authors': ['John Smith', 'Jane Doe', 'Bob Johnson'],
            'title': 'Machine Learning: A Comprehensive Study',
            'year': 2023,
            'journal': 'Journal of Artificial Intelligence',
            'doi': '10.1234/example.2023.001'
        }

    @pytest.fixture
    def single_author_metadata(self):
        """Metadata with single author."""
        return {
            'authors': ['Alice Williams'],
            'title': 'Deep Learning Fundamentals',
            'year': 2024,
            'journal': 'Neural Networks Review',
            'doi': None
        }

    @pytest.fixture
    def formatter(self):
        """Create CitationFormatter instance."""
        return CitationFormatter()

    def test_formatter_initialization(self, formatter):
        """Test 1: Verify formatter initializes correctly."""
        log.info("TEST 1: Testing formatter initialization")
        assert formatter is not None
        assert isinstance(formatter, CitationFormatter)
        log.info("✓ Formatter initialized successfully")

    def test_format_authors_ieee_single(self, formatter):
        """Test 2: Format single author in IEEE style."""
        log.info("TEST 2: Testing IEEE author formatting (single author)")
        authors = ['John Smith']
        result = formatter.format_authors(authors, style='ieee')
        assert 'J. Smith' in result
        log.info(f"✓ IEEE single author: {result}")

    def test_format_authors_ieee_multiple(self, formatter):
        """Test 3: Format multiple authors in IEEE style."""
        log.info("TEST 3: Testing IEEE author formatting (multiple authors)")
        authors = ['John Smith', 'Jane Doe', 'Bob Johnson', 'Alice Williams']
        result = formatter.format_authors(authors, max_authors=3, style='ieee')
        assert 'et al.' in result
        assert 'J. Smith' in result
        log.info(f"✓ IEEE multiple authors: {result}")

    def test_format_authors_apa(self, formatter):
        """Test 4: Format authors in APA style."""
        log.info("TEST 4: Testing APA author formatting")
        authors = ['John Smith', 'Jane Doe']
        result = formatter.format_authors(authors, style='apa')
        assert 'Smith, J.' in result
        assert 'Doe, J.' in result
        assert '&' in result  # APA uses &
        log.info(f"✓ APA authors: {result}")

    def test_format_authors_mla(self, formatter):
        """Test 5: Format authors in MLA style."""
        log.info("TEST 5: Testing MLA author formatting")
        authors = ['John Smith', 'Jane Doe', 'Bob Johnson']
        result = formatter.format_authors(authors, style='mla')
        assert 'Smith, John' in result or 'et al.' in result
        log.info(f"✓ MLA authors: {result}")

    def test_ieee_full_citation(self, sample_metadata):
        """Test 6: Generate full IEEE citation."""
        log.info("TEST 6: Testing full IEEE citation")
        result = format_citation(sample_metadata, page=42, style='ieee', inline=False)

        assert 'Smith' in result
        assert '2023' in result
        assert 'Machine Learning' in result
        assert 'p. 42' in result
        assert '10.1234' in result

        log.info(f"✓ IEEE citation: {result[:100]}...")

    def test_apa_full_citation(self, sample_metadata):
        """Test 7: Generate full APA citation."""
        log.info("TEST 7: Testing full APA citation")
        result = format_citation(sample_metadata, page=42, style='apa', inline=False)

        assert '2023' in result
        assert 'Machine Learning' in result
        assert 'p. 42' in result

        log.info(f"✓ APA citation: {result[:100]}...")

    def test_mla_full_citation(self, sample_metadata):
        """Test 8: Generate full MLA citation."""
        log.info("TEST 8: Testing full MLA citation")
        result = format_citation(sample_metadata, page=42, style='mla', inline=False)

        assert 'Smith' in result
        assert '2023' in result
        assert 'Machine Learning' in result
        assert '42' in result

        log.info(f"✓ MLA citation: {result[:100]}...")

    def test_chicago_full_citation(self, sample_metadata):
        """Test 9: Generate full Chicago citation."""
        log.info("TEST 9: Testing full Chicago citation")
        result = format_citation(sample_metadata, page=42, style='chicago', inline=False)

        assert 'Smith' in result or 'et al.' in result
        assert '2023' in result
        assert 'Machine Learning' in result

        log.info(f"✓ Chicago citation: {result[:100]}...")

    def test_bibtex_citation(self, sample_metadata):
        """Test 10: Generate BibTeX citation."""
        log.info("TEST 10: Testing BibTeX citation")
        result = format_citation(sample_metadata, page=42, style='bibtex', inline=False)

        assert '@article' in result
        assert 'author = {' in result
        assert 'title = {' in result
        assert 'year = {2023}' in result
        assert 'Smith' in result

        log.info(f"✓ BibTeX entry:\n{result}")

    def test_inline_citation_ieee(self, sample_metadata):
        """Test 11: Generate inline IEEE citation."""
        log.info("TEST 11: Testing inline IEEE citation")
        result = format_citation(sample_metadata, page=42, style='ieee', inline=True)

        assert '(' in result and ')' in result
        assert 'Smith' in result
        assert '2023' in result
        assert '42' in result

        log.info(f"✓ Inline IEEE: {result}")

    def test_inline_citation_apa(self, sample_metadata):
        """Test 12: Generate inline APA citation."""
        log.info("TEST 12: Testing inline APA citation")
        result = format_citation(sample_metadata, page=42, style='apa', inline=True)

        assert '(' in result and ')' in result
        assert 'et al.' in result or 'Smith' in result
        assert '2023' in result

        log.info(f"✓ Inline APA: {result}")

    def test_inline_citation_mla(self, single_author_metadata):
        """Test 13: Generate inline MLA citation."""
        log.info("TEST 13: Testing inline MLA citation")
        result = format_citation(single_author_metadata, page=15, style='mla', inline=True)

        assert '(' in result and ')' in result
        assert 'Williams' in result
        assert '15' in result

        log.info(f"✓ Inline MLA: {result}")

    def test_citation_without_page(self, sample_metadata):
        """Test 14: Generate citation without page number."""
        log.info("TEST 14: Testing citation without page number")
        result = format_citation(sample_metadata, page=None, style='ieee', inline=True)

        assert 'Smith' in result
        assert '2023' in result
        # Should not have page reference
        assert 'p.' not in result

        log.info(f"✓ Citation without page: {result}")

    def test_citation_missing_doi(self, single_author_metadata):
        """Test 15: Handle citation without DOI."""
        log.info("TEST 15: Testing citation without DOI")
        result = format_citation(single_author_metadata, style='ieee', inline=False)

        assert 'Williams' in result
        assert '2024' in result
        # Should still work without DOI
        assert 'Deep Learning' in result

        log.info(f"✓ Citation without DOI: {result[:80]}...")

    def test_citation_empty_authors(self):
        """Test 16: Handle metadata with no authors."""
        log.info("TEST 16: Testing citation with no authors")
        metadata = {
            'authors': [],
            'title': 'Anonymous Paper',
            'year': 2023,
            'journal': None,
            'doi': None
        }

        result = format_citation(metadata, style='ieee', inline=True)

        assert 'Unknown' in result or 'Anonymous' in result
        assert '2023' in result

        log.info(f"✓ Citation with no authors: {result}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
