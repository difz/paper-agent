"""Tests for Discord-specific tools."""
import pytest
from agent.tools_discord import (
    retrieve_passages_for_user,
    summarize_with_citations_for_user,
    create_user_tools
)


def test_retrieve_passages_no_index():
    """Test retrieval when user has no PDFs indexed."""
    user_id = "test_user_no_pdfs"

    result = retrieve_passages_for_user(user_id, "test query")

    assert isinstance(result, str)
    assert "No PDFs indexed" in result or "upload" in result.lower()


def test_summarize_no_index():
    """Test summarization when user has no PDFs indexed."""
    user_id = "test_user_no_pdfs_2"

    result = summarize_with_citations_for_user(user_id, "test question")

    assert isinstance(result, str)
    assert "No PDFs indexed" in result or "upload" in result.lower()


def test_create_user_tools():
    """Test that user tools are created correctly."""
    user_id = "test_user_tools"

    tools = create_user_tools(user_id)

    assert len(tools) == 3
    assert tools[0].name == "retrieve"
    assert tools[1].name == "summarize"
    assert tools[2].name == "search_papers"


def test_user_tools_have_descriptions():
    """Test that tools have proper descriptions."""
    user_id = "test_user_desc"

    tools = create_user_tools(user_id)

    for tool in tools:
        assert hasattr(tool, "description")
        assert len(tool.description) > 0
        assert isinstance(tool.description, str)


def test_user_tools_are_callable():
    """Test that user tools can be called."""
    user_id = "test_user_callable"

    tools = create_user_tools(user_id)

    # Test retrieve tool
    result = tools[0].run("test query")
    assert isinstance(result, str)

    # Test summarize tool
    result = tools[1].run("test question")
    assert isinstance(result, str)

    # Test search tool
    result = tools[2].run("machine learning")
    assert isinstance(result, str)
