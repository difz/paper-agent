"""
Enhanced search tools with free alternatives and advanced filtering.
Includes: CrossRef (free DOI lookup), PubMed (free medical papers),
CORE (free academic search), and OpenAlex (free academic graph).
"""
import os
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime

log = logging.getLogger("search_tools_enhanced")


class CrossRefSearch:
    """Search CrossRef for DOI metadata (completely free)."""

    BASE_URL = "https://api.crossref.org/works"

    def search(self, query: str, limit: int = 5, year_from: Optional[int] = None,
               year_to: Optional[int] = None) -> str:
        """
        Search CrossRef for papers.

        Args:
            query: Search query
            limit: Number of results
            year_from: Filter by year from
            year_to: Filter by year to

        Returns:
            Formatted string with results
        """
        try:
            params = {
                "query": query,
                "rows": limit,
                "mailto": "researcher@example.com"  # Polite pool access
            }

            # Add date filter if provided
            if year_from or year_to:
                from_date = f"{year_from}-01-01" if year_from else "1900-01-01"
                to_date = f"{year_to}-12-31" if year_to else datetime.now().strftime("%Y-%m-%d")
                params["filter"] = f"from-pub-date:{from_date},until-pub-date:{to_date}"

            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("message", {}).get("items"):
                return f"No papers found for query: {query}"

            results = []
            for item in data["message"]["items"][:limit]:
                title = item.get("title", ["Unknown"])[0]
                authors = item.get("author", [])
                author_names = [f"{a.get('given', '')} {a.get('family', '')}".strip()
                               for a in authors[:3]]
                if len(authors) > 3:
                    author_names.append("et al.")
                author_str = ", ".join(author_names)

                # Published date
                pub_date = item.get("published-print", item.get("published-online", {}))
                year = pub_date.get("date-parts", [[None]])[0][0]

                # Journal
                journal = item.get("container-title", [""])[0]

                # DOI
                doi = item.get("DOI", "")

                # Citations
                cited_by = item.get("is-referenced-by-count", 0)

                result = f"**{title}**\n"
                if author_str:
                    result += f"Authors: {author_str}\n"
                if year:
                    result += f"Year: {year}"
                if cited_by:
                    result += f" | Citations: {cited_by}"
                result += "\n"
                if journal:
                    result += f"Journal: {journal}\n"
                if doi:
                    result += f"DOI: https://doi.org/{doi}\n"

                results.append(result)

            return "\n---\n".join(results)

        except Exception as e:
            log.error(f"CrossRef search error: {e}")
            return f"Error searching CrossRef: {str(e)}"


class OpenAlexSearch:
    """Search OpenAlex - free and open catalog of scholarly papers."""

    BASE_URL = "https://api.openalex.org/works"

    def search(self, query: str, limit: int = 5, year_from: Optional[int] = None,
               year_to: Optional[int] = None, author: Optional[str] = None) -> str:
        """
        Search OpenAlex for papers.

        Args:
            query: Search query
            limit: Number of results
            year_from: Filter by year from
            year_to: Filter by year to
            author: Filter by author name

        Returns:
            Formatted string with results
        """
        try:
            params = {
                "search": query,
                "per_page": limit,
                "mailto": "researcher@example.com"
            }

            # Build filter
            filters = []
            if year_from:
                filters.append(f"from_publication_date:{year_from}-01-01")
            if year_to:
                filters.append(f"to_publication_date:{year_to}-12-31")
            if author:
                filters.append(f"author.search:{author}")

            if filters:
                params["filter"] = ",".join(filters)

            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("results"):
                return f"No papers found for query: {query}"

            results = []
            for item in data["results"][:limit]:
                title = item.get("title", "Unknown title")

                # Authors
                authorships = item.get("authorships", [])
                author_names = [a.get("author", {}).get("display_name", "")
                               for a in authorships[:3]]
                if len(authorships) > 3:
                    author_names.append("et al.")
                author_str = ", ".join(author_names)

                # Year
                year = item.get("publication_year")

                # Citations
                cited_by = item.get("cited_by_count", 0)

                # Venue
                venue = item.get("host_venue", {}).get("display_name", "")

                # Open access
                oa_status = item.get("open_access", {}).get("oa_status", "closed")
                oa_url = item.get("open_access", {}).get("oa_url", "")

                # DOI
                doi = item.get("doi", "").replace("https://doi.org/", "")

                result = f"**{title}**\n"
                if author_str:
                    result += f"Authors: {author_str}\n"
                if year:
                    result += f"Year: {year}"
                if cited_by:
                    result += f" | Citations: {cited_by}"
                result += "\n"
                if venue:
                    result += f"Venue: {venue}\n"
                if oa_status != "closed":
                    result += f"Open Access: {oa_status.upper()}\n"
                if oa_url:
                    result += f"PDF: {oa_url}\n"
                if doi:
                    result += f"DOI: https://doi.org/{doi}\n"

                results.append(result)

            return "\n---\n".join(results)

        except Exception as e:
            log.error(f"OpenAlex search error: {e}")
            return f"Error searching OpenAlex: {str(e)}"


class CORESearch:
    """Search CORE - free access to millions of research papers."""

    BASE_URL = "https://api.core.ac.uk/v3/search/works"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("CORE_API_KEY")  # Optional, free tier available

    def search(self, query: str, limit: int = 5, year_from: Optional[int] = None,
               year_to: Optional[int] = None) -> str:
        """
        Search CORE for papers.

        Args:
            query: Search query
            limit: Number of results
            year_from: Filter by year from
            year_to: Filter by year to

        Returns:
            Formatted string with results
        """
        if not self.api_key:
            return "CORE search requires an API key. Get one free at https://core.ac.uk/services/api"

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}

            # Build query
            search_query = query
            if year_from and year_to:
                search_query += f" AND yearPublished:>={year_from} AND yearPublished:<={year_to}"
            elif year_from:
                search_query += f" AND yearPublished:>={year_from}"
            elif year_to:
                search_query += f" AND yearPublished:<={year_to}"

            params = {
                "q": search_query,
                "limit": limit
            }

            response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("results"):
                return f"No papers found for query: {query}"

            results = []
            for item in data["results"][:limit]:
                title = item.get("title", "Unknown title")
                authors = item.get("authors", [])
                author_str = ", ".join([a for a in authors[:3]])
                if len(authors) > 3:
                    author_str += " et al."

                year = item.get("yearPublished")
                abstract = item.get("abstract", "")
                if len(abstract) > 200:
                    abstract = abstract[:200] + "..."

                download_url = item.get("downloadUrl", "")
                doi = item.get("doi", "")

                result = f"**{title}**\n"
                if author_str:
                    result += f"Authors: {author_str}\n"
                if year:
                    result += f"Year: {year}\n"
                if abstract:
                    result += f"Abstract: {abstract}\n"
                if download_url:
                    result += f"PDF: {download_url}\n"
                if doi:
                    result += f"DOI: {doi}\n"

                results.append(result)

            return "\n---\n".join(results)

        except Exception as e:
            log.error(f"CORE search error: {e}")
            return f"Error searching CORE: {str(e)}"


class PubMedSearch:
    """Search PubMed for medical/biomedical papers (completely free)."""

    SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def search(self, query: str, limit: int = 5, year_from: Optional[int] = None,
               year_to: Optional[int] = None) -> str:
        """
        Search PubMed for papers.

        Args:
            query: Search query
            limit: Number of results
            year_from: Filter by year from
            year_to: Filter by year to

        Returns:
            Formatted string with results
        """
        try:
            # Build date filter
            search_term = query
            if year_from and year_to:
                search_term += f" AND {year_from}:{year_to}[pdat]"
            elif year_from:
                search_term += f" AND {year_from}:3000[pdat]"
            elif year_to:
                search_term += f" AND 1900:{year_to}[pdat]"

            # Search for IDs
            search_params = {
                "db": "pubmed",
                "term": search_term,
                "retmax": limit,
                "retmode": "json"
            }

            response = requests.get(self.SEARCH_URL, params=search_params, timeout=10)
            response.raise_for_status()
            data = response.json()

            id_list = data.get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return f"No papers found for query: {query}"

            # Fetch details
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml"
            }

            response = requests.get(self.FETCH_URL, params=fetch_params, timeout=10)
            response.raise_for_status()

            # Parse XML (simple text extraction)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            results = []
            for article in root.findall(".//PubmedArticle")[:limit]:
                # Title
                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else "Unknown title"

                # Authors
                author_elems = article.findall(".//Author")
                authors = []
                for author in author_elems[:3]:
                    last = author.find("LastName")
                    first = author.find("ForeName")
                    if last is not None:
                        name = last.text
                        if first is not None:
                            name = f"{first.text} {name}"
                        authors.append(name)

                if len(author_elems) > 3:
                    authors.append("et al.")
                author_str = ", ".join(authors)

                # Year
                year_elem = article.find(".//PubDate/Year")
                year = year_elem.text if year_elem is not None else "N/A"

                # Journal
                journal_elem = article.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else ""

                # PMID
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else ""

                result = f"**{title}**\n"
                if author_str:
                    result += f"Authors: {author_str}\n"
                result += f"Year: {year}\n"
                if journal:
                    result += f"Journal: {journal}\n"
                if pmid:
                    result += f"PubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/\n"

                results.append(result)

            return "\n---\n".join(results)

        except Exception as e:
            log.error(f"PubMed search error: {e}")
            return f"Error searching PubMed: {str(e)}"


def search_academic_papers_enhanced(query: str, sources: List[str] = None,
                                   year_from: Optional[int] = None,
                                   year_to: Optional[int] = None,
                                   author: Optional[str] = None) -> str:
    """
    Enhanced academic search with filters.

    Args:
        query: Search query
        sources: List of sources to search
        year_from: Filter by year from
        year_to: Filter by year to
        author: Filter by author name

    Returns:
        Formatted string with results
    """
    if sources is None:
        sources = ['openalex', 'crossref', 'arxiv']

    all_results = []

    if 'openalex' in sources:
        log.info(f"Searching OpenAlex for: {query}")
        oa = OpenAlexSearch()
        result = oa.search(query, limit=3, year_from=year_from, year_to=year_to, author=author)
        all_results.append(f"=== OPENALEX RESULTS (FREE) ===\n{result}")

    if 'crossref' in sources:
        log.info(f"Searching CrossRef for: {query}")
        cr = CrossRefSearch()
        result = cr.search(query, limit=3, year_from=year_from, year_to=year_to)
        all_results.append(f"=== CROSSREF RESULTS (FREE) ===\n{result}")

    if 'pubmed' in sources:
        log.info(f"Searching PubMed for: {query}")
        pm = PubMedSearch()
        result = pm.search(query, limit=3, year_from=year_from, year_to=year_to)
        all_results.append(f"=== PUBMED RESULTS (FREE) ===\n{result}")

    if 'core' in sources:
        log.info(f"Searching CORE for: {query}")
        core = CORESearch()
        result = core.search(query, limit=3, year_from=year_from, year_to=year_to)
        all_results.append(f"=== CORE RESULTS ===\n{result}")

    # Include original arXiv if requested
    if 'arxiv' in sources:
        from .search_tools import ArXivSearch
        log.info(f"Searching arXiv for: {query}")
        arxiv = ArXivSearch()
        result = arxiv.search(query, limit=3)
        all_results.append(f"=== ARXIV RESULTS (FREE) ===\n{result}")

    return "\n\n".join(all_results)
