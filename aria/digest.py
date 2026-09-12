"""Session digests: one markdown file per session under memory/digests/.

A digest is the compact record of a session that the context gatherer
injects (the newest RECENT_DIGESTS of them) into every turn. The historian
sub-agent writes the body; this module owns the file -- where it lives, the
frontmatter that says how far into the session it reaches, and the cursor
logic that makes re-running on a still-growing session incremental.

Manual for now (`aria digest <session_id>`); the consolidation daemon will
call run_digest on a schedule later.
"""
from datetime import datetime, timezone
from pathlib import Path

from aria import history, manifest
from aria.subagents.historian import historian


def digest_path(session_id: str) -> Path:
    return manifest.digests_dir() / f"{session_id}.md"


def read_digest(session_id: str) -> tuple[dict, str]:
    """(frontmatter, body). Both empty if there is no digest yet."""
    path = digest_path(session_id)
    if not path.exists():
        return {}, ""
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}, text.strip()
    head, _, body = text[4:].partition("\n---\n")
    meta = {}
    for line in head.splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body.strip()


def write_digest(session_id: str, body: str, digested: list[history.Turn]) -> Path:
    last = digested[-1]
    span = f"{digested[0].started_at[:10]} .. {last.ended_at[:10]}"
    front = "\n".join([
        "---",
        f"session: {session_id}",
        f"turns_digested: {len(digested)}",
        f"through_message: {last.last_message_id}",
        f"span: {span}",
        f"digested_at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "---",
    ])
    path = digest_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(front + "\n" + body.strip() + "\n")
    return path


def run_digest(session_id: str, force: bool = False) -> str:
    """Digest whatever the session has added since the last run.

    Returns a one-line status. A turn still waiting on its reply is left for
    the next run, so digesting a live session is safe.
    """
    turns = history.turns(session_id)
    if turns and not turns[-1].response:
        turns = turns[:-1]
    if not turns:
        return f"{session_id}: no completed turns to digest."

    meta, body = ({}, "") if force else read_digest(session_id)
    done = int(meta.get("turns_digested", 0))
    if done >= len(turns):
        return f"{session_id}: digest is up to date ({done} turns)."

    markdown = historian(session_id, start_turn=done, end_turn=len(turns) - 1,
                         existing_digest=body)
    path = write_digest(session_id, markdown, turns)
    what = "created" if not body else f"updated (+{len(turns) - done} turns)"
    return f"{session_id}: digest {what}, {len(turns)} turns -> {path}"
