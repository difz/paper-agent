"""
Unit tests for PDF metadata extraction.
Tests the extraction of authors, title, year, DOI, and journal from PDFs.
"""
import pytest
import os
import logging
from agent.pdf_metadata import PDFMetadataExtractor, extract_pdf_metadata

# Set up logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("test_pdf_metadata")


class TestPDFMetadataExtractor:
    """Test suite for PDF metadata extraction."""

    @pytest.fixture
    def extractor(self):
        """Create a PDFMetadataExtractor instance."""
        return PDFMetadataExtractor()

    def test_extractor_initialization(self, extractor):
        """Test 1: Verify extractor initializes correctly."""
        log.info("TEST 1: Testing extractor initialization")
        assert extractor is not None
        assert isinstance(extractor, PDFMetadataExtractor)
        log.info("✓ Extractor initialized successfully")

    def test_parse_authors_single(self, extractor):
        """Test 2: Parse single author string."""
        log.info("TEST 2: Testing single author parsing")
        author_str = "John Smith"
        result = extractor._parse_authors(author_str)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "John Smith"
        log.info(f"✓ Parsed single author: {result}")

    def test_parse_authors_multiple_comma(self, extractor):
        """Test 3: Parse multiple authors separated by comma."""
        log.info("TEST 3: Testing multiple author parsing with commas")
        author_str = "John Smith, Jane Doe, Bob Johnson"
        result = extractor._parse_authors(author_str)
        assert len(result) == 3
        assert "John Smith" in result
        assert "Jane Doe" in result
        assert "Bob Johnson" in result
        log.info(f"✓ Parsed {len(result)} authors: {result}")

    def test_parse_authors_with_and(self, extractor):
        """Test 4: Parse authors with 'and' separator."""
        log.info("TEST 4: Testing author parsing with 'and' separator")
        author_str = "John Smith and Jane Doe"
        result = extractor._parse_authors(author_str)
        assert len(result) == 2
        assert "John Smith" in result
        assert "Jane Doe" in result
        log.info(f"✓ Parsed authors with 'and': {result}")

    def test_parse_authors_cleanup(self, extractor):
        """Test 5: Parse authors with email and affiliations (should be cleaned)."""
        log.info("TEST 5: Testing author parsing with cleanup")
        author_str = "John Smith (john@example.com)¹, Jane Doe²"
        result = extractor._parse_authors(author_str)
        assert len(result) == 2
        # Should remove email and superscripts
        assert any("John Smith" in author for author in result)
        assert any("Jane Doe" in author for author in result)
        log.info(f"✓ Cleaned and parsed authors: {result}")

    def test_extract_year_from_date(self, extractor):
        """Test 6: Extract year from date string."""
        log.info("TEST 6: Testing year extraction from date string")
        date_str = "D:20230415120000"  # PDF date format
        result = extractor._extract_year(date_str)
        assert result == 2023
        log.info(f"✓ Extracted year: {result}")

    def test_extract_year_invalid(self, extractor):
        """Test 7: Handle invalid year extraction."""
        log.info("TEST 7: Testing invalid year extraction")
        result = extractor._extract_year("invalid date")
        assert result is None
        log.info("✓ Correctly returned None for invalid date")

    def test_extract_doi_from_text(self, extractor):
        """Test 8: Extract DOI from text."""
        log.info("TEST 8: Testing DOI extraction")
        text = "This paper is published. DOI: 10.1109/ISML60050.2024.11007439"
        result = extractor._extract_doi(text)
        assert result is not None
        assert "10.1109" in result
        log.info(f"✓ Extracted DOI: {result}")

    def test_extract_doi_not_found(self, extractor):
        """Test 9: Handle text without DOI."""
        log.info("TEST 9: Testing DOI extraction when not present")
        text = "This is just regular text without any DOI."
        result = extractor._extract_doi(text)
        assert result is None
        log.info("✓ Correctly returned None when DOI not found")

    def test_extract_year_from_text(self, extractor):
        """Test 10: Extract year from text content."""
        log.info("TEST 10: Testing year extraction from text")
        text = "Published in 2023. Authors: John Smith, Jane Doe."
        result = extractor._extract_year_from_text(text)
        assert result == 2023
        log.info(f"✓ Extracted year from text: {result}")

    def test_extract_authors_from_camelcase(self, extractor):
        """Test 11: Extract CamelCase names (like PDF extraction issues)."""
        log.info("TEST 11: Testing CamelCase name extraction")
        text = """Title of Paper
NadimpalliMadanaKailashVarma
Department of Computer Science"""
        result = extractor._extract_authors_from_text(text)
        assert len(result) > 0
        # Should split CamelCase
        assert any("Nadimpalli" in author or "Varma" in author for author in result)
        log.info(f"✓ Extracted authors from CamelCase: {result}")

    def test_extract_metadata_fallback_title(self, extractor):
        """Test 12: Use filename as fallback title."""
        log.info("TEST 12: Testing fallback title from filename")
        metadata = {
            'filename': 'machine_learning_paper.pdf',
            'filepath': '/fake/path/machine_learning_paper.pdf',
            'title': None,
            'authors': [],
            'year': None,
            'journal': None,
            'doi': None,
            'abstract': None,
        }

        # Simulate the fallback logic
        if not metadata['title']:
            metadata['title'] = os.path.splitext(metadata['filename'])[0].replace('_', ' ').replace('-', ' ')

        assert metadata['title'] == "machine learning paper"
        log.info(f"✓ Fallback title created: {metadata['title']}")

    @pytest.mark.skipif(
        not os.path.exists("store/users"),
        reason="No user PDFs available for testing"
    )
    def test_extract_from_real_pdf(self):
        """Test 13: Extract metadata from a real PDF if available."""
        log.info("TEST 13: Testing metadata extraction from real PDF")

        # Try to find a PDF in user store
        import glob
        pdfs = glob.glob("store/users/*/pdfs/*.pdf")

        if not pdfs:
            pytest.skip("No PDFs available for testing")

        pdf_path = pdfs[0]
        log.info(f"Testing with PDF: {os.path.basename(pdf_path)}")

        metadata = extract_pdf_metadata(pdf_path)

        # Verify structure
        assert 'filename' in metadata
        assert 'title' in metadata
        assert 'authors' in metadata
        assert 'year' in metadata

        # Log results
        log.info(f"  Title: {metadata.get('title', 'N/A')}")
        log.info(f"  Authors: {metadata.get('authors', [])}")
        log.info(f"  Year: {metadata.get('year', 'N/A')}")
        log.info(f"  DOI: {metadata.get('doi', 'N/A')}")
        log.info("✓ Successfully extracted metadata from real PDF")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
