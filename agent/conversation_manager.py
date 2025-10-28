"""
Conversation history manager for maintaining context across queries.
Stores per-user conversation history with timestamps and citations.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

log = logging.getLogger("conversation_manager")


class ConversationManager:
    """Manages conversation history for users."""

    def __init__(self, base_dir: str = "./store/conversations"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_file(self, user_id: str) -> Path:
        """Get the conversation file path for a user."""
        user_file = self.base_dir / f"user_{user_id}.json"
        return user_file

    def add_conversation(self, user_id: str, question: str, answer: str,
                        sources: Optional[List[str]] = None):
        """
        Add a conversation turn to history.

        Args:
            user_id: User identifier
            question: User's question
            answer: Agent's answer
            sources: List of sources/citations used
        """
        user_file = self._get_user_file(user_id)

        # Load existing history
        if user_file.exists():
            with open(user_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = {"user_id": user_id, "conversations": []}

        # Add new conversation
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "sources": sources or []
        }
        history["conversations"].append(conversation)

        # Save
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        log.info(f"Saved conversation for user {user_id}")

    def get_history(self, user_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get conversation history for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of recent conversations to return

        Returns:
            List of conversation dictionaries
        """
        user_file = self._get_user_file(user_id)

        if not user_file.exists():
            return []

        with open(user_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

        conversations = history.get("conversations", [])

        if limit:
            conversations = conversations[-limit:]

        return conversations

    def get_recent_context(self, user_id: str, num_turns: int = 3) -> str:
        """
        Get recent conversation context as formatted string.

        Args:
            user_id: User identifier
            num_turns: Number of recent turns to include

        Returns:
            Formatted context string
        """
        history = self.get_history(user_id, limit=num_turns)

        if not history:
            return ""

        context_parts = []
        for conv in history:
            context_parts.append(f"Q: {conv['question']}")
            context_parts.append(f"A: {conv['answer'][:200]}...")  # Truncate long answers

        return "\n".join(context_parts)

    def clear_history(self, user_id: str) -> bool:
        """
        Clear conversation history for a user.

        Args:
            user_id: User identifier

        Returns:
            True if successful
        """
        user_file = self._get_user_file(user_id)

        if user_file.exists():
            user_file.unlink()
            log.info(f"Cleared conversation history for user {user_id}")
            return True

        return False

    def format_history(self, user_id: str, limit: int = 10) -> str:
        """
        Format conversation history for display.

        Args:
            user_id: User identifier
            limit: Number of recent conversations

        Returns:
            Formatted string for Discord display
        """
        history = self.get_history(user_id, limit=limit)

        if not history:
            return "No conversation history found."

        lines = [f"📜 **Your Recent Conversations** (last {len(history)}):\n"]

        for i, conv in enumerate(history, 1):
            timestamp = datetime.fromisoformat(conv['timestamp'])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M")

            lines.append(f"**{i}. {time_str}**")
            lines.append(f"❓ Q: {conv['question']}")

            # Truncate long answers
            answer = conv['answer']
            if len(answer) > 150:
                answer = answer[:150] + "..."

            lines.append(f"💡 A: {answer}")

            if conv.get('sources'):
                lines.append(f"📚 Sources: {len(conv['sources'])}")

            lines.append("")  # Empty line

        return "\n".join(lines)

    def get_all_sources(self, user_id: str) -> List[str]:
        """
        Get all unique sources cited in user's conversations.

        Args:
            user_id: User identifier

        Returns:
            List of unique source identifiers
        """
        history = self.get_history(user_id)

        all_sources = set()
        for conv in history:
            all_sources.update(conv.get('sources', []))

        return sorted(list(all_sources))

    def search_history(self, user_id: str, query: str) -> List[Dict]:
        """
        Search conversation history for specific topics.

        Args:
            user_id: User identifier
            query: Search query

        Returns:
            List of matching conversations
        """
        history = self.get_history(user_id)

        query_lower = query.lower()
        matches = []

        for conv in history:
            if (query_lower in conv['question'].lower() or
                query_lower in conv['answer'].lower()):
                matches.append(conv)

        return matches
