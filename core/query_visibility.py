"""
Query Visibility — Manages message visibility (local vs group) for shared notebooks.
Uses JSON file per notebook for message persistence.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from config.settings import DATA_DIR

logger = logging.getLogger(__name__)

MESSAGES_DIR = DATA_DIR / "messages"


class QueryVisibilityManager:
    """Manages persisted messages with visibility controls."""

    def __init__(self):
        MESSAGES_DIR.mkdir(parents=True, exist_ok=True)

    def _get_messages_path(self, notebook_id: str) -> Path:
        return MESSAGES_DIR / f"{notebook_id}_messages.json"

    def _load_messages(self, notebook_id: str) -> list:
        path = self._get_messages_path(notebook_id)
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_messages(self, notebook_id: str, messages: list):
        path = self._get_messages_path(notebook_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)

    def save_message(self, notebook_id: str, user_id: str, role: str,
                     content: str, sources: list = None, visibility: str = "group"):
        """Save a message with visibility metadata."""
        messages = self._load_messages(notebook_id)
        messages.append({
            "user_id": user_id,
            "role": role,
            "content": content,
            "sources": sources or [],
            "visibility": visibility,  # "local" or "group"
            "timestamp": datetime.now().strftime("%H:%M"),
            "date": datetime.now().isoformat(),
        })
        self._save_messages(notebook_id, messages)

    def get_visible_messages(self, notebook_id: str, user_id: str) -> list:
        """Get messages visible to a specific user."""
        messages = self._load_messages(notebook_id)
        visible = []
        for msg in messages:
            if msg["visibility"] == "group":
                visible.append(msg)
            elif msg["user_id"] == user_id:
                visible.append(msg)
        return visible

    def clear_messages(self, notebook_id: str, user_id: str = None):
        """Clear messages for a notebook. If user_id given, only clear that user's local messages."""
        if user_id:
            messages = self._load_messages(notebook_id)
            messages = [m for m in messages if not (m["user_id"] == user_id and m["visibility"] == "local")]
            self._save_messages(notebook_id, messages)
        else:
            path = self._get_messages_path(notebook_id)
            if path.exists():
                path.unlink()

    def delete_notebook_messages(self, notebook_id: str):
        """Delete all messages for a notebook."""
        path = self._get_messages_path(notebook_id)
        if path.exists():
            path.unlink()
