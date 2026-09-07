"""Session identity: what sessions exist, and minting new ones.

FileSessionManager already persists each session under
`<storage_dir>/session_<session_id>/` and resumes one by re-passing its id.
This module is the one place that knows that on-disk shape, so callers
(the REST API, the CLI) work with session ids only.
"""
from datetime import datetime, timezone
from pathlib import Path
import os
import uuid

from aria.ledger import latest_entries_by_session

SESSION_PREFIX = "session_"


def sessions_root() -> Path:
    return Path(os.getenv("SESSION_DIR", "sessions"))


def new_session_id(user_id: str = "user") -> str:
    return f"conv-{user_id}-{uuid.uuid4().hex[:8]}"


def session_exists(session_id: str) -> bool:
    return (sessions_root() / f"{SESSION_PREFIX}{session_id}").is_dir()


def list_sessions() -> list[dict]:
    """Existing sessions, most recently active first.

    "Active" prefers the ledger's last-turn timestamp: FileSessionManager
    never touches a session's top-level directory again after its first
    turn (only files nested under agents/.../messages/ change), so the
    directory's own mtime goes stale after one turn and can't be trusted
    for ordering. Falls back to directory mtime for sessions that predate
    the ledger.
    """
    root = sessions_root()
    if not root.exists():
        return []

    latest = latest_entries_by_session()

    sessions = []
    for path in root.iterdir():
        if path.is_dir() and path.name.startswith(SESSION_PREFIX):
            session_id = path.name[len(SESSION_PREFIX):]
            entry = latest.get(session_id)
            if entry:
                updated_at = entry["timestamp"]
            else:
                updated_at = datetime.fromtimestamp(
                    path.stat().st_mtime, tz=timezone.utc
                ).isoformat()
            sessions.append({"session_id": session_id, "updated_at": updated_at})
    sessions.sort(key=lambda s: s["updated_at"], reverse=True)
    return sessions


def most_recent_session_id() -> str | None:
    sessions = list_sessions()
    return sessions[0]["session_id"] if sessions else None
