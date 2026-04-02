"""
Memory Manager — Simple conversation buffer memory for chat history.
"""

import logging

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages conversation memory for the RAG system using a simple list."""

    def __init__(self):
        self._history = []

    def get_memory(self):
        """Return self for compatibility."""
        return self

    def save_context(self, inputs, outputs):
        """Save a new context item."""
        self._history.append({"input": inputs.get("input", ""), "output": outputs.get("output", "")})

    def clear_memory(self):
        """Clear all conversation history."""
        self._history = []
        logger.info("Conversation memory cleared")

    def get_chat_history(self):
        """Return the chat history as a list of dictionaries."""
        return self._history

