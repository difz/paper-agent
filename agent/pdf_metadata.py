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
                log.debug(f"PDF metadata found: {pdf_info}")
                metadata['title'] = pdf_info.get('/Title', None)
                author_str = pdf_info.get('/Author', None)
                if author_str:
                    log.debug(f"Raw author string from PDF metadata: {author_str}")
                    metadata['authors'] = self._parse_authors(author_str)
                    log.debug(f"Parsed authors: {metadata['authors']}")

                # Try to extract year from creation date
                creation_date = pdf_info.get('/CreationDate', '')
                year = self._extract_year(creation_date)
                if year:
                    metadata['year'] = year
            else:
                log.debug("No PDF metadata found")

            # Extract from first page text (fallback for missing metadata)
            if len(reader.pages) > 0:
                first_page_text = reader.pages[0].extract_text()

                # If title not in metadata, try to extract from first page
                if not metadata['title']:
                    metadata['title'] = self._extract_title_from_text(first_page_text)

                # Extract authors from first page if not in metadata
                if not metadata['authors']:
                    log.debug("Attempting to extract authors from first page text...")
                    metadata['authors'] = self._extract_authors_from_text(first_page_text)
                    if metadata['authors']:
                        log.debug(f"Extracted authors from text: {metadata['authors']}")
                    else:
                        log.debug("No authors found in first page text")

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
        authors = re.split(r'[;,]|\sand\s|\s&\s|\n', author_str)

        # Clean up each author name
        cleaned = []
        for author in authors:
            author = author.strip()
            # Remove email addresses
            author = re.sub(r'\s*\([^)]*@[^)]*\)', '', author)
            # Remove affiliations in parentheses/brackets
            author = re.sub(r'\s*[\[\(][^\]\)]*[\]\)]', '', author)
            # Remove trailing numbers and symbols
            author = re.sub(r'[\d\*†‡§¹²³⁴⁵⁶⁷⁸⁹⁰,]+$', '', author).strip()

            if author and len(author) > 2:
                cleaned.append(author)

        return cleaned

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
        lines = text.split('\n')

        # Skip first 5 lines (usually title) and scan for author section
        start_line = 3

        # Strategy 1: Look for the author section (names followed by "Department")
        # This is the most reliable pattern for academic papers
        for i in range(start_line, min(len(lines), 60)):
            line = lines[i].strip()

            if not line or len(line) > 200:
                continue

            # Check if next line has department/university keywords
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip().lower()

                # If next line starts with "department", current line is likely an author
                if (next_line.startswith('department') or 'department of' in next_line or
                    'university' in next_line or 'college' in next_line):

                    # CamelCase name: "NadimpalliMadanaKailashVarma"
                    if re.match(r'^([A-Z][a-z]+){2,6}$', line) and 10 < len(line) < 60:
                        name = re.sub(r'([a-z])([A-Z])', r'\1 \2', line)
                        # Filter out title words
                        title_words = ['Machine', 'Learning', 'System', 'Track', 'Enable',
                                      'Urban', 'Mobility', 'Enhanced', 'Real', 'Time', 'Smart',
                                      'Transit', 'Bus']
                        if not any(word in name for word in title_words):
                            authors.append(name.strip())

                    # Initial + name: "G.RishabBabu"
                    elif re.match(r'^[A-Z]\.(?:\s*[A-Z][a-z]+){1,3}$', line):
                        name = re.sub(r'\.([A-Z])', r'. \1', line)
                        name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
                        authors.append(name.strip())

                    # Title + name: "Mrs.FatimaUnnisa" or "Dr.JohnSmith"
                    elif re.match(r'^(?:Mrs?\.?|Dr\.?|Prof\.?)[A-Z]', line):
                        name = re.sub(r'(^(?:Mrs?|Dr|Prof))\.([A-Z])', r'\1. \2', line)
                        name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
                        authors.append(name.strip())

                    # Normal spaced name: "John Smith"
                    elif re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+){1,4}$', line):
                        authors.append(line.strip())

            # Stop after finding 10 authors
            if len(authors) >= 10:
                break

        # Strategy 2: If still no authors, look for names followed by "Department" pattern
        # This is common in IEEE/ACM papers: Name\nDepartment of...\n
        if len(authors) < 2:  # Need at least 2 authors
            for i, line in enumerate(lines[:60]):
                line = line.strip()

                # Check if next line has department/university
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip().lower()

                    # If next line starts with "department", current line might be an author
                    if next_line.startswith('department') or 'department of' in next_line:
                        # Current line should be a name (handle both normal and CamelCase)
                        if re.match(r'^([A-Z][a-z]+){2,6}$', line) and 10 < len(line) < 60:
                            # CamelCase name
                            name = re.sub(r'([a-z])([A-Z])', r'\1 \2', line)
                            # Don't add if it looks like a title
                            if not any(word in name for word in ['System', 'Track', 'Enable', 'Urban', 'Mobility', 'Enhanced', 'Real']):
                                authors.append(name.strip())
                        elif re.match(r'^[A-Z]\.(?:\s*[A-Z][a-z]+){1,3}$', line):
                            # Initial format: "G.RishabBabu"
                            name = re.sub(r'\.([A-Z])', r'. \1', line)
                            name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
                            authors.append(name.strip())
                        elif re.match(r'^(?:Mrs?\.?|Dr\.?|Prof\.?)\s*[A-Z]', line):
                            # Title + name: "Mrs.FatimaUnnisa"
                            name = re.sub(r'\.([A-Z])', r'. \1', line)
                            name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
                            authors.append(name.strip())

        # Clean up and deduplicate
        cleaned_authors = []
        seen = set()
        for author in authors[:15]:  # Check up to 15 potential authors
            author = author.strip()
            # Remove trailing numbers, symbols, and extra text
            author = re.sub(r'[\d\*†‡§¹²³⁴⁵⁶⁷⁸⁹⁰]+$', '', author).strip()
            # Remove email addresses
            author = re.sub(r'\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', author).strip()

            # Validate: must be at least 4 chars, start with capital, contain at least one space or dot
            if (author and len(author) >= 4 and author[0].isupper() and
                (' ' in author or '.' in author) and author not in seen):
                # Skip if it's a common false positive
                false_positives = ['Abstract', 'Introduction', 'Keywords', 'References',
                                  'Acknowledgment', 'Conclusion', 'Results', 'Methods',
                                  'Machine Learning', 'Artificial Intelligence', 'Deep Learning']
                if author not in false_positives:
                    cleaned_authors.append(author)
                    seen.add(author)

        return cleaned_authors[:10]  # Limit to first 10 authors

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
