"""The memory directory: what lives under MEMORY_DIR and how each piece reaches ARIA.

This is the one place that knows the layout. Code resolves paths through it,
aria.context walks ARTIFACTS to decide what goes into the system prompt, and
render_for_prompt() is the directory listing ARIA herself sees.

Policies:
  always     read into every turn's system prompt
  recent     the RECENT_DIGESTS newest files in the directory go into every turn
  on_demand  described so ARIA knows it exists; reached by tool, never injected
"""
import os
from dataclasses import dataclass
from pathlib import Path

RECENT_DIGESTS = 3


def memory_dir() -> Path:
    return Path(os.getenv("MEMORY_DIR", "memory")).resolve()


def sessions_dir() -> Path:
    return Path(os.getenv("SESSION_DIR", memory_dir() / "sessions")).resolve()


def chroma_dir() -> Path:
    return Path(os.getenv("CHROMA_DB_DIR", "chroma_db")).resolve()


def artifacts_dir() -> Path:
    return Path(os.getenv("ARTIFACTS_DIR", "artifacts")).resolve()


def identity_file() -> Path:
    return memory_dir() / "identity" / "ARIA.md"


def user_file(user_id: str) -> Path:
    # lower-cased: USER_ID is whatever the person typed at setup ("Nick"),
    # the file is what we ship ("nick.md"), and Linux won't bridge the two
    return memory_dir() / "users" / f"{user_id.lower()}.md"


def digests_dir() -> Path:
    return memory_dir() / "digests"


@dataclass(frozen=True)
class Artifact:
    name: str
    path: Path
    policy: str      # always | recent | on_demand
    purpose: str     # one line, in ARIA's own voice, shown in the prompt


def artifacts(user_id: str | None = None) -> list[Artifact]:
    """Every artifact ARIA's context is built from, in injection order."""
    listed = [
        Artifact("identity", identity_file(), "always",
                 "who I am; loaded into every agent's prompt"),
    ]
    if user_id:
        listed.append(Artifact("user", user_file(user_id), "always",
                               "what I know about the person I'm talking with"))
    listed += [
        Artifact("digests", digests_dir(), "recent",
                 f"one digest per session; the {RECENT_DIGESTS} newest are in my context"),
        Artifact("sessions", sessions_dir(), "on_demand",
                 "raw session history in Strands' replay format; `aria log` reads it, I don't"),
        Artifact("artifacts", artifacts_dir(), "on_demand",
                 "things I make: files, research, code"),
    ]
    return listed


def ensure_layout() -> None:
    """Create the directories the layout expects. Safe to call repeatedly."""
    for directory in (identity_file().parent, memory_dir() / "users",
                      digests_dir(), sessions_dir(), artifacts_dir()):
        directory.mkdir(parents=True, exist_ok=True)


def render_for_prompt(user_id: str | None = None) -> str:
    """The directory listing that goes into the system prompt."""
    lines = ["## File System", f"My memory lives at {memory_dir()}.", ""]
    for artifact in artifacts(user_id):
        lines.append(f"- {artifact.name}: {artifact.path} — {artifact.purpose}")
    return "\n".join(lines)
