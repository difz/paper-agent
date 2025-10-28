#!/usr/bin/env python3
"""
Test runner script for paper-agent project.
Provides easy test execution with detailed logging and reporting.
"""
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("test_runner")


def run_tests(test_type="all", verbose=False, show_output=False):
    """
    Run tests with specified options.

    Args:
        test_type: Type of tests to run ("all", "unit", "integration", or specific file)
        verbose: Show verbose output
        show_output: Show print statements from tests
    """
    log.info("=" * 70)
    log.info("PAPER-AGENT TEST SUITE")
    log.info("=" * 70)

    # Build pytest command
    cmd = ["pytest"]

    # Select test scope
    if test_type == "all":
        cmd.append("tests/")
        log.info("Running: ALL TESTS")
    elif test_type == "unit":
        cmd.extend([
            "tests/test_pdf_metadata.py",
            "tests/test_citation_formatter.py"
        ])
        log.info("Running: UNIT TESTS")
    elif test_type == "integration":
        cmd.extend([
            "tests/test_search_tools.py",
            "tests/test_integration.py",
            "-m", "integration"
        ])
        log.info("Running: INTEGRATION TESTS")
    else:
        # Specific test file
        test_path = Path(f"tests/{test_type}")
        if not test_path.exists():
            test_path = Path(test_type)

        if test_path.exists():
            cmd.append(str(test_path))
            log.info(f"Running: {test_path}")
        else:
            log.error(f"Test file not found: {test_type}")
            return 1

    # Add options
    if verbose:
        cmd.append("-v")

    if show_output:
        cmd.append("-s")

    # Always show summary
    cmd.extend(["--tb=short", "--color=yes"])

    log.info(f"Command: {' '.join(cmd)}")
    log.info("-" * 70)

    # Run tests
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)

        log.info("-" * 70)
        if result.returncode == 0:
            log.info("✓ ALL TESTS PASSED")
        else:
            log.error("✗ SOME TESTS FAILED")
        log.info("=" * 70)

        return result.returncode

    except KeyboardInterrupt:
        log.warning("\n⚠ Tests interrupted by user")
        return 130
    except Exception as e:
        log.error(f"Error running tests: {e}")
        return 1


def main():
    """Main entry point with argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run paper-agent test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                          # Run all tests
  python run_tests.py --unit                   # Run only unit tests
  python run_tests.py --integration            # Run only integration tests
  python run_tests.py --verbose                # Run with verbose output
  python run_tests.py --show-output            # Show print statements
  python run_tests.py test_citation_formatter.py  # Run specific file
  python run_tests.py -v -s --integration      # Integration tests with full output

Test Categories:
  - Unit tests: test_pdf_metadata.py, test_citation_formatter.py
  - Integration tests: test_search_tools.py, test_integration.py
        """
    )

    parser.add_argument(
        "test_file",
        nargs="?",
        default="all",
        help="Specific test file to run (default: all)"
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-s", "--show-output",
        action="store_true",
        help="Show print statements and logs from tests"
    )

    args = parser.parse_args()

    # Determine test type
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"
    else:
        test_type = args.test_file

    # Run tests
    sys.exit(run_tests(
        test_type=test_type,
        verbose=args.verbose,
        show_output=args.show_output
    ))


if __name__ == "__main__":
    main()
