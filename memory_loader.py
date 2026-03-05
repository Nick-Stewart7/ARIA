from pathlib import Path

_ROOT = Path(__file__).parent

FILE_SYSTEM_ARCHITECTURE = f"""
## File System
- Artifacts: {_ROOT / "artifacts"}
- Journal: {_ROOT / "journal"}
- Memory: {_ROOT / "memory"}
- Tasks: {_ROOT / "memory" / "tasks.md"}
"""


def load_identity() -> str:
    """Load ARIA's core identity from memory/identity/ARIA.md."""
    path = _ROOT / "memory" / "identity" / "ARIA.md"
    return path.read_text() if path.exists() else ""


def load_user_context(user_id: str) -> str:
    """Load per-user context from memory/users/{user_id}.md."""
    path = _ROOT / "memory" / "users" / f"{user_id}.md"
    return path.read_text() if path.exists() else ""
