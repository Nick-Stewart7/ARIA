"""Context gathering: what ARIA has in mind at the start of every turn.

Builds the ambient part of the system prompt from the manifest -- file reads
only, no LLM calls, no tools -- so anything written to a memory artifact (by
ARIA, by a digest run, by Nick in an editor) is live on the next turn. Every
turn builds a fresh Agent, so this runs every turn.

Slots are ordered stable-first: identity and the user model rarely change,
recent digests change every session. Prompt templates keep that order so the
model provider's prompt cache can keep the stable prefix.
"""
from dataclasses import dataclass
from pathlib import Path

from aria import manifest
from aria.sessions import HEARTBEAT_USER_ID

HEARTBEAT_USER_NOTE = (
    "This is an autonomous cycle. The input comes from my own possibility "
    "drive, not from a person; nobody is waiting on a reply."
)


@dataclass
class Context:
    identity: str
    user_context: str
    recent_history: str
    file_system: str

    def slots(self) -> dict[str, str]:
        """Keyword arguments for PROMPT.format(**...). Templates use the
        slots they need and ignore the rest."""
        return vars(self)


def _read(path: Path) -> str:
    return path.read_text().strip() if path.exists() else ""


def _user_context(user_id: str | None) -> str:
    if not user_id:
        return ""
    if user_id == HEARTBEAT_USER_ID:
        return HEARTBEAT_USER_NOTE
    text = _read(manifest.user_file(user_id))
    return text or f"No user model for {user_id} yet. It belongs at {manifest.user_file(user_id)}."


def recent_digests() -> list[Path]:
    """Newest first, by file mtime -- re-digesting a session bumps it forward,
    which is what we want."""
    directory = manifest.digests_dir()
    if not directory.is_dir():
        return []
    files = [p for p in directory.iterdir() if p.suffix == ".md"]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[: manifest.RECENT_DIGESTS]


def _recent_history() -> str:
    lines = ["## Recent History", f"The {manifest.RECENT_DIGESTS} most recent session digests, newest first."]
    digests = recent_digests()
    if not digests:
        lines.append("(no session digests yet)")
        return "\n".join(lines)
    for path in digests:
        lines += ["", f"### {path.stem}", _read(path)]
    return "\n".join(lines)


def gather(user_id: str | None = None) -> Context:
    """Everything a prompt template can ask for. Sub-agents call it with no
    user_id and get identity + file system only."""
    return Context(
        identity=_read(manifest.identity_file()),
        user_context=_user_context(user_id),
        recent_history=_recent_history() if user_id else "",
        file_system=manifest.render_for_prompt(user_id),
    )
