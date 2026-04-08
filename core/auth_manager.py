"""
Auth Manager — JSON-based user authentication (no SQLite needed).
Uses hashlib for password hashing (built-in Python).
Stores users in data/users.json
"""

import json
import uuid
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from config.settings import DATA_DIR

logger = logging.getLogger(__name__)

USERS_FILE = DATA_DIR / "users.json"


class AuthManager:
    """Manages user authentication using JSON file storage."""

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not USERS_FILE.exists():
            self._save_users({})

    def _load_users(self) -> dict:
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_users(self, users: dict):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _hash_password(password: str, salt: str = None) -> tuple:
        """Hash password with salt using SHA-256."""
        if salt is None:
            salt = uuid.uuid4().hex[:16]
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        return hashed, salt

    def register(self, username: str, display_name: str, password: str) -> tuple:
        """
        Register a new user.
        Returns: (success: bool, message: str, user_id: str|None)
        """
        users = self._load_users()

        # Check if username exists
        for uid, user in users.items():
            if user["username"].lower() == username.lower():
                return False, "Username already exists", None

        if len(username) < 3:
            return False, "Username must be at least 3 characters", None
        if len(password) < 4:
            return False, "Password must be at least 4 characters", None

        user_id = uuid.uuid4().hex[:12]
        hashed, salt = self._hash_password(password)

        users[user_id] = {
            "username": username,
            "display_name": display_name or username,
            "password_hash": hashed,
            "salt": salt,
            "created_at": datetime.now().isoformat(),
        }

        self._save_users(users)
        logger.info(f"New user registered: {username} (ID: {user_id})")
        return True, "Registration successful!", user_id

    def login(self, username: str, password: str) -> tuple:
        """
        Authenticate a user.
        Returns: (success: bool, message: str, user_data: dict|None)
        """
        users = self._load_users()

        for uid, user in users.items():
            if user["username"].lower() == username.lower():
                hashed, _ = self._hash_password(password, user["salt"])
                if hashed == user["password_hash"]:
                    user_data = {
                        "user_id": uid,
                        "username": user["username"],
                        "display_name": user["display_name"],
                    }
                    logger.info(f"User logged in: {username}")
                    return True, "Login successful!", user_data
                else:
                    return False, "Incorrect password", None

        return False, "Username not found", None

    def get_all_users(self) -> list:
        """Get list of all users (for sharing notebooks)."""
        users = self._load_users()
        return [
            {"user_id": uid, "username": u["username"], "display_name": u["display_name"]}
            for uid, u in users.items()
        ]

    def get_user(self, user_id: str) -> dict | None:
        """Get user data by ID."""
        users = self._load_users()
        user = users.get(user_id)
        if user:
            return {
                "user_id": user_id,
                "username": user["username"],
                "display_name": user["display_name"],
            }
        return None

    # ── Session Persistence (survive page refresh) ──

    SESSION_FILE = DATA_DIR / "session.json"

    def save_session(self, user_data: dict):
        """Save active session to disk so login survives refresh."""
        try:
            with open(self.SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "user_data": user_data,
                    "timestamp": datetime.now().isoformat(),
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")

    def load_session(self) -> dict | None:
        """Load saved session from disk. Returns user_data or None."""
        try:
            if self.SESSION_FILE.exists():
                with open(self.SESSION_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                user_data = data.get("user_data")
                if user_data and user_data.get("user_id"):
                    # Verify user still exists
                    if self.get_user(user_data["user_id"]):
                        return user_data
        except Exception as e:
            logger.warning(f"Failed to load session: {e}")
        return None

    def clear_session(self):
        """Clear saved session (logout)."""
        try:
            if self.SESSION_FILE.exists():
                self.SESSION_FILE.unlink()
        except Exception as e:
            logger.warning(f"Failed to clear session: {e}")
