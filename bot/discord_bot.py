"""
Discord bot for academic research assistant.
Handles PDF uploads, user queries, and integrates with the LangChain agent.
"""
import os
import logging
import discord
from discord.ext import commands
from typing import Optional
import asyncio
import io
import difflib

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from agent.config import Settings
from agent.user_store_manager import UserStoreManager
from agent.tools_discord import create_user_tools
from agent.logging_conf import setup_logging
from agent.search_tools import search_papers as search_papers_tool  # Import with alias to avoid name collision
from agent.search_tools_enhanced import search_academic_papers_enhanced
from agent.conversation_manager import ConversationManager
from agent.citation_export import CitationManager, Citation
from agent.document_summarizer import DocumentSummarizer

log = logging.getLogger("discord_bot")


class ResearchBot(commands.Bot):
    """Discord bot for research assistance with per-user PDF management."""

    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None  # We'll create our own help command
        )

        self.settings = Settings()
        self.store_manager = UserStoreManager()
        self.conversation_manager = ConversationManager()
        self.citation_manager = CitationManager()
        self.summarizer = DocumentSummarizer()

    async def on_ready(self):
        """Called when bot is ready."""
        log.info(f"Bot logged in as {self.user.name} (ID: {self.user.id})")
        log.info(f"Connected to {len(self.guilds)} guild(s)")

    def _build_agent_for_user(self, user_id: str):
        """Build a LangChain agent for a specific user using LangChain 1.0+ API."""
        llm = ChatGoogleGenerativeAI(model=self.settings.llm_model, temperature=0)
        tools = create_user_tools(user_id)

        # Create agent using new API (returns CompiledStateGraph)
        return create_agent(
            model=llm,
            tools=tools,
            system_prompt="""You are a helpful research assistant. You MUST follow these rules:
1.  Your primary function is to answer questions using ONLY the user's uploaded PDF documents.
2.  You MUST use the `retrieve_passages` or `summarize_with_citations` tools to find all information.
3.  You may use the `search_academic_papers` tool if the user asks for external academic papers.
4.  **CRITICAL**: You MUST provide a specific citation for ALL information in your response.
5.  **DO NOT** use your general knowledge. If the answer is not in the user's documents, you MUST state that you cannot find the information in the provided documents."""
        )

    def _build_general_agent_for_user(self, user_id: str):
        """Build a general-purpose LangChain agent that intelligently searches both local and external sources."""
        llm = ChatGoogleGenerativeAI(model=self.settings.llm_model, temperature=0)
        tools = create_user_tools(user_id)

        # Create agent with intelligent fallback behavior
        return create_agent(
            model=llm,
            tools=tools,
            system_prompt="""You are an intelligent research assistant. Follow this decision process:

1. **Analyze the user's request** to understand what they need.

2. **Always try local PDFs first**:
   - Use `retrieve_passages` or `summarize_with_citations` to search the user's uploaded documents
   - If you find relevant information, provide it with proper citations

3. **Automatic external search fallback**:
   - If local PDFs return "No relevant passages found" or "No PDFs indexed yet"
   - OR if the user explicitly asks for external papers or recent research
   - THEN automatically use `search_academic_papers` to find information from academic databases

4. **Citation requirements**:
   - ALWAYS provide citations for ALL information
   - For local PDFs: use the citation format provided by the tools
   - For external papers: include title, authors, year, and source

5. **Be transparent**:
   - Tell the user whether information came from their local PDFs or external sources
   - If searching both, clearly separate the results

6. **Never use general knowledge**: Only use information from tools. If no information is found anywhere, clearly state that.

Your goal is to provide the best answer by intelligently combining local and external sources when appropriate."""
        )

    async def process_pdf_upload(self, message: discord.Message, attachment: discord.Attachment):
        """Process a PDF attachment from a user."""
        user_id = str(message.author.id)

        if not attachment.filename.lower().endswith('.pdf'):
            return

        try:
            # Download PDF
            pdf_bytes = await attachment.read()

            # Save PDF
            pdf_path = self.store_manager.save_pdf(
                user_id,
                pdf_bytes,
                attachment.filename
            )

            await message.add_reaction("📄")  # React to show we received it

            # Send processing message
            processing_msg = await message.reply(
                f"📚 Processing **{attachment.filename}**... This may take a moment."
            )

            # Build index
            loop = asyncio.get_event_loop()
            num_chunks = await loop.run_in_executor(
                None,
                self.store_manager.build_user_index,
                user_id
            )

            # Generate summary
            await processing_msg.edit(
                content=f"📚 Generating summary for **{attachment.filename}**..."
            )

            summary = await loop.run_in_executor(
                None,
                self.summarizer.generate_summary,
                pdf_path
            )

            # Get stats
            stats = self.store_manager.get_user_stats(user_id)

            # Format summary
            summary_text = self.summarizer.format_summary_for_display(summary)

            # Update message with summary
            await processing_msg.edit(
                content=f"✅ **{attachment.filename}** indexed successfully!\n\n"
                        f"📊 Your library: {stats['pdf_count']} PDF(s), "
                        f"{stats['total_size_mb']} MB, {num_chunks} chunks indexed.\n\n"
                        f"{summary_text[:1500]}\n\n"  # Truncate if too long
                        f"Use `!ask <your question>` to query this document!"
            )

        except Exception as e:
            log.error(f"Error processing PDF for user {user_id}: {e}", exc_info=True)
            await message.reply(f"❌ Error processing PDF: {str(e)}")

    async def on_message(self, message: discord.Message):
        """Handle incoming messages."""
        # Ignore bot's own messages
        if message.author.bot:
            return

        # Check for PDF attachments
        for attachment in message.attachments:
            if attachment.filename.lower().endswith('.pdf'):
                await self.process_pdf_upload(message, attachment)

        # Process commands
        await self.process_commands(message)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            # Extract the attempted command
            content = ctx.message.content
            if content.startswith('!'):
                attempted_command = content.split()[0]
                await ctx.reply(
                    f"❌ **Command not found**: `{attempted_command}`\n\n"
                    f"Available commands:\n"
                    f"• `!general` - Smart search (local + external)\n"
                    f"• `!ask` - Ask about your PDFs\n"
                    f"• `!search` - Search external papers\n"
                    f"• `!fsearch` - Free search with filters\n"
                    f"• `!summarize` - Get PDF summary\n"
                    f"• `!history` - View conversation history\n"
                    f"• `!cite` - Export citations\n"
                    f"• `!stats` - View library stats\n"
                    f"• `!clear` - Clear your library\n"
                    f"• `!help` - Show detailed help\n\n"
                    f"Type `!help` for more information."
                )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(
                f"❌ **Missing required argument**: {error.param.name}\n\n"
                f"Usage: `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`\n"
                f"Type `!help` for more information."
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.reply(
                f"❌ **Invalid argument**: {str(error)}\n\n"
                f"Type `!help` for more information."
            )
        else:
            # Log other errors
            log.error(f"Command error: {error}", exc_info=error)
            await ctx.reply(
                f"❌ **An error occurred**: {str(error)}\n\n"
                f"Please try again or contact support if the issue persists."
            )


def setup_commands(bot: ResearchBot):
    """Set up bot commands."""

    @bot.command(name="ask")
    async def ask_question(ctx: commands.Context, *, question: str):
        """
        Ask a question about your uploaded PDFs or search for papers.

        Usage: !ask <your question>
        Example: !ask What is perceived inclusion?
        """
        user_id = str(ctx.author.id)

        try:
            # Validate input
            if not question or question.strip() == "":
                await ctx.reply(
                    "❌ **Empty question detected**\n\n"
                    "Please provide a question.\n"
                    "Example: `!ask What is perceived inclusion?`"
                )
                return

            # Check if query is too short (less than 3 characters)
            if len(question.strip()) < 3:
                await ctx.reply(
                    "❌ **Question too short**\n\n"
                    "Please provide a more detailed question.\n"
                    "Example: `!ask What is perceived inclusion?`"
                )
                return

            # Check if user has PDFs
            stats = bot.store_manager.get_user_stats(user_id)

            # Send thinking message
            thinking_msg = await ctx.reply("🤔 Thinking...")

            # Build agent and run
            agent_graph = bot._build_agent_for_user(user_id)

            # Invoke with messages format
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                agent_graph.invoke,
                {"messages": [{"role": "user", "content": question}]}
            )

            # Extract the final AI message
            messages = result.get("messages", [])
            response = ""
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
                            response = '\n'.join(text_parts)
                        elif isinstance(content, str):
                            response = content
                        else:
                            response = str(content)
                        break
                if not response and hasattr(messages[-1], 'content'):
                    content = messages[-1].content
                    if isinstance(content, str):
                        response = content
                    else:
                        response = str(content)
            if not response:
                response = str(result)

            # Save conversation
            bot.conversation_manager.add_conversation(user_id, question, response)

            # Split response if too long (Discord limit is 2000 chars)
            if len(response) > 1900:
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                await thinking_msg.edit(content=chunks[0])
                for chunk in chunks[1:]:
                    await ctx.send(chunk)
            else:
                await thinking_msg.edit(content=response)

        except Exception as e:
            log.error(f"Error processing question for user {user_id}: {e}", exc_info=True)
            await ctx.reply(f"❌ Error: {str(e)}")

    @bot.command(name="general")
    async def general_query(ctx: commands.Context, *, query: str):
        """
        General-purpose query that intelligently searches both local PDFs and external sources.
        The agent will first try your PDFs, then automatically search external sources if needed.

        Also supports natural language command routing:
        - "clear my data" → routes to !clear
        - "show my stats" → routes to !stats
        - "show help" → routes to !help
        - "show history" → routes to !history

        Usage: !general <your question or request>
        Example: !general What is machine learning?
        Example: !general Tell me about perceived inclusion
        Example: !general clear my data
        Example: !general show my stats
        """
        user_id = str(ctx.author.id)

        try:
            # Validate input
            if not query or query.strip() == "":
                await ctx.reply(
                    "❌ **Empty query detected**\n\n"
                    "Please provide a question or request.\n"
                    "Example: `!general What is machine learning?`"
                )
                return

            # Check if query is too short (less than 3 characters)
            if len(query.strip()) < 3:
                await ctx.reply(
                    "❌ **Query too short**\n\n"
                    "Please provide a more detailed question.\n"
                    "Example: `!general What is machine learning?`"
                )
                return

            # Intent detection - route to specific commands if detected
            # This allows natural language commands via !general
            query_lower = query.lower().strip()

            # Check for clear/delete data intent
            if any(pattern in query_lower for pattern in [
                'clear my data', 'delete my data', 'clear data', 'delete data',
                'clear library', 'delete library', 'clear pdfs', 'delete pdfs',
                'remove my data', 'erase my data', 'clear everything', 'reset my data'
            ]):
                await ctx.reply("🔄 Detected clear intent → routing to `!clear` command...")
                await clear_library(ctx)
                return

            # Check for stats intent
            if any(pattern in query_lower for pattern in [
                'show stats', 'show my stats', 'library stats', 'my library',
                'how many pdfs', 'what pdfs', 'list pdfs', 'show pdfs',
                'my pdfs', 'check stats', 'view stats'
            ]) and len(query_lower.split()) <= 6:  # Short queries only
                await ctx.reply("🔄 Detected stats intent → routing to `!stats` command...")
                await show_stats(ctx)
                return

            # Check for help intent
            if any(pattern in query_lower for pattern in [
                'show help', 'show commands', 'list commands', 'available commands',
                'what commands', 'how to use', 'show usage', 'help me'
            ]) and len(query_lower.split()) <= 6:
                await ctx.reply("🔄 Detected help intent → routing to `!help` command...")
                await show_help(ctx)
                return

            # Check for history intent
            if any(pattern in query_lower for pattern in [
                'show history', 'my history', 'conversation history', 'view history',
                'past conversations', 'previous questions'
            ]) and len(query_lower.split()) <= 6:
                await ctx.reply("🔄 Detected history intent → routing to `!history` command...")
                await show_history(ctx)
                return

            # Send thinking message
            thinking_msg = await ctx.reply("🤔 Analyzing your request...")

            # Build general agent and run
            agent_graph = bot._build_general_agent_for_user(user_id)

            # Invoke with messages format
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                agent_graph.invoke,
                {"messages": [{"role": "user", "content": query}]}
            )

            # Extract the final AI message
            messages = result.get("messages", [])
            response = ""
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
                            response = '\n'.join(text_parts)
                        elif isinstance(content, str):
                            response = content
                        else:
                            response = str(content)
                        break
                if not response and hasattr(messages[-1], 'content'):
                    content = messages[-1].content
                    if isinstance(content, str):
                        response = content
                    else:
                        response = str(content)
            if not response:
                response = str(result)

            # Check if response is empty or indicates agent couldn't understand
            if not response or response.strip() == "":
                await thinking_msg.edit(
                    content="❌ **I couldn't generate a response**\n\n"
                    "This might be because:\n"
                    "• Your query was unclear\n"
                    "• No relevant information was found\n"
                    "• There was an issue processing your request\n\n"
                    "Try:\n"
                    "• Rephrasing your question more clearly\n"
                    "• Being more specific\n"
                    "• Using `!help` to see example queries"
                )
                return

            # Check for common agent confusion patterns
            confusion_patterns = [
                "i don't understand",
                "i cannot understand",
                "unclear what you",
                "please clarify",
                "i'm not sure what you mean"
            ]

            response_lower = response.lower()
            if any(pattern in response_lower for pattern in confusion_patterns):
                await thinking_msg.edit(
                    content=f"🤷 **I had trouble understanding your request**\n\n"
                    f"Agent response: {response}\n\n"
                    f"**Suggestions:**\n"
                    f"• Try rephrasing your question more clearly\n"
                    f"• Be more specific about what you want to know\n"
                    f"• Use `!help` to see example queries\n\n"
                    f"**Examples:**\n"
                    f"• `!general What is machine learning?`\n"
                    f"• `!general Explain the concept of RAG`\n"
                    f"• `!general Find papers about transformers`"
                )
                return

            # Save conversation
            bot.conversation_manager.add_conversation(user_id, query, response)

            # Split response if too long (Discord limit is 2000 chars)
            if len(response) > 1900:
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                await thinking_msg.edit(content=chunks[0])
                for chunk in chunks[1:]:
                    await ctx.send(chunk)
            else:
                await thinking_msg.edit(content=response)

        except Exception as e:
            log.error(f"Error processing general query for user {user_id}: {e}", exc_info=True)
            await ctx.reply(
                f"❌ **An error occurred while processing your request**\n\n"
                f"Error details: {str(e)}\n\n"
                f"**What you can do:**\n"
                f"• Try again with a different query\n"
                f"• Check if your PDFs are properly uploaded (`!stats`)\n"
                f"• Use simpler queries\n"
                f"• Contact support if the issue persists\n\n"
                f"Type `!help` for more information."
            )

    @bot.command(name="search")
    async def search_papers(ctx: commands.Context, *, query: str):
        """
        Search for academic papers on Semantic Scholar, arXiv, and Google.

        Usage: !search <search query>
        Example: !search transformer attention mechanisms
        """
        try:
            # Validate input
            if not query or query.strip() == "":
                await ctx.reply(
                    "❌ **Empty search query**\n\n"
                    "Please provide a search query.\n"
                    "Example: `!search transformer attention mechanisms`"
                )
                return

            if len(query.strip()) < 3:
                await ctx.reply(
                    "❌ **Search query too short**\n\n"
                    "Please provide a more detailed search query.\n"
                    "Example: `!search transformer attention mechanisms`"
                )
                return

            thinking_msg = await ctx.reply("🔍 Searching academic databases...")

            # Search papers using non-decorated function
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, search_papers_tool, query)

            # Ensure results is a string
            if not isinstance(results, str):
                results = str(results)

            # Split if needed
            if len(results) > 1900:
                chunks = [results[i:i+1900] for i in range(0, len(results), 1900)]
                await thinking_msg.edit(content=chunks[0])
                for chunk in chunks[1:]:
                    await ctx.send(chunk)
            else:
                await thinking_msg.edit(content=results)

        except Exception as e:
            log.error(f"Error searching papers: {e}", exc_info=True)
            await ctx.reply(f"❌ Error: {str(e)}")

    @bot.command(name="stats")
    async def show_stats(ctx: commands.Context):
        """
        Show your library statistics.

        Usage: !stats
        """
        user_id = str(ctx.author.id)

        try:
            stats = bot.store_manager.get_user_stats(user_id)

            if stats['pdf_count'] == 0:
                await ctx.reply(
                    "📚 Your library is empty.\n\n"
                    "Upload PDFs by attaching them to a message, then use `!ask` to query them!"
                )
                return

            pdfs_list = "\n".join(f"  • {name}" for name in stats['pdf_names'])

            message = (
                f"📊 **Your Library Stats**\n\n"
                f"📄 PDFs: {stats['pdf_count']}\n"
                f"💾 Total size: {stats['total_size_mb']} MB\n"
                f"🔍 Indexed: {'✅ Yes' if stats['has_index'] else '❌ No'}\n\n"
                f"**Your PDFs:**\n{pdfs_list}"
            )

            await ctx.reply(message)

        except Exception as e:
            log.error(f"Error getting stats: {e}", exc_info=True)
            await ctx.reply(f"❌ Error: {str(e)}")

    @bot.command(name="clear")
    async def clear_library(ctx: commands.Context):
        """
        Clear all your uploaded PDFs and index.

        Usage: !clear
        """
        user_id = str(ctx.author.id)

        try:
            # Ask for confirmation
            confirm_msg = await ctx.reply(
                "⚠️ **Warning**: This will delete all your uploaded PDFs and index.\n"
                "React with ✅ to confirm or ❌ to cancel."
            )
            await confirm_msg.add_reaction("✅")
            await confirm_msg.add_reaction("❌")

            def check(reaction, user):
                return (
                    user == ctx.author and
                    str(reaction.emoji) in ["✅", "❌"] and
                    reaction.message.id == confirm_msg.id
                )

            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)

                if str(reaction.emoji) == "✅":
                    success = bot.store_manager.clear_user_data(user_id)
                    if success:
                        await ctx.send("🗑️ Your library has been cleared.")
                    else:
                        await ctx.send("ℹ️ Your library was already empty.")
                else:
                    await ctx.send("❌ Cancelled.")

            except asyncio.TimeoutError:
                await ctx.send("⏱️ Confirmation timeout. Clear cancelled.")

        except Exception as e:
            log.error(f"Error clearing library: {e}", exc_info=True)
            await ctx.reply(f"❌ Error: {str(e)}")

    @bot.command(name="history")
    async def show_history(ctx: commands.Context, limit: int = 10):
        """
        Show your conversation history.

        Usage: !history [limit]
        Example: !history 5
        """
        user_id = str(ctx.author.id)

        try:
            history_text = bot.conversation_manager.format_history(user_id, limit=limit)

            # Split if too long
            if len(history_text) > 1900:
                chunks = [history_text[i:i+1900] for i in range(0, len(history_text), 1900)]
                await ctx.reply(chunks[0])
                for chunk in chunks[1:]:
                    await ctx.send(chunk)
            else:
                await ctx.reply(history_text)

        except Exception as e:
            log.error(f"Error showing history: {e}", exc_info=True)
            await ctx.reply(f"❌ Error: {str(e)}")

    @bot.command(name="summarize")
    async def summarize_pdf(ctx: commands.Context, *, pdf_name: Optional[str] = None):
        """
        Get a summary of a specific PDF or the most recent one.

        Usage: !summarize [pdf_name]
        Example: !summarize my_paper.pdf
        """
        user_id = str(ctx.author.id)

        try:
            if pdf_name:
                # Find specific PDF
                pdfs = bot.store_manager.get_user_pdfs(user_id)
                matching_pdf = None
                for pdf in pdfs:
                    if pdf_name.lower() in pdf.lower():
                        matching_pdf = pdf
                        break

                if not matching_pdf:
                    await ctx.reply(f"❌ PDF '{pdf_name}' not found. Use `!stats` to see your PDFs.")
                    return

                pdf_path = matching_pdf
            else:
                # Use most recent PDF
                pdfs = bot.store_manager.get_user_pdfs(user_id)
                if not pdfs:
                    await ctx.reply("❌ No PDFs uploaded yet.")
                    return
                pdf_path = max(pdfs, key=os.path.getmtime)

            # Check if summary exists
            summary = bot.summarizer.get_summary(os.path.basename(pdf_path))

            if not summary:
                # Generate new summary
                thinking_msg = await ctx.reply("📝 Generating summary...")
                loop = asyncio.get_event_loop()
                summary = await loop.run_in_executor(
                    None,
                    bot.summarizer.generate_summary,
                    pdf_path
                )
                await thinking_msg.delete()

            # Format and send
            summary_text = bot.summarizer.format_summary_for_display(summary)

            if len(summary_text) > 1900:
                chunks = [summary_text[i:i+1900] for i in range(0, len(summary_text), 1900)]
                await ctx.reply(chunks[0])
                for chunk in chunks[1:]:
                    await ctx.send(chunk)
            else:
                await ctx.reply(summary_text)

        except Exception as e:
            log.error(f"Error summarizing PDF: {e}", exc_info=True)
            await ctx.reply(f"❌ Error: {str(e)}")

    @bot.command(name="cite")
    async def export_citations(ctx: commands.Context, format_type: str = "apa"):
        """
        Export citations from your recent searches in various formats.

        Usage: !cite [format]
        Formats: apa, mla, chicago, bibtex, ieee
        Example: !cite bibtex
        """
        user_id = str(ctx.author.id)

        try:
            # Get recent conversations
            history = bot.conversation_manager.get_history(user_id, limit=5)

            if not history:
                await ctx.reply("❌ No search history found.")
                return

            # Extract citations from history
            all_text = "\n".join([conv.get('answer', '') for conv in history])
            citations = bot.citation_manager.extract_from_text(all_text)

            if not citations:
                await ctx.reply("❌ No citations found in recent conversations.")
                return

            # Format bibliography
            bibliography = bot.citation_manager.format_bibliography(citations, format_type)

            # Split if needed
            if len(bibliography) > 1900:
                chunks = [bibliography[i:i+1900] for i in range(0, len(bibliography), 1900)]
                await ctx.reply(f"📚 **Bibliography ({format_type.upper()})**:\n\n{chunks[0]}")
                for chunk in chunks[1:]:
                    await ctx.send(chunk)
            else:
                await ctx.reply(f"📚 **Bibliography ({format_type.upper()})**:\n\n{bibliography}")

        except Exception as e:
            log.error(f"Error exporting citations: {e}", exc_info=True)
            await ctx.reply(f"❌ Error: {str(e)}")

    @bot.command(name="fsearch")
    async def free_search(ctx: commands.Context, *, args: str):
        """
        Enhanced free search with filters (OpenAlex, CrossRef, PubMed, arXiv).

        Usage: !fsearch <query> [--year-from YYYY] [--year-to YYYY] [--author "Name"]
        Example: !fsearch machine learning --year-from 2020 --year-to 2024
        Example: !fsearch transformers --author "Vaswani"
        """
        try:
            # Validate input
            if not args or args.strip() == "":
                await ctx.reply(
                    "❌ **Empty search query**\n\n"
                    "Please provide a search query.\n"
                    "Example: `!fsearch machine learning --year-from 2020`"
                )
                return

            # Parse arguments
            import shlex
            parts = shlex.split(args)

            query = []
            year_from = None
            year_to = None
            author = None

            i = 0
            while i < len(parts):
                if parts[i] == "--year-from" and i + 1 < len(parts):
                    year_from = int(parts[i + 1])
                    i += 2
                elif parts[i] == "--year-to" and i + 1 < len(parts):
                    year_to = int(parts[i + 1])
                    i += 2
                elif parts[i] == "--author" and i + 1 < len(parts):
                    author = parts[i + 1]
                    i += 2
                else:
                    query.append(parts[i])
                    i += 1

            query_str = " ".join(query)

            if not query_str:
                await ctx.reply("❌ Please provide a search query.")
                return

            thinking_msg = await ctx.reply("🔍 Searching free academic databases...")

            # Search using enhanced search
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                search_academic_papers_enhanced,
                query_str,
                ['openalex', 'crossref', 'pubmed', 'arxiv'],  # sources
                year_from,
                year_to,
                author
            )

            # Split if needed
            if len(results) > 1900:
                chunks = [results[i:i+1900] for i in range(0, len(results), 1900)]
                await thinking_msg.edit(content=chunks[0])
                for chunk in chunks[1:]:
                    await ctx.send(chunk)
            else:
                await thinking_msg.edit(content=results)

        except Exception as e:
            log.error(f"Error in free search: {e}", exc_info=True)
            await ctx.reply(f"❌ Error: {str(e)}")

    @bot.command(name="help")
    async def show_help(ctx: commands.Context):
        """Show help message."""
        help_text = """
📚 **Research Assistant Bot - Help**

**Upload PDFs:**
Simply attach PDF files to any message. Auto-indexed with summary!

**Commands:**

`!general <query>` ⭐ NEW!
Smart query that automatically searches your PDFs first, then external sources if needed.
Supports natural language commands!
Examples:
  • `!general What is machine learning?`
  • `!general clear my data` → routes to !clear
  • `!general show my stats` → routes to !stats
  • `!general show help` → routes to !help
  • `!general show history` → routes to !history

`!ask <question>`
Ask questions about your PDFs or search for papers.

`!search <query>`
Search Semantic Scholar and arXiv.

`!fsearch <query> [--year-from YYYY] [--year-to YYYY] [--author "Name"]`
Enhanced FREE search (OpenAlex, CrossRef, PubMed, arXiv) with filters.
Example: `!fsearch transformers --year-from 2020`

`!summarize [pdf_name]`
Get summary of a PDF (auto-generated on upload).

`!history [limit]`
View your conversation history.

`!cite [format]`
Export citations (apa, mla, chicago, bibtex, ieee).

`!stats`
View your library statistics.

`!clear`
Delete all your PDFs and data.

`!help`
Show this message.

**Features:**
✅ Auto PDF summary on upload
✅ Conversation history tracking
✅ Citation export in multiple formats
✅ 100% FREE academic search engines
✅ Advanced search filters (year, author)
✅ Intelligent local + external search
"""
        await ctx.reply(help_text)


def run_bot():
    """Main function to run the Discord bot."""
    setup_logging()

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        log.error("DISCORD_TOKEN not found in environment variables!")
        return

    bot = ResearchBot()
    setup_commands(bot)

    log.info("Starting Discord bot...")
    bot.run(token)


if __name__ == "__main__":
    run_bot()
