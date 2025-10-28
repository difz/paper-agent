"""
Citation export utilities for generating citations in various formats.
Supports BibTeX, APA, MLA, Chicago, and IEEE formats.
"""
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime

log = logging.getLogger("citation_export")


class Citation:
    """Represents a citation with all relevant metadata."""

    def __init__(self, **kwargs):
        self.title = kwargs.get('title', '')
        self.authors = kwargs.get('authors', [])  # List of author names
        self.year = kwargs.get('year', '')
        self.journal = kwargs.get('journal', '')
        self.volume = kwargs.get('volume', '')
        self.issue = kwargs.get('issue', '')
        self.pages = kwargs.get('pages', '')
        self.doi = kwargs.get('doi', '')
        self.url = kwargs.get('url', '')
        self.publisher = kwargs.get('publisher', '')
        self.pdf_file = kwargs.get('pdf_file', '')
        self.page_num = kwargs.get('page_num', '')

    def to_bibtex(self, cite_key: Optional[str] = None) -> str:
        """Generate BibTeX citation."""
        if not cite_key:
            # Generate cite key from first author + year
            first_author = self.authors[0].split()[-1] if self.authors else "Unknown"
            cite_key = f"{first_author}{self.year}"

        lines = [f"@article{{{cite_key},"]

        if self.title:
            lines.append(f"  title = {{{self.title}}},")
        if self.authors:
            authors_str = " and ".join(self.authors)
            lines.append(f"  author = {{{authors_str}}},")
        if self.year:
            lines.append(f"  year = {{{self.year}}},")
        if self.journal:
            lines.append(f"  journal = {{{self.journal}}},")
        if self.volume:
            lines.append(f"  volume = {{{self.volume}}},")
        if self.issue:
            lines.append(f"  number = {{{self.issue}}},")
        if self.pages:
            lines.append(f"  pages = {{{self.pages}}},")
        if self.doi:
            lines.append(f"  doi = {{{self.doi}}},")
        if self.url:
            lines.append(f"  url = {{{self.url}}},")

        lines.append("}")
        return "\n".join(lines)

    def to_apa(self) -> str:
        """Generate APA 7th edition citation."""
        parts = []

        # Authors
        if self.authors:
            if len(self.authors) == 1:
                parts.append(self.authors[0])
            elif len(self.authors) == 2:
                parts.append(f"{self.authors[0]}, & {self.authors[1]}")
            elif len(self.authors) <= 20:
                parts.append(", ".join(self.authors[:-1]) + f", & {self.authors[-1]}")
            else:
                parts.append(", ".join(self.authors[:19]) + ", ... " + self.authors[-1])

        # Year
        if self.year:
            parts.append(f"({self.year}).")
        else:
            parts.append("(n.d.).")

        # Title
        if self.title:
            parts.append(f"{self.title}.")

        # Journal info
        if self.journal:
            journal_part = f"*{self.journal}*"
            if self.volume:
                journal_part += f", *{self.volume}*"
            if self.issue:
                journal_part += f"({self.issue})"
            if self.pages:
                journal_part += f", {self.pages}"
            parts.append(journal_part + ".")

        # DOI or URL
        if self.doi:
            parts.append(f"https://doi.org/{self.doi}")
        elif self.url:
            parts.append(self.url)

        return " ".join(parts)

    def to_mla(self) -> str:
        """Generate MLA 9th edition citation."""
        parts = []

        # Authors
        if self.authors:
            if len(self.authors) == 1:
                # Last, First
                name_parts = self.authors[0].split()
                if len(name_parts) >= 2:
                    parts.append(f"{name_parts[-1]}, {' '.join(name_parts[:-1])}.")
                else:
                    parts.append(f"{self.authors[0]}.")
            elif len(self.authors) == 2:
                parts.append(f"{self.authors[0]}, and {self.authors[1]}.")
            else:
                parts.append(f"{self.authors[0]}, et al.")

        # Title
        if self.title:
            parts.append(f'"{self.title}."')

        # Journal
        if self.journal:
            parts.append(f"*{self.journal}*,")

        # Volume and issue
        if self.volume:
            vol_str = f"vol. {self.volume}"
            if self.issue:
                vol_str += f", no. {self.issue}"
            parts.append(vol_str + ",")

        # Year
        if self.year:
            parts.append(f"{self.year},")

        # Pages
        if self.pages:
            parts.append(f"pp. {self.pages}.")

        # DOI or URL
        if self.doi:
            parts.append(f"https://doi.org/{self.doi}.")
        elif self.url:
            parts.append(f"{self.url}.")

        return " ".join(parts)

    def to_chicago(self) -> str:
        """Generate Chicago Manual of Style citation."""
        parts = []

        # Authors
        if self.authors:
            if len(self.authors) == 1:
                # Last, First
                name_parts = self.authors[0].split()
                if len(name_parts) >= 2:
                    parts.append(f"{name_parts[-1]}, {' '.join(name_parts[:-1])}.")
                else:
                    parts.append(f"{self.authors[0]}.")
            else:
                parts.append(", ".join(self.authors) + ".")

        # Title
        if self.title:
            parts.append(f'"{self.title}."')

        # Journal
        if self.journal:
            journal_part = f"*{self.journal}*"
            if self.volume:
                journal_part += f" {self.volume}"
            if self.issue:
                journal_part += f", no. {self.issue}"
            parts.append(journal_part)

        # Year
        if self.year:
            parts.append(f"({self.year}):")

        # Pages
        if self.pages:
            parts.append(f"{self.pages}.")

        # DOI
        if self.doi:
            parts.append(f"https://doi.org/{self.doi}.")

        return " ".join(parts)

    def to_ieee(self) -> str:
        """Generate IEEE citation."""
        parts = []

        # Authors (initials + last name)
        if self.authors:
            author_parts = []
            for author in self.authors[:6]:  # IEEE uses up to 6 authors
                name_parts = author.split()
                if len(name_parts) >= 2:
                    initials = ". ".join([n[0] for n in name_parts[:-1]]) + "."
                    author_parts.append(f"{initials} {name_parts[-1]}")
                else:
                    author_parts.append(author)

            if len(self.authors) > 6:
                author_parts.append("et al.")

            parts.append(", ".join(author_parts) + ",")

        # Title
        if self.title:
            parts.append(f'"{self.title},"')

        # Journal
        if self.journal:
            journal_part = f"*{self.journal}*"
            if self.volume:
                journal_part += f", vol. {self.volume}"
            if self.issue:
                journal_part += f", no. {self.issue}"
            if self.pages:
                journal_part += f", pp. {self.pages}"
            if self.year:
                journal_part += f", {self.year}"
            parts.append(journal_part + ".")

        # DOI
        if self.doi:
            parts.append(f"doi: {self.doi}.")

        return " ".join(parts)

    def to_plain(self) -> str:
        """Generate simple plain text citation."""
        parts = []

        if self.authors:
            parts.append(", ".join(self.authors))

        if self.year:
            parts.append(f"({self.year})")

        if self.title:
            parts.append(self.title)

        if self.journal:
            parts.append(self.journal)

        if self.pdf_file and self.page_num:
            parts.append(f"[{self.pdf_file}, p.{self.page_num}]")

        return ". ".join(parts)


class CitationManager:
    """Manages citation extraction and formatting."""

    def __init__(self):
        self.citations = {}

    def extract_from_text(self, text: str) -> List[Citation]:
        """
        Extract citation information from text (e.g., from search results).

        Args:
            text: Text containing citation information

        Returns:
            List of Citation objects
        """
        citations = []

        # Try to extract citations from formatted search results
        # This is a simple implementation - can be enhanced
        pattern = r'\*\*(.*?)\*\*\s*\nAuthors?: (.*?)\nYear: (\d{4})?'
        matches = re.findall(pattern, text, re.MULTILINE)

        for match in matches:
            title, authors, year = match
            author_list = [a.strip() for a in authors.split(',')]

            citation = Citation(
                title=title.strip(),
                authors=author_list,
                year=year
            )
            citations.append(citation)

        return citations

    def format_bibliography(self, citations: List[Citation], format_type: str = "apa") -> str:
        """
        Format multiple citations as a bibliography.

        Args:
            citations: List of Citation objects
            format_type: Citation format (apa, mla, chicago, bibtex, ieee)

        Returns:
            Formatted bibliography string
        """
        if not citations:
            return "No citations to format."

        lines = []

        for i, citation in enumerate(citations, 1):
            if format_type.lower() == "bibtex":
                lines.append(citation.to_bibtex(f"ref{i}"))
            elif format_type.lower() == "apa":
                lines.append(citation.to_apa())
            elif format_type.lower() == "mla":
                lines.append(citation.to_mla())
            elif format_type.lower() == "chicago":
                lines.append(citation.to_chicago())
            elif format_type.lower() == "ieee":
                lines.append(f"[{i}] {citation.to_ieee()}")
            else:
                lines.append(citation.to_plain())

            lines.append("")  # Empty line between citations

        return "\n".join(lines)
