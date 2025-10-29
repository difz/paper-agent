# Research Assistant Agent

A RAG (Retrieval-Augmented Generation) agent that helps researchers find relevant passages, synthesize answers, and ground every claim with real citations from PDFs. Integrates with Discord for easy collaboration and includes multi-source academic search.

## ✨ Features

### Core Features
- 📚 **PDF Analysis**: Upload PDFs and ask questions about them
- 🔍 **100% FREE Academic Search**: OpenAlex, CrossRef, PubMed, arXiv (no paid APIs!)
- 🤖 **Smart Agent**: Autonomously decides whether to search your PDFs or external sources
- 📝 **Citations**: Every answer includes precise citations with file names and page numbers
- 💬 **Discord Integration**: Per-user isolated storage, automatic PDF indexing
- 🔒 **Privacy**: Each user's PDFs are completely isolated

### NEW High-Priority Features ⭐
- 📜 **Conversation History**: Track all your questions and answers
- 📖 **Auto PDF Summaries**: Automatic summary generation on upload (overview, key findings, methodology, conclusions)
- 🎓 **Citation Export**: Export references in BibTeX, APA, MLA, Chicago, IEEE formats
- 🔎 **Advanced Search Filters**: Filter by year, author, venue
- 🆓 **Free Search Engines**: OpenAlex, CrossRef, PubMed, arXiv - all 100% free!

## 🚀 Quick Start

### 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp logs/.env.example .env
# Edit .env and add:
# - GOOGLE_API_KEY (required for Gemini)
# - DISCORD_TOKEN (required for Discord bot)
```

### 3. Run Discord Bot

```bash
python run_bot.py
```

### 4. Use the Bot

In Discord:
- **Upload PDFs**: Attach PDF files (auto-indexed with summary!)
- **Ask questions**: `!ask What is perceived inclusion?`
- **Free search with filters**: `!fsearch transformers --year-from 2020 --author "Vaswani"`
- **View PDF summary**: `!summarize my_paper.pdf`
- **View history**: `!history 10`
- **Export citations**: `!cite bibtex`
- **View stats**: `!stats`
- **Clear library**: `!clear`

## 🛠️ CLI Mode

```bash
# Index PDFs
python -m demo.cli --cmd index --corpus ./corpus

# Ask questions
python -m demo.cli --cmd ask --q "Your question here"
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Test specific components
python -m pytest tests/test_search_tools.py -v
python -m pytest tests/test_user_store.py -v
```

## 🔑 API Keys

- **GOOGLE_API_KEY**: Required for Gemini LLM and embeddings
- **DISCORD_TOKEN**: Required for Discord bot
- **SEMANTIC_SCHOLAR_API_KEY**: Optional, for higher rate limits

## 📦 Architecture

```
User Question
    ↓
LangChain Agent (Gemini)
    ↓
Chooses Tool:
├── retrieve (from user's PDFs)
├── summarize (from user's PDFs)
└── search_papers (Semantic Scholar + arXiv)
    ↓
Response with Citations
```

