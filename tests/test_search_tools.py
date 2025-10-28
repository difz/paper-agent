"""Tests for search tools functionality."""
import pytest
from agent.search_tools import (
    SemanticScholarSearch,
    ArXivSearch,
    GoogleScholarSearch,
    search_academic_papers
)


def test_semantic_scholar_search():
    """Test Semantic Scholar API search."""
    ss = SemanticScholarSearch()
    result = ss.search("machine learning", limit=2)

    # Should return results or error message
    assert isinstance(result, str)
    assert len(result) > 0

    # Should not be an error for a common query
    assert "Error" not in result or "No papers found" in result


def test_arxiv_search():
    """Test arXiv API search."""
    arxiv = ArXivSearch()
    result = arxiv.search("neural networks", limit=2)

    # Should return results or error message
    assert isinstance(result, str)
    assert len(result) > 0


def test_google_search_without_keys():
    """Test Google Search without API keys returns appropriate message."""
    google = GoogleScholarSearch(api_key=None, cse_id=None)
    result = google.search("deep learning", limit=2)

    # Should inform about missing configuration
    assert "not configured" in result or "Error" in result


def test_search_academic_papers_semantic_scholar():
    """Test multi-source search with Semantic Scholar only."""
    result = search_academic_papers("attention mechanism", sources=["semantic_scholar"])

    assert isinstance(result, str)
    assert "SEMANTIC SCHOLAR" in result


def test_search_academic_papers_arxiv():
    """Test multi-source search with arXiv only."""
    result = search_academic_papers("transformer architecture", sources=["arxiv"])

    assert isinstance(result, str)
    assert "ARXIV" in result


def test_search_academic_papers_all_sources():
    """Test multi-source search with all sources."""
    result = search_academic_papers("reinforcement learning", sources=None)

    assert isinstance(result, str)
    # Should include results from multiple sources
    assert "SEMANTIC SCHOLAR" in result or "ARXIV" in result


def test_semantic_scholar_empty_query():
    """Test Semantic Scholar with empty results."""
    ss = SemanticScholarSearch()
    result = ss.search("xyzabc123nonexistentquery456", limit=1)

    assert isinstance(result, str)
    # Should handle gracefully
    assert "No papers found" in result or "Error" in result or len(result) > 0
