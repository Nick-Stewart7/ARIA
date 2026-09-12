"""ARIA package.

Loads the project's .env here so every entry point -- `aria serve`, `aria
chat`, a one-off script that imports aria.history -- sees the same
configuration before any module reads MEMORY_DIR, SESSION_DIR, and friends.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
