from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from .tools_gemini import retrieve_passages, summarize_with_citations
from .search_tools import search_academic_papers
from .config import Settings

def build_agent():
    """Build a LangChain agent using the new 1.0+ API."""
    s = Settings()
    llm = ChatGoogleGenerativeAI(model=s.llm_model, temperature=0)
    tools = [
        retrieve_passages,
        summarize_with_citations,
        search_academic_papers
    ]

    # Create agent using new API (returns CompiledStateGraph)
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt="""You are a helpful research assistant. You can:
1. Answer general questions using your knowledge
2. Search and retrieve information from uploaded PDF documents (use retrieve_passages or summarize_with_citations tools)
3. Search for academic papers when needed (use search_academic_papers tool)

Use tools when the user asks about specific documents or needs to find academic papers. For general questions, feel free to answer directly using your knowledge."""
    )

def ask_agent(message: str) -> str:
    """Ask the agent a question and return the response."""
    agent_graph = build_agent()

    # Invoke with messages format
    result = agent_graph.invoke(
        {"messages": [{"role": "user", "content": message}]}
    )

    # Extract the final AI message
    messages = result.get("messages", [])
    if messages:
        # Get the last AI message
        for msg in reversed(messages):
            if hasattr(msg, 'content') and hasattr(msg, 'type') and msg.type == 'ai':
                content = msg.content
                # Handle structured content (list of content blocks)
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and 'text' in block:
                            text_parts.append(block['text'])
                        elif isinstance(block, str):
                            text_parts.append(block)
                    return '\n'.join(text_parts)
                elif isinstance(content, str):
                    return content
                else:
                    return str(content)
        # Fallback: return last message content
        if hasattr(messages[-1], 'content'):
            content = messages[-1].content
            if isinstance(content, str):
                return content
            return str(content)
        return str(messages[-1])

    return str(result)
