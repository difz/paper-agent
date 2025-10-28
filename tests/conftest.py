"""
Shared pytest configuration and fixtures for paper-agent tests.
"""
import pytest
import logging
import os
from pathlib import Path

# Set up logging for all tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Return the test data directory."""
    test_dir = project_root / "tests" / "test_data"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture(scope="session")
def sample_pdfs_dir(project_root):
    """Return directory with sample PDFs if available."""
    # Check user store
    store_path = project_root / "store" / "users"
    if store_path.exists():
        pdf_paths = list(store_path.glob("*/pdfs/*.pdf"))
        if pdf_paths:
            return pdf_paths[0].parent

    # Check corpus directory
    corpus_path = project_root / "corpus"
    if corpus_path.exists() and list(corpus_path.glob("*.pdf")):
        return corpus_path

    return None


@pytest.fixture
def sample_bibliographic_metadata():
    """Sample bibliographic metadata for testing."""
    return {
        'authors': ['John Smith', 'Jane Doe', 'Alice Johnson'],
        'title': 'Machine Learning Applications in Research',
        'year': 2023,
        'journal': 'Journal of Artificial Intelligence',
        'doi': '10.1234/example.2023.001',
        'abstract': 'This paper discusses various machine learning applications.'
    }


@pytest.fixture
def single_author_metadata():
    """Bibliographic metadata with single author."""
    return {
        'authors': ['John Smith'],
        'title': 'Deep Learning Fundamentals',
        'year': 2024,
        'journal': 'Neural Networks Review',
        'doi': None,
        'abstract': 'An introduction to deep learning.'
    }


@pytest.fixture
def no_author_metadata():
    """Bibliographic metadata with no authors."""
    return {
        'authors': [],
        'title': 'Anonymous Research Paper',
        'year': 2023,
        'journal': None,
        'doi': None,
        'abstract': None
    }


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers",
        "requires_api: mark test as requiring external API access"
    )
    config.addinivalue_line(
        "markers",
        "requires_env: mark test as requiring environment variables"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Auto-mark tests that use search tools
        if "search" in item.nodeid.lower():
            item.add_marker(pytest.mark.requires_api)


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment before each test."""
    # Store original environment
    original_env = os.environ.copy()

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing without requiring .env file."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key_12345")
    monkeypatch.setenv("LLM_MODEL", "gemini-1.5-flash-002")
    monkeypatch.setenv("EMBED_MODEL", "text-embedding-004")
    monkeypatch.setenv("TOP_K", "6")
    monkeypatch.setenv("CHROMA_DIR", "./test_store/chroma")


def pytest_report_header(config):
    """Add custom header to test report."""
    return [
        "Paper-Agent Test Suite",
        "=" * 70,
        "Testing: PDF metadata extraction, citation formatting, search tools, and integration",
        "=" * 70
    ]


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add custom summary to test output."""
    if exitstatus == 0:
        terminalreporter.section("Test Summary")
        terminalreporter.write_line("✓ All tests passed successfully!", green=True)
    else:
        terminalreporter.section("Test Summary")
        terminalreporter.write_line("✗ Some tests failed. Review output above.", red=True)
