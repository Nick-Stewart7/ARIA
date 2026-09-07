"""A readable record of every turn ARIA runs — chat and heartbeat alike.

The session files under SESSION_DIR are Strands' internal replay format:
one JSON file per message, meant for resuming an agent, not for reading.
This is the other view — one line per turn, in the order it happened,
readable without opening a session directory or scrolling terminal history.

Written from the one place both chat and heartbeat already go through:
agent.run_turn.
"""
import json
import os
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path

HEARTBEAT_USER_ID = "aria"


def ledger_path() -> Path:
    return Path(os.getenv("MEMORY_DIR", "memory")) / "ledger.jsonl"


def record_turn(session_id: str, user_id: str, user_input: str, response: str) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "user_id": user_id,
        "input": user_input,
        "response": response,
    }
    path = ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def latest_entries_by_session() -> dict[str, dict]:
    """Most recent ledger entry per session_id, keyed by session_id.

    read_entries() returns entries in the order they were appended, so the
    last write for a given session_id in this loop is genuinely its latest.
    """
    latest: dict[str, dict] = {}
    for entry in read_entries():
        latest[entry["session_id"]] = entry
    return latest


def read_entries(session_id: str | None = None, tail: int | None = None) -> list[dict]:
    path = ledger_path()
    if not path.exists():
        return []
    entries = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if session_id:
        entries = [e for e in entries if e["session_id"] == session_id]
    if tail:
        entries = entries[-tail:]
    return entries


def _wrap(label: str, text: str, width: int = 100) -> str:
    indent = " " * (len(label) + 2)
    wrapped = textwrap.fill(
        text, width=width, initial_indent=f"{label}: ", subsequent_indent=indent
    )
    return wrapped


def format_entry(entry: dict) -> str:
    ts = entry["timestamp"].replace("T", " ").split("+")[0].split(".")[0]
    kind = "heartbeat" if entry["user_id"] == HEARTBEAT_USER_ID else "chat"
    who = "ARIA (self)" if kind == "heartbeat" else entry["user_id"]
    header = f"── {ts} UTC · {kind} · {entry['session_id']} ──"
    lines = [
        header,
        _wrap(who, entry["input"]),
        "",
        _wrap("ARIA", entry["response"]),
    ]
    return "\n".join(lines)


def print_ledger(session_id: str | None = None, tail: int | None = None) -> None:
    entries = read_entries(session_id=session_id, tail=tail)
    if not entries:
        print("No ledger entries yet.")
        return
    for entry in entries:
        print(format_entry(entry))
        print()


def follow_ledger(session_id: str | None = None) -> None:
    """Poll for new entries and print them as they land, like tail -f."""
    path = ledger_path()
    seen = len(read_entries(session_id=session_id))
    print(f"Watching {path} — Ctrl+C to stop.\n")
    try:
        while True:
            entries = read_entries(session_id=session_id)
            for entry in entries[seen:]:
                print(format_entry(entry))
                print()
            seen = len(entries)
            time.sleep(2)
    except KeyboardInterrupt:
        pass
