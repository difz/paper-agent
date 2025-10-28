"""Tests for user store manager."""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from agent.user_store_manager import UserStoreManager


@pytest.fixture
def temp_store_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def store_manager(temp_store_dir):
    """Create a UserStoreManager instance for testing."""
    return UserStoreManager(base_dir=temp_store_dir)


def test_user_dir_creation(store_manager, temp_store_dir):
    """Test that user directories are created correctly."""
    user_id = "test_user_123"

    user_dir = store_manager._get_user_dir(user_id)
    assert user_dir.exists()
    assert user_dir.is_dir()
    assert "test_user_123" in str(user_dir)


def test_pdf_dir_creation(store_manager):
    """Test PDF directory creation."""
    user_id = "test_user_456"

    pdf_dir = store_manager._get_pdf_dir(user_id)
    assert pdf_dir.exists()
    assert pdf_dir.is_dir()
    assert "pdfs" in str(pdf_dir)


def test_save_pdf(store_manager):
    """Test saving a PDF file."""
    user_id = "test_user_789"
    pdf_content = b"fake pdf content"
    filename = "test_paper.pdf"

    pdf_path = store_manager.save_pdf(user_id, pdf_content, filename)

    assert os.path.exists(pdf_path)
    with open(pdf_path, "rb") as f:
        assert f.read() == pdf_content


def test_get_user_pdfs(store_manager):
    """Test retrieving user PDF list."""
    user_id = "test_user_list"

    # Initially empty
    pdfs = store_manager.get_user_pdfs(user_id)
    assert len(pdfs) == 0

    # Save some PDFs
    store_manager.save_pdf(user_id, b"content1", "paper1.pdf")
    store_manager.save_pdf(user_id, b"content2", "paper2.pdf")

    pdfs = store_manager.get_user_pdfs(user_id)
    assert len(pdfs) == 2


def test_get_user_stats(store_manager):
    """Test user statistics."""
    user_id = "test_user_stats"

    # Empty stats
    stats = store_manager.get_user_stats(user_id)
    assert stats["pdf_count"] == 0
    assert stats["total_size"] == 0
    assert stats["has_index"] is False

    # Add a PDF
    store_manager.save_pdf(user_id, b"test content", "test.pdf")
    stats = store_manager.get_user_stats(user_id)
    assert stats["pdf_count"] == 1
    assert stats["total_size"] > 0
    assert len(stats["pdf_names"]) == 1


def test_clear_user_data(store_manager):
    """Test clearing user data."""
    user_id = "test_user_clear"

    # Add some data
    store_manager.save_pdf(user_id, b"content", "test.pdf")

    # Clear
    result = store_manager.clear_user_data(user_id)
    assert result is True

    # Verify cleared
    pdfs = store_manager.get_user_pdfs(user_id)
    assert len(pdfs) == 0

    # Clear non-existent user
    result = store_manager.clear_user_data("non_existent_user")
    assert result is False


def test_filename_sanitization(store_manager):
    """Test that filenames are sanitized."""
    user_id = "test_user_sanitize"

    # Try to save with special characters
    pdf_content = b"content"
    filename = "test/../../../etc/passwd.pdf"

    pdf_path = store_manager.save_pdf(user_id, pdf_content, filename)

    # Should be sanitized
    assert "../" not in pdf_path
    assert "etc" not in pdf_path
    assert os.path.exists(pdf_path)
