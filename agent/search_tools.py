"""
Search tools for finding academic papers and journals from multiple sources.
Supports Semantic Scholar, arXiv, and Google Custom Search.
"""
import os
import logging
import requests
from typing import List, Dict, Optional
from urllib.parse import quote

log = logging.getLogger("search_tools")


class SemanticScholarSearch:
    """Search Semantic Scholar for academic papers."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.headers = {}
        if self.api_key:
            self.headers["x-api-key"] = self.api_key

    def search(self, query: str, limit: int = 5) -> str:
        """
        Search Semantic Scholar for papers.
        Returns formatted string with title, authors, year, citations, and URL.
        """
        try:
            url = f"{self.BASE_URL}/paper/search"
            params = {
                "query": query,
                "limit": limit,
                "fields": "title,authors,year,citationCount,abstract,url,openAccessPdf"
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("data"):
                return f"No papers found for query: {query}"

            results = []
            for paper in data["data"]:
                authors = ", ".join([a.get("name", "") for a in paper.get("authors", [])[:3]])
                if len(paper.get("authors", [])) > 3:
                    authors += " et al."

                title = paper.get("title", "Unknown title")
                year = paper.get("year", "N/A")
                citations = paper.get("citationCount", 0)
                abstract = paper.get("abstract", "")
                url = paper.get("url", "")
                pdf_url = paper.get("openAccessPdf", {}).get("url", "") if paper.get("openAccessPdf") else ""

                # Truncate abstract
                if abstract and len(abstract) > 200:
                    abstract = abstract[:200] + "..."

                result = f"**{title}**\n"
                result += f"Authors: {authors}\n"
                result += f"Year: {year} | Citations: {citations}\n"
                if abstract:
                    result += f"Abstract: {abstract}\n"
                if url:
                    result += f"URL: {url}\n"
                if pdf_url:
                    result += f"PDF: {pdf_url}\n"

                results.append(result)

            return "\n---\n".join(results)

        except Exception as e:
            log.error(f"Semantic Scholar search error: {e}")
            return f"Error searching Semantic Scholar: {str(e)}"


class ArXivSearch:
    """Search arXiv for preprints and papers."""

    BASE_URL = "http://export.arxiv.org/api/query"

    def search(self, query: str, limit: int = 5) -> str:
        """
        Search arXiv for papers.
        Returns formatted string with title, authors, published date, and PDF link.
        """
        try:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": limit,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }

            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            # Namespace handling
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            entries = root.findall('atom:entry', ns)

            if not entries:
                return f"No papers found on arXiv for query: {query}"

            results = []
            for entry in entries:
                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')

                authors = entry.findall('atom:author', ns)
                author_names = [a.find('atom:name', ns).text for a in authors[:3]]
                if len(authors) > 3:
                    author_names.append("et al.")
                author_str = ", ".join(author_names)

                published = entry.find('atom:published', ns).text[:10]  # YYYY-MM-DD
                summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                if len(summary) > 200:
                    summary = summary[:200] + "..."

                pdf_link = entry.find('atom:id', ns).text.replace('/abs/', '/pdf/') + '.pdf'
                abs_link = entry.find('atom:id', ns).text

                result = f"**{title}**\n"
                result += f"Authors: {author_str}\n"
                result += f"Published: {published}\n"
                result += f"Abstract: {summary}\n"
                result += f"URL: {abs_link}\n"
                result += f"PDF: {pdf_link}\n"

                results.append(result)

            return "\n---\n".join(results)

        except Exception as e:
            log.error(f"arXiv search error: {e}")
            return f"Error searching arXiv: {str(e)}"


class GoogleScholarSearch:
    """Search using Google Custom Search API (can include Scholar results)."""

    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.cse_id = cse_id or os.getenv("GOOGLE_CSE_ID")

    def search(self, query: str, limit: int = 5) -> str:
        """
        Search using Google Custom Search.
        Requires GOOGLE_API_KEY and GOOGLE_CSE_ID.
        """
        if not self.api_key or not self.cse_id:
            return "Google Search not configured. Set GOOGLE_API_KEY and GOOGLE_CSE_ID."

        try:
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": query,
                "num": min(limit, 10)
            }

            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "items" not in data:
                return f"No results found for query: {query}"

            results = []
            for item in data["items"]:
                title = item.get("title", "")
                link = item.get("link", "")
                snippet = item.get("snippet", "")

                result = f"**{title}**\n"
                result += f"{snippet}\n"
                result += f"URL: {link}\n"

                results.append(result)

            return "\n---\n".join(results)

        except Exception as e:
            log.error(f"Google Search error: {e}")
            return f"Error searching Google: {str(e)}"


# Main search function that tries multiple sources
def search_academic_papers(query: str, sources: List[str] = None) -> str:
    """
    Search for academic papers across multiple sources.

    Args:
        query: Search query
        sources: List of sources to search. Options: ['semantic_scholar', 'arxiv', 'google']
                 If None, searches all available sources.

    Returns:
        Formatted string with results from all sources.
    """
    if sources is None:
        sources = ['semantic_scholar', 'arxiv', 'google']

    all_results = []

    if 'semantic_scholar' in sources:
        log.info(f"Searching Semantic Scholar for: {query}")
        ss = SemanticScholarSearch()
        result = ss.search(query, limit=3)
        all_results.append(f"=== SEMANTIC SCHOLAR RESULTS ===\n{result}")

    if 'arxiv' in sources:
        log.info(f"Searching arXiv for: {query}")
        arxiv = ArXivSearch()
        result = arxiv.search(query, limit=3)
        all_results.append(f"=== ARXIV RESULTS ===\n{result}")

    if 'google' in sources:
        log.info(f"Searching Google for: {query}")
        google = GoogleScholarSearch()
        result = google.search(query, limit=3)
        all_results.append(f"=== GOOGLE SEARCH RESULTS ===\n{result}")

    return "\n\n".join(all_results)
