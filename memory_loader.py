from pathlib import Path
from memory_manager import MemoryManager

from subagents.narrative_writer import narrative_agent

_ROOT = Path(__file__).parent

FILE_SYSTEM_ARCHITECTURE = f"""
Here is a list of files present in your directory.
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

def load_related_memories(query: str) -> str:
    """load memories related to the user query"""
    memory_manager = MemoryManager()
    memory_recall = memory_manager.recall(query)
    result = narrative_agent(memory_recall)
    return str(result)
