# Research Assistant Agent

A RAG (Retrieval-Augmented Generation) agent that helps researchers find relevant passages, synthesize answers, and ground every claim with real citations from PDFs. Integrates with Discord for easy collaboration and includes multi-source academic search.

## ✨ Features

### Core Features
- 📚 **PDF Analysis**: Upload PDFs and ask questions about them
- 🔍 **100% FREE Academic Search**: OpenAlex, CrossRef, PubMed, arXiv (no paid APIs!)
- 🤖 **Smart Agent**: Autonomously decides whether to search your PDFs or external sources
- 🧠 **Intelligent General Query (NEW!)**: Automatically searches local PDFs first, then falls back to external sources if needed
- 📝 **Citations**: Every answer includes precise citations with file names and page numbers
- 💬 **Discord Integration**: Per-user isolated storage, automatic PDF indexing
- 🔒 **Privacy**: Each user's PDFs are completely isolated

### NEW High-Priority Features ⭐
- 📜 **Conversation History**: Track all your questions and answers
- 📖 **Auto PDF Summaries**: Automatic summary generation on upload (overview, key findings, methodology, conclusions)
- 🎓 **Citation Export**: Export references in BibTeX, APA, MLA, Chicago, IEEE formats
- 🔎 **Advanced Search Filters**: Filter by year, author, venue
- 🆓 **Free Search Engines**: OpenAlex, CrossRef, PubMed, arXiv - all 100% free!
- 🛡️ **Comprehensive Error Handling**: Helpful error messages with suggestions when commands fail or agent can't understand

### 🆕 Latest Updates
- ✅ **Fixed Database Errors**: Resolved "readonly database" issues by ensuring proper virtual environment usage
- ✅ **Fixed Double Replies**: Startup script now prevents multiple bot instances
- ✅ **Real-time Logs**: New `start_bot.sh` script shows logs in terminal with automatic environment checks
- ✅ **Enhanced Troubleshooting**: Added comprehensive troubleshooting guide for common issues

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

**IMPORTANT**: Always use the startup script to ensure proper environment:

```bash
# Start the bot with real-time logs (recommended)
./start_bot.sh

# The script will:
# ✅ Check virtual environment exists
# ✅ Verify ChromaDB is installed
# ✅ Prevent multiple bot instances (fixes double replies)
# ✅ Show logs in real-time
# ✅ Save logs to bot.log

# Press Ctrl+C to stop the bot
```

**Alternative methods** (manual):
```bash
# Option 1: Activate virtual environment first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python run_bot.py

# Option 2: Use venv Python directly
.venv/bin/python run_bot.py
```

**⚠️ Common Issues:**
- **Database errors**: Running with system Python instead of `.venv/bin/python`
- **Double replies**: Multiple bot instances running (use startup script to prevent)
- **No ChromaDB**: Dependencies not installed in virtual environment

### 4. Stop the Bot

```bash
# If running with ./start_bot.sh:
# Press Ctrl+C in the terminal

# If running in background, kill the process:
pkill -f "python.*run_bot.py"

# Check if bot is still running:
ps aux | grep run_bot
```

### 5. Use the Bot

In Discord:
- **Upload PDFs**: Attach PDF files (auto-indexed with summary!)
- **General query (NEW!)**: `!general What is machine learning?` - Intelligently searches your PDFs first, then external sources automatically
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

