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
            src = os.path.basename(d.metadata.get("source", ""))
            txt = d.page_content.replace("\n", " ")
            if len(txt) > 450:
                txt = txt[:450] + "…"
            lines.append(f"- {txt}\n  _{src}, p.{page}_")

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

        context = "\n\n---\n\n".join([d.page_content for d in docs])

        llm = ChatGoogleGenerativeAI(model=s.llm_model, temperature=0)
        prompt = ChatPromptTemplate.from_template(
            """You are a research assistant helping a researcher. Write a concise answer in bullet points.
Each point MUST be grounded in CONTEXT and include (source, p.page) if present.
If info is missing, state what's missing.

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
    from langchain.agents import Tool
    from .search_tools import search_academic_papers

    return [
        Tool(
            name="retrieve",
            func=lambda q: retrieve_passages_for_user(user_id, q),
            description="Fetch relevant quoted passages from your uploaded PDFs."
        ),
        Tool(
            name="summarize",
            func=lambda q: summarize_with_citations_for_user(user_id, q),
            description="Summarize retrieved passages with inline citations from your PDFs."
        ),
        Tool(
            name="search_papers",
            func=search_academic_papers,
            description="Search for academic papers and journals from Semantic Scholar, arXiv, and Google. Use this to find related research papers when local PDFs don't have enough information."
        ),
    ]
