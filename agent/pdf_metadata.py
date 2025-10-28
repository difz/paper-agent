"""
Extract bibliographic metadata from PDF documents.
"""
import os
import re
import logging
from typing import Dict, Optional, List
from pypdf import PdfReader

log = logging.getLogger("pdf_metadata")


class PDFMetadataExtractor:
    """Extract bibliographic information from PDF documents."""

    def extract_metadata(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract metadata from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with metadata fields
        """
        metadata = {
            'filename': os.path.basename(pdf_path),
            'filepath': pdf_path,
            'title': None,
            'authors': [],
            'year': None,
            'journal': None,
            'doi': None,
            'abstract': None,
        }

        try:
            reader = PdfReader(pdf_path)

            # Extract from PDF metadata
            pdf_info = reader.metadata
            if pdf_info:
                metadata['title'] = pdf_info.get('/Title', None)
                author_str = pdf_info.get('/Author', None)
                if author_str:
                    metadata['authors'] = self._parse_authors(author_str)

                # Try to extract year from creation date
                creation_date = pdf_info.get('/CreationDate', '')
                year = self._extract_year(creation_date)
                if year:
                    metadata['year'] = year

            # Extract from first page text (fallback for missing metadata)
            if len(reader.pages) > 0:
                first_page_text = reader.pages[0].extract_text()

                # If title not in metadata, try to extract from first page
                if not metadata['title']:
                    metadata['title'] = self._extract_title_from_text(first_page_text)

                # Extract authors from first page if not in metadata
                if not metadata['authors']:
                    metadata['authors'] = self._extract_authors_from_text(first_page_text)

                # Extract year from first page if not in metadata
                if not metadata['year']:
                    metadata['year'] = self._extract_year_from_text(first_page_text)

                # Extract DOI
                metadata['doi'] = self._extract_doi(first_page_text)

                # Extract journal name
                metadata['journal'] = self._extract_journal(first_page_text)

                # Extract abstract (first few paragraphs)
                metadata['abstract'] = self._extract_abstract(first_page_text)

            # Fallback: use filename as title if still no title
            if not metadata['title']:
                metadata['title'] = os.path.splitext(metadata['filename'])[0].replace('_', ' ').replace('-', ' ')

        except Exception as e:
            log.error(f"Error extracting metadata from {pdf_path}: {e}")

        return metadata

    def _parse_authors(self, author_str: str) -> List[str]:
        """Parse author string into list of authors."""
        if not author_str:
            return []

        # Split by common delimiters
        authors = re.split(r'[;,]|\sand\s|\s&\s', author_str)
        return [a.strip() for a in authors if a.strip()]

    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extract year from date string."""
        if not date_str:
            return None

        # Look for 4-digit year
        match = re.search(r'(\d{4})', str(date_str))
        if match:
            year = int(match.group(1))
            if 1900 <= year <= 2100:
                return year
        return None

    def _extract_title_from_text(self, text: str) -> Optional[str]:
        """Extract title from first page text (usually the largest/first text)."""
        if not text:
            return None

        lines = text.split('\n')
        # Take the first substantial line (more than 10 chars)
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 10 and not line.isupper():
                return line
        return None

    def _extract_authors_from_text(self, text: str) -> List[str]:
        """Extract author names from first page text."""
        if not text:
            return []

        authors = []

        # Common patterns for author names in academic papers
        # Look for lines with format: "FirstName LastName"
        lines = text.split('\n')[:20]  # Check first 20 lines

        for line in lines:
            line = line.strip()
            # Skip empty lines and lines that are too long (likely not author names)
            if not line or len(line) > 100:
                continue

            # Pattern: Looks like names (2-5 words, capitalized)
            if re.match(r'^[A-Z][a-z]+(\s+[A-Z]\.?\s*)*[A-Z][a-z]+(\s*,?\s+(and|&)\s+[A-Z][a-z]+(\s+[A-Z]\.?\s*)*[A-Z][a-z]+)*$', line):
                # Parse multiple authors separated by 'and' or ','
                author_parts = re.split(r'\s+and\s+|\s*,\s*|\s+&\s+', line)
                authors.extend([a.strip() for a in author_parts if a.strip()])

        return authors[:10]  # Limit to first 10 authors

    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """Extract publication year from text."""
        if not text:
            return None

        # Look for year patterns (1900-2100)
        matches = re.findall(r'\b(19\d{2}|20\d{2})\b', text[:1000])
        if matches:
            # Return the most recent reasonable year
            years = [int(y) for y in matches if 1900 <= int(y) <= 2100]
            if years:
                return max(years)
        return None

    def _extract_doi(self, text: str) -> Optional[str]:
        """Extract DOI from text."""
        if not text:
            return None

        # DOI pattern: 10.xxxx/xxxxx
        match = re.search(r'10\.\d{4,}/[^\s]+', text)
        if match:
            return match.group(0).rstrip('.,;)')
        return None

    def _extract_journal(self, text: str) -> Optional[str]:
        """Extract journal name from text."""
        if not text:
            return None

        # Look for common journal indicators
        patterns = [
            r'(?:Published in|Journal of|Proceedings of)\s+([^\n]+)',
            r'([A-Z][a-z]+\s+(?:Journal|Review|Letters|Transactions)(?:\s+(?:of|on|in))?\s+[^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text[:1000])
            if match:
                journal = match.group(1).strip()
                # Clean up
                journal = re.sub(r'\s+', ' ', journal)
                return journal[:200]  # Limit length
        return None

    def _extract_abstract(self, text: str) -> Optional[str]:
        """Extract abstract from text."""
        if not text:
            return None

        # Look for "Abstract" section
        match = re.search(r'(?i)abstract[:\s]*\n(.+?)(?:\n\n|\n[A-Z]|\nKeywords:)', text, re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            # Clean up
            abstract = re.sub(r'\s+', ' ', abstract)
            return abstract[:500]  # Limit length
        return None


# Singleton instance
_extractor = PDFMetadataExtractor()


def extract_pdf_metadata(pdf_path: str) -> Dict[str, any]:
    """Extract metadata from a PDF file."""
    return _extractor.extract_metadata(pdf_path)
