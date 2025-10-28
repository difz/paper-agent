"""
Discord-specific tools that work with per-user vector stores.
"""
import os
import logging
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from .config import Settings
from .user_store_manager import UserStoreManager
from .citation_formatter import format_citation
from langchain.tools import tool

log = logging.getLogger("tools_discord")

# Global store manager instance
store_manager = UserStoreManager()

def retrieve_passages_for_user(user_id: str, query: str) -> str:
    """
    Retrieve passages from a specific user's PDFs.

    Args:
        user_id: Discord user ID
        query: Search query

    Returns:
        Formatted string with passages and citations
    """
    retriever = store_manager.get_retriever(user_id)

    if retriever is None:
        return "No PDFs indexed yet. Please upload PDFs first using the upload command or by attaching PDFs to your message."

    try:
        docs = retriever.invoke(query)

        if not docs:
            return "No relevant passages found in your PDFs."

        lines = []
        for d in docs:
            page = d.metadata.get("page", "?")
            txt = d.page_content.replace("\n", " ")
            if len(txt) > 450:
                txt = txt[:450] + "…"

            # Format citation using bibliographic metadata (IEEE style by default)
            bib_metadata = {
                'authors': d.metadata.get('bib_authors', []),
                'title': d.metadata.get('bib_title'),
                'year': d.metadata.get('bib_year'),
                'journal': d.metadata.get('bib_journal'),
                'doi': d.metadata.get('bib_doi'),
            }
            citation = format_citation(bib_metadata, page=page, style='ieee', inline=True)

            lines.append(f"- {txt}\n  {citation}")

        return "\n".join(lines) if lines else "No passages found."

    except Exception as e:
        log.error(f"Error retrieving passages for user {user_id}: {e}")
        return f"Error retrieving passages: {str(e)}"

def summarize_with_citations_for_user(user_id: str, query: str) -> str:
    """
    Summarize information from a user's PDFs with citations.

    Args:
        user_id: Discord user ID
        query: Question to answer

    Returns:
        Formatted summary with citations
    """
    s = Settings()
    retriever = store_manager.get_retriever(user_id)

    if retriever is None:
        return "No PDFs indexed yet. Please upload PDFs first."

    try:
        docs = retriever.invoke(query)

        if not docs:
            return "No relevant information found in your PDFs for this question."

        # Build context with proper bibliographic metadata for citations
        context_parts = []
        for d in docs:
            page = d.metadata.get("page", "?")

            # Get bibliographic metadata
            authors = d.metadata.get('bib_authors', [])
            title = d.metadata.get('bib_title', 'Unknown Title')
            year = d.metadata.get('bib_year', 'n.d.')
            journal = d.metadata.get('bib_journal')

            # Build citation reference for this chunk
            authors_str = ', '.join(authors) if authors else 'Unknown Author'
            citation_ref = f"[Citation: {authors_str} ({year}). {title}"
            if journal:
                citation_ref += f". {journal}"
            citation_ref += f". Page {page}]"

            context_parts.append(f"{citation_ref}\n{d.page_content}")

        context = "\n\n---\n\n".join(context_parts)

        llm = ChatGoogleGenerativeAI(model=s.llm_model, temperature=0)
        prompt = ChatPromptTemplate.from_template(
            """You are a research assistant helping a researcher. Write a concise answer in bullet points.
Each point MUST be grounded in the CONTEXT provided below.

For EVERY claim, you MUST include an in-text citation in IEEE format using the information from the [Citation: ...] tags.

IEEE In-text Citation Format:
- Use: (Author(s), Year, p. Page)
- Example: (Smith, 2020, p. 5)
- Multiple authors: (Smith et al., 2020, p. 5)

IMPORTANT:
1. Extract the author name(s), year, and page number from the [Citation: ...] tags in the context
2. Format each citation exactly as shown in the IEEE format above
3. Do NOT use generic terms like "context" or "document"
4. Every factual claim MUST have a citation

If information is missing from the context, state what's missing.

QUESTION:
{question}

CONTEXT:
{context}
""")
        chain = prompt | llm
        return chain.invoke({"question": query, "context": context}).content

    except Exception as e:
        log.error(f"Error summarizing for user {user_id}: {e}")
        return f"Error generating summary: {str(e)}"

def create_user_tools(user_id: str):
    """
    Create tools bound to a specific user's context.

    Args:
        user_id: Discord user ID

    Returns:
        List of LangChain tools for the user
    """
    from langchain.tools import tool
    from .search_tools import search_academic_papers

    # Create user-specific tools with proper decorators
    @tool
    def retrieve_passages(query: str) -> str:
        """Retrieve relevant passages from your uploaded PDFs based on the query."""
        return retrieve_passages_for_user(user_id, query)

    @tool
    def summarize_with_citations(query: str) -> str:
        """Summarize information from your PDFs with proper citations."""
        return summarize_with_citations_for_user(user_id, query)

    return [
        retrieve_passages,
        summarize_with_citations,
        search_academic_papers
    ]
