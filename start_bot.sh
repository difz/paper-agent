#!/bin/bash
# Discord Bot Startup Script
# This script ensures the bot runs with the correct Python environment

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found at .venv/"
    echo "Please run: python -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Check if ChromaDB is installed
if ! .venv/bin/python -c "import chromadb" 2>/dev/null; then
    echo "Warning: ChromaDB not found in virtual environment"
    echo "Installing dependencies..."
    .venv/bin/pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found"
    echo "Please create .env file with DISCORD_TOKEN and GOOGLE_API_KEY"
    exit 1
fi

echo "Starting Discord bot..."
echo "Using Python: $(which .venv/bin/python)"
echo "ChromaDB version: $(.venv/bin/python -c 'import chromadb; print(chromadb.__version__)')"

# Check if bot is already running
if pgrep -f "python.*run_bot.py" > /dev/null; then
    echo ""
    echo "WARNING: Bot is already running!"
    echo "Existing processes:"
    ps aux | grep "[p]ython.*run_bot"
    echo ""
    read -p "Kill existing processes and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping existing bot processes..."
        pkill -f "python.*run_bot.py"
        sleep 2
    else
        echo "Aborted. Keeping existing bot process."
        exit 0
    fi
fi

# Run bot
echo "Starting bot..."
echo ""
echo "Options:"
echo "  Press Ctrl+C to stop the bot"
echo "  Logs are also saved to bot.log"
echo ""
echo "==================== BOT LOGS ===================="
echo ""

# Run in foreground so you can see logs
.venv/bin/python run_bot.py 2>&1 | tee bot.log
