"""Session identity: ids, where they live on disk, and minting new ones.

FileSessionManager persists each session under
`<storage_dir>/session_<session_id>/` and resumes one by re-passing its id.
Reading what's *inside* a session is aria.history's job; this module only
knows how sessions are named and where the root is.
"""
from pathlib import Path
import os
import uuid

from aria import manifest

SESSION_PREFIX = "session_"

# The heartbeat runs in one long-lived session with a fixed id, so ARIA's
# self-directed turns accumulate in one place instead of a new session per cycle.
HEARTBEAT_SESSION_ID = os.getenv("HEARTBEAT_SESSION_ID", "heartbeat")
HEARTBEAT_USER_ID = "aria"


def sessions_root() -> Path:
    return manifest.sessions_dir()


def new_session_id(user_id: str = "user") -> str:
    return f"conv-{user_id}-{uuid.uuid4().hex[:8]}"


def session_exists(session_id: str) -> bool:
    return (sessions_root() / f"{SESSION_PREFIX}{session_id}").is_dir()


def is_heartbeat(session_id: str) -> bool:
    return session_id == HEARTBEAT_SESSION_ID
