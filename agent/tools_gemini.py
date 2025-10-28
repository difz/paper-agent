import os
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from .config import Settings
from .citation_formatter import format_citation


def _retriever():
    s = Settings()
    emb = GoogleGenerativeAIEmbeddings(model=s.embed_model)
    vs = Chroma(persist_directory=s.chroma_dir, embedding_function=emb)
    return vs.as_retriever(search_kwargs={"k": s.top_k})

@tool
def retrieve_passages(q: str) -> str:
    """Retrieve relevant passages from indexed PDF documents based on the query."""
    docs = _retriever().invoke(q)
    lines = []
    for d in docs:
        page = d.metadata.get("page", "?")
        txt  = d.page_content.replace("\n", " ")
        if len(txt) > 450: txt = txt[:450] + "…"

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

@tool
def summarize_with_citations(q: str) -> str:
    """Summarize information from indexed PDFs with proper citations."""
    s = Settings()
    retriever = _retriever()
    docs = retriever.invoke(q)

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
        """You are a research assistant. Write a concise answer in bullet points.
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
    return chain.invoke({"question": q, "context": context}).content
