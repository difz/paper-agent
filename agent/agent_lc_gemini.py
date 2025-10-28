from langchain.agents import Tool, initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from .tools_gemini import retrieve_passages, summarize_with_citations
from .search_tools import search_academic_papers
from .config import Settings

def build_agent():
    s = Settings()
    llm = ChatGoogleGenerativeAI(model=s.llm_model, temperature=0)
    tools = [
        Tool(name="retrieve", func=retrieve_passages,
             description="Fetch relevant quoted passages from indexed PDFs uploaded by users."),
        Tool(name="summarize", func=summarize_with_citations,
             description="Summarize retrieved passages with inline citations from user PDFs."),
        Tool(name="search_papers", func=search_academic_papers,
             description="Search for academic papers and journals from Semantic Scholar, arXiv, and Google. Use this to find related research papers when the user asks for external sources or when local PDFs don't have enough information."),
    ]
    return initialize_agent(
        tools, llm,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False, handle_parsing_errors=True
    )

def ask_agent(message: str) -> str:
    return build_agent().run(message)
