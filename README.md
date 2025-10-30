# Research Assistant Agent
Dibuat oleh:
- Muhammad Hifzhon Harundoyo (22/487269/TK/54647)
- Muhammad Budi Setiawan (22/505064/TK/55254)

# Description
Sebuah Bot yang berguna untuk membantu peneliti dalam menemukan, merangkum, dan melakukan sitasi jurnal untuk memudahkan dalam penulisan.  Dengan menggunakan LLM Agent yang dikombinasikan dengan berbagai tools serta terintegrasi dengan discord, bot ini siap untuk membantu peneliti dalam melakukan penelitiannya.

## ✨ Fitur

### Fitur Inti
- 📚 Analisis PDF: Unggah file PDF dan ajukan pertanyaan langsung tentang isinya.
- 🔍 Pencarian Akademik 100% Gratis: Terhubung dengan OpenAlex, CrossRef, PubMed, dan arXiv.
- 🤖 Agen Cerdas: Melakukan pencarian otomatis dari sumber internal (PDF lokal) maupun eksternal.
- 🧠 Kueri Umum Cerdas (BARU!): Secara otomatis mencari di PDF lokal terlebih dahulu, lalu ke sumber eksternal jika diperlukan.
- 📝 Sitasi: Setiap jawaban dilengkapi dengan sitasi yang akurat, mencakup nama file dan nomor halaman.
- 💬 Integrasi Discord: Penyimpanan terpisah per pengguna dan pengindeksan PDF otomatis.

### Fitur Prioritas Baru ⭐
- 📜 Riwayat Percakapan: Melacak seluruh pertanyaan dan jawaban Anda.
- 📖 Ringkasan Otomatis PDF: Membuat ringkasan otomatis saat file diunggah (termasuk gambaran umum, temuan utama, metodologi, dan kesimpulan).
- 🎓 Ekspor Sitasi: Ekspor referensi dalam format BibTeX, APA, MLA, Chicago, atau IEEE.
- 🔎 Filter Pencarian Lanjutan: Memfilter hasil berdasarkan tahun, penulis, atau tempat publikasi.
- 🆓 Mesin Pencari Gratis: OpenAlex, CrossRef, PubMed, dan arXiv — semuanya gratis!
- 🛡️ Penanganan Kesalahan Lengkap: Pesan kesalahan yang informatif dan memberikan saran saat perintah gagal atau agen tidak memahami permintaan.

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

