from pathlib import Path
import os
from aria.memory_manager import MemoryManager


from aria.subagents.narrative_writer import narrative_agent

ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "artifacts"))
MEMORY_DIR = Path(os.getenv("MEMORY_DIR", "memory"))
JOURNAL_DIR = Path(os.getenv("JOURNAL_DIR", "journal"))

FILE_SYSTEM_ARCHITECTURE = f"""
Here is a list of files present in your directory.
## File System
- Artifacts: {ARTIFACTS_DIR}
- Journal: {JOURNAL_DIR}
- Memory: {MEMORY_DIR}
"""


def load_identity() -> str:
    """Load ARIA's core identity from memory/identity/ARIA.md."""
    path = Path(os.getenv("IDENTITY_FILE", MEMORY_DIR / "identity" / "ARIA.md"))
    return path.read_text() if path.exists() else ""


def load_user_context(user_id: str) -> str:
    """Load per-user context from memory/users/{user_id}.md."""
    path = Path(os.getenv("USER_CONTEXT_DIR", str(MEMORY_DIR / "users"))) / f"{user_id}.md"
    return path.read_text() if path.exists() else ""

def load_related_memories(query: str) -> str:
    """load memories related to the user query"""
    memory_manager = MemoryManager()
    memory_recall = memory_manager.recall(query)
    result = narrative_agent(memory_recall)
    return str(result)
