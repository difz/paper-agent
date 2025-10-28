"""
Demo script to test academic search functionality.
Run this to verify search tools are working.
"""
from agent.logging_conf import setup_logging
from agent.search_tools import (
    SemanticScholarSearch,
    ArXivSearch,
    search_academic_papers
)

def main():
    setup_logging()
    print("=" * 80)
    print("Academic Paper Search Demo")
    print("=" * 80)

    # Test Semantic Scholar
    print("\n1. Testing Semantic Scholar Search...")
    print("-" * 80)
    ss = SemanticScholarSearch()
    result = ss.search("attention mechanism transformers", limit=2)
    print(result)

    # Test arXiv
    print("\n\n2. Testing arXiv Search...")
    print("-" * 80)
    arxiv = ArXivSearch()
    result = arxiv.search("neural networks", limit=2)
    print(result)

    # Test multi-source search
    print("\n\n3. Testing Multi-Source Search...")
    print("-" * 80)
    result = search_academic_papers(
        "reinforcement learning",
        sources=["semantic_scholar", "arxiv"]
    )
    print(result)

    print("\n" + "=" * 80)
    print("Demo complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
