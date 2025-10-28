"""
Integration tests for the paper-agent system.
Tests end-to-end workflows and component integration.
"""
import pytest
import logging
import os
import glob
from agent.citation_formatter import format_citation
from agent.pdf_metadata import extract_pdf_metadata
from agent.search_tools import search_papers

# Set up logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("test_integration")


class TestMetadataToCitations:
    """Test integration between metadata extraction and citation formatting."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not glob.glob("store/users/*/pdfs/*.pdf"),
        reason="No PDFs available for integration testing"
    )
    def test_pdf_to_citation_workflow(self):
        """Test 1: Complete workflow from PDF to formatted citation."""
        log.info("TEST 1: Testing PDF → Metadata → Citation workflow")

        # Find a PDF
        pdfs = glob.glob("store/users/*/pdfs/*.pdf")
        if not pdfs:
            pytest.skip("No PDFs for testing")

        pdf_path = pdfs[0]
        log.info(f"  Using PDF: {os.path.basename(pdf_path)}")

        # Step 1: Extract metadata
        metadata = extract_pdf_metadata(pdf_path)
        assert metadata is not None
        log.info(f"  ✓ Extracted metadata")
        log.info(f"    Title: {metadata.get('title', 'N/A')}")
        log.info(f"    Authors: {len(metadata.get('authors', []))} found")

        # Step 2: Format as IEEE citation
        authors_list = metadata.get('authors', [])
        # Parse if string
        if isinstance(authors_list, str):
            authors_list = authors_list.split('; ')

        citation_metadata = {
            'authors': authors_list,
            'title': metadata.get('title'),
            'year': metadata.get('year'),
            'journal': metadata.get('journal'),
            'doi': metadata.get('doi')
        }

        ieee_citation = format_citation(citation_metadata, page=5, style='ieee', inline=True)
        assert isinstance(ieee_citation, str)
        assert len(ieee_citation) > 0
        log.info(f"  ✓ Generated IEEE citation: {ieee_citation}")

        # Step 3: Format as APA citation
        apa_citation = format_citation(citation_metadata, page=5, style='apa', inline=True)
        assert isinstance(apa_citation, str)
        log.info(f"  ✓ Generated APA citation: {apa_citation}")

        # Step 4: Generate full reference
        full_ref = format_citation(citation_metadata, page=5, style='ieee', inline=False)
        assert isinstance(full_ref, str)
        log.info(f"  ✓ Generated full reference: {full_ref[:100]}...")

        log.info("✓ Complete PDF-to-citation workflow successful!")


class TestSearchAndFormat:
    """Test integration between search and citation formatting."""

    @pytest.mark.integration
    def test_search_to_citation_workflow(self):
        """Test 2: Search for paper and format as citation."""
        log.info("TEST 2: Testing Search → Citation workflow")

        # Search for a paper
        log.info("  Searching arXiv...")
        results = search_papers("neural networks", sources=['arxiv'])

        assert isinstance(results, str)
        assert len(results) > 0
        log.info(f"  ✓ Search returned {len(results)} characters")

        # Verify result contains citation elements
        assert "Authors:" in results or "Published:" in results
        log.info("  ✓ Results contain citation elements")

        log.info("✓ Search-to-citation workflow successful!")


class TestModuleIntegration:
    """Test that all modules work together."""

    def test_all_modules_import(self):
        """Test 3: Verify all major modules can be imported together."""
        log.info("TEST 3: Testing all module imports")

        try:
            from agent.pdf_metadata import extract_pdf_metadata
            from agent.citation_formatter import format_citation
            from agent.search_tools import search_papers
            from agent.config import Settings
            from agent.tools_gemini import retrieve_passages, summarize_with_citations
            from agent.tools_discord import create_user_tools

            log.info("  ✓ agent.pdf_metadata")
            log.info("  ✓ agent.citation_formatter")
            log.info("  ✓ agent.search_tools")
            log.info("  ✓ agent.config")
            log.info("  ✓ agent.tools_gemini")
            log.info("  ✓ agent.tools_discord")

            log.info("✓ All modules imported successfully!")

        except ImportError as e:
            log.error(f"✗ Import failed: {e}")
            pytest.fail(f"Module import failed: {e}")

    def test_settings_configuration(self):
        """Test 4: Verify settings load correctly."""
        log.info("TEST 4: Testing settings configuration")

        from agent.config import Settings

        settings = Settings()

        assert hasattr(settings, 'llm_model')
        assert hasattr(settings, 'embed_model')
        assert hasattr(settings, 'top_k')
        assert hasattr(settings, 'chroma_dir')

        log.info(f"  LLM Model: {settings.llm_model}")
        log.info(f"  Embed Model: {settings.embed_model}")
        log.info(f"  Top K: {settings.top_k}")
        log.info(f"  Chroma Dir: {settings.chroma_dir}")

        log.info("✓ Settings loaded successfully!")


class TestCitationStyleConsistency:
    """Test citation formatting consistency across workflows."""

    def test_citation_style_consistency(self):
        """Test 5: Verify different citation styles work consistently."""
        log.info("TEST 5: Testing citation style consistency")

        metadata = {
            'authors': ['Alice Smith', 'Bob Jones'],
            'title': 'Test Paper on Neural Networks',
            'year': 2024,
            'journal': 'AI Journal',
            'doi': '10.1234/test.2024'
        }

        styles = ['ieee', 'apa', 'mla', 'chicago', 'bibtex']
        citations = {}

        for style in styles:
            citation = format_citation(metadata, page=10, style=style, inline=False)
            citations[style] = citation

            assert isinstance(citation, str)
            assert len(citation) > 0
            log.info(f"  ✓ {style.upper()}: {len(citation)} chars")

        # Verify all styles contain key elements
        for style, citation in citations.items():
            if style != 'bibtex':
                assert '2024' in citation, f"{style} missing year"

        log.info("✓ All citation styles consistent!")

    def test_inline_vs_full_citations(self):
        """Test 6: Verify inline and full citations differ appropriately."""
        log.info("TEST 6: Testing inline vs full citations")

        metadata = {
            'authors': ['John Doe'],
            'title': 'Machine Learning Basics',
            'year': 2023,
            'journal': None,
            'doi': None
        }

        inline = format_citation(metadata, page=5, style='ieee', inline=True)
        full = format_citation(metadata, page=5, style='ieee', inline=False)

        assert isinstance(inline, str)
        assert isinstance(full, str)

        # Inline should be shorter
        assert len(inline) < len(full)

        # Both should contain key elements
        assert '2023' in inline
        assert '2023' in full
        assert 'Doe' in inline
        assert 'Doe' in full

        log.info(f"  Inline ({len(inline)} chars): {inline}")
        log.info(f"  Full ({len(full)} chars): {full}")
        log.info("✓ Inline and full citations work correctly!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
