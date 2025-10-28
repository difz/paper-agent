# Paper-Agent Test Suite

Comprehensive test suite for the paper-agent project with 49 test cases covering unit tests, functional tests, and integration tests.

## Test Structure

### Test Files

1. **test_pdf_metadata.py** (13 test cases)
   - PDF metadata extraction
   - Author name parsing (single, multiple, CamelCase)
   - Year and DOI extraction
   - Real PDF testing

2. **test_citation_formatter.py** (16 test cases)
   - Citation formatting in multiple styles (IEEE, APA, MLA, Chicago, BibTeX)
   - Inline vs full citations
   - Edge cases (missing DOI, no authors, no page)

3. **test_search_tools.py** (9 test cases)
   - Semantic Scholar search (public API)
   - arXiv search
   - Multi-source search
   - Integration with external APIs

4. **test_integration.py** (6 test cases)
   - End-to-end workflows
   - PDF → Metadata → Citation
   - Search → Citation
   - Module integration
   - Settings configuration

5. **conftest.py**
   - Shared fixtures
   - Test configuration
   - Automatic test markers

## Running Tests

### Using the Test Runner Script (Recommended)

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run with verbose output
python run_tests.py --verbose

# Show print statements from tests
python run_tests.py --show-output

# Run specific test file
python run_tests.py test_citation_formatter.py

# Combine options
python run_tests.py -v -s --integration
```

### Using Pytest Directly

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_pdf_metadata.py

# Run with verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Run only integration tests
pytest tests/ -m integration

# Run specific test by name
pytest tests/test_citation_formatter.py::TestCitationFormatter::test_ieee_full_citation

# Run with coverage (requires pytest-cov)
pytest tests/ --cov=agent --cov-report=html
```

## Test Categories

### Unit Tests
Fast tests that don't require external resources:
- `test_pdf_metadata.py` - PDF parsing and metadata extraction
- `test_citation_formatter.py` - Citation formatting logic

### Integration Tests
Tests that may make external API calls or require PDFs:
- `test_search_tools.py` - Live API calls to Semantic Scholar and arXiv
- `test_integration.py` - End-to-end workflows

### Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.integration` - Integration tests (may be slow or require network)
- `@pytest.mark.skipif` - Conditional skip based on available resources
- `@pytest.mark.requires_api` - Requires external API access
- `@pytest.mark.requires_pdfs` - Requires PDF files in corpus

## Test Configuration

### pytest.ini
Main pytest configuration:
- Test discovery patterns
- Marker definitions
- Logging configuration
- Output options

### conftest.py
Shared test fixtures:
- `sample_bibliographic_metadata` - Sample citation data
- `single_author_metadata` - Single author citation
- `no_author_metadata` - Anonymous paper
- `project_root` - Project directory path
- `mock_settings` - Mock environment settings

## Expected Test Results

### Successful Tests
All tests should pass if:
- Dependencies are installed
- PDF files are available in `store/users/*/pdfs/` (for PDF tests)
- Internet connection available (for integration tests)

### Skipped Tests
Some tests may be skipped if:
- No PDFs available for testing
- External APIs are rate limited (Semantic Scholar)
- Missing API credentials (Google Scholar)

### Test Output Example

```
tests/test_pdf_metadata.py::TestPDFMetadataExtractor::test_extractor_initialization PASSED
tests/test_pdf_metadata.py::TestPDFMetadataExtractor::test_parse_authors_single PASSED
tests/test_citation_formatter.py::TestCitationFormatter::test_ieee_full_citation PASSED
...
================ 49 passed, 2 skipped in 15.42s =================
```

## Logging

All tests include detailed logging:
- Test number and description
- Step-by-step execution
- Results and assertions
- Success/failure indicators (✓/✗)

Example log output:
```
2024-01-15 10:30:45 - test_citation_formatter - INFO - TEST 6: Testing full IEEE citation
2024-01-15 10:30:45 - test_citation_formatter - INFO -   ✓ IEEE citation: J. Smith, J. Doe, and B. Johnson, "Machine Learning...
2024-01-15 10:30:45 - test_citation_formatter - INFO - ✓ Complete workflow successful!
```

## Troubleshooting

### Tests Fail Due to Missing Dependencies
```bash
pip install pytest
# Or install all requirements
pip install -r requirements.txt
```

### Integration Tests Fail
- Check internet connection
- Semantic Scholar may rate limit (429 errors) - this is expected
- Some APIs require environment variables (GOOGLE_API_KEY, etc.)

### PDF Tests Skipped
Upload PDF files to `store/users/{user_id}/pdfs/` or `corpus/` directory

### Import Errors
Ensure you're in the project root directory and the agent package is importable:
```bash
cd /home/rakuro/Documents/paper-agent
python -m pytest tests/
```

## Adding New Tests

### Test File Template
```python
import pytest
import logging

log = logging.getLogger("test_module")

class TestFeature:
    @pytest.fixture
    def setup_data(self):
        return {"key": "value"}

    def test_something(self, setup_data):
        log.info("TEST 1: Testing something")
        assert setup_data["key"] == "value"
        log.info("✓ Test passed")
```

### Integration Test
```python
@pytest.mark.integration
def test_external_api(self):
    log.info("TEST: Testing external API")
    result = call_external_api()
    assert result is not None
```

## Continuous Integration

To run tests in CI/CD:
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --tb=short
```

## Test Coverage

To generate coverage report:
```bash
pip install pytest-cov
pytest tests/ --cov=agent --cov-report=html
# Open htmlcov/index.html in browser
```

## Contact

For test-related issues, check:
1. Test logs in console output
2. pytest.ini configuration
3. conftest.py fixtures
4. Individual test file documentation
