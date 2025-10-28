import os
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from .config import Settings


def _retriever():
    s = Settings()
    emb = GoogleGenerativeAIEmbeddings(model=s.embed_model)
    vs = Chroma(persist_directory=s.chroma_dir, embedding_function=emb)
    return vs.as_retriever(search_kwargs={"k": s.top_k})

@tool
def retrieve_passages(q: str) -> str:
    docs = _retriever().invoke(q)
    lines = []
    for d in docs:
        page = d.metadata.get("page", "?")
        src  = os.path.basename(d.metadata.get("source", ""))
        txt  = d.page_content.replace("\n", " ")
        if len(txt) > 450: txt = txt[:450] + "…"
        lines.append(f"- {txt}\n  _{src}, p.{page}_")
    return "\n".join(lines) if lines else "No passages found."

@tool
def summarize_with_citations(q: str) -> str:
    s = Settings()
    retriever = _retriever()
    docs = retriever.invoke(q)
    context = "\n\n---\n\n".join([d.page_content for d in docs])

    llm = ChatGoogleGenerativeAI(model=s.llm_model, temperature=0)
    prompt = ChatPromptTemplate.from_template(
        """You are a research assistant. Write a concise answer in bullet points.
Each point MUST be grounded in CONTEXT and include (source, p.page) if present.
If info is missing, state what's missing.

QUESTION:
{question}

CONTEXT:
{context}
""")
    chain = prompt | llm
    return chain.invoke({"question": q, "context": context}).content
