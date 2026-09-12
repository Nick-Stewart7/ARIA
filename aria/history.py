"""Read access to ARIA's session history — the archive tier's single door.

FileSessionManager persists a session as one JSON file per raw model
message:

    <SESSION_DIR>/session_<id>/session.json
    <SESSION_DIR>/session_<id>/agents/agent_default/agent.json
    <SESSION_DIR>/session_<id>/agents/agent_default/messages/message_<n>.json

That is a replay format, meant for resuming an agent: one turn that calls
tools spans several files (assistant toolUse -> user toolResult -> ...
-> assistant text). This module is the only place that knows the shape.
It folds the files back into turns — one user input, everything ARIA did
in response, and the final reply — for `aria log`, `aria sessions`,
session digests, and (later) history search.
"""
import json
import os
import re
import textwrap
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from aria.sessions import SESSION_PREFIX, is_heartbeat, sessions_root

_MESSAGE_FILE = re.compile(r"message_(\d+)\.json$")
_CONV_ID = re.compile(r"^conv-(.+)-[0-9a-f]{8}$")


@dataclass
class ToolCall:
    name: str
    input: dict
    status: str = ""     # "success" / "error" once the result lands
    result: str = ""     # result text, empty if the turn was cut off


@dataclass
class Turn:
    session_id: str
    index: int                     # 0-based turn number within the session
    input: str
    response: str = ""
    tools: list[ToolCall] = field(default_factory=list)
    started_at: str = ""           # ISO timestamp of the user message
    ended_at: str = ""             # ISO timestamp of the last message in the turn
    first_message_id: int = 0      # raw message ids this turn spans -- the
    last_message_id: int = 0       # cursor a digest can resume from


@dataclass
class SessionInfo:
    session_id: str
    created_at: str
    updated_at: str                # last message written, not dir mtime


# --- on-disk shape ---------------------------------------------------------

def _session_dir(session_id: str) -> Path:
    return sessions_root() / f"{SESSION_PREFIX}{session_id}"


def _messages_dir(session_id: str) -> Path:
    return _session_dir(session_id) / "agents" / "agent_default" / "messages"


def _message_files(session_id: str) -> list[Path]:
    """Message files in message_id order (lexical order would put 10 before 2)."""
    directory = _messages_dir(session_id)
    if not directory.is_dir():
        return []
    numbered = []
    for path in directory.iterdir():
        match = _MESSAGE_FILE.match(path.name)
        if match:
            numbered.append((int(match.group(1)), path))
    return [path for _, path in sorted(numbered)]


def message_count(session_id: str) -> int:
    return len(_message_files(session_id))


def _text_of(content: list[dict]) -> str:
    return "\n".join(block["text"] for block in content if "text" in block)


def _result_text(result: dict) -> str:
    parts = []
    for block in result.get("content", []):
        if "text" in block:
            parts.append(block["text"])
        elif "json" in block:
            parts.append(json.dumps(block["json"]))
    return "\n".join(parts)


# --- turns -----------------------------------------------------------------

def turns(session_id: str) -> list[Turn]:
    """Fold a session's raw messages into turns.

    A user message carrying text starts a turn; user messages carrying only
    toolResult blocks belong to the turn in flight. Assistant text is taken
    from the last assistant message in the turn, so a "let me look..." that
    precedes tool calls is superseded by the actual reply.
    """
    folded: list[Turn] = []
    current: Turn | None = None
    pending: dict[str, ToolCall] = {}   # toolUseId -> call awaiting its result

    for path in _message_files(session_id):
        raw = json.loads(path.read_text())
        message = raw.get("redact_message") or raw["message"]
        content = message.get("content", [])
        message_id = raw["message_id"]
        stamp = raw.get("updated_at") or raw.get("created_at") or ""

        if message["role"] == "user":
            results = [block["toolResult"] for block in content if "toolResult" in block]
            if results and current is not None:
                for result in results:
                    call = pending.pop(result.get("toolUseId"), None)
                    if call:
                        call.status = result.get("status", "")
                        call.result = _result_text(result)
            else:
                current = Turn(
                    session_id=session_id,
                    index=len(folded),
                    input=_text_of(content),
                    started_at=raw.get("created_at") or "",
                    first_message_id=message_id,
                )
                folded.append(current)
                pending = {}
        else:
            if current is None:  # session file starts mid-turn; don't lose it
                current = Turn(session_id=session_id, index=len(folded), input="",
                               started_at=raw.get("created_at") or "",
                               first_message_id=message_id)
                folded.append(current)
            for block in content:
                if "toolUse" in block:
                    use = block["toolUse"]
                    call = ToolCall(name=use.get("name", "?"), input=use.get("input", {}))
                    current.tools.append(call)
                    pending[use.get("toolUseId")] = call
            text = _text_of(content)
            if text:
                current.response = text

        current.ended_at = stamp
        current.last_message_id = message_id

    return folded


def last_turn(session_id: str) -> Turn | None:
    folded = turns(session_id)
    return folded[-1] if folded else None


# --- sessions --------------------------------------------------------------

def _last_activity(session_id: str) -> str:
    """ISO timestamp of the newest message; falls back to dir mtime for a
    session that has no messages yet."""
    files = _message_files(session_id)
    if files:
        raw = json.loads(files[-1].read_text())
        stamp = raw.get("updated_at") or raw.get("created_at")
        if stamp:
            return stamp
    return datetime.fromtimestamp(
        _session_dir(session_id).stat().st_mtime, tz=timezone.utc
    ).isoformat()


def session_info(session_id: str) -> SessionInfo:
    meta_path = _session_dir(session_id) / "session.json"
    created_at = ""
    if meta_path.exists():
        created_at = json.loads(meta_path.read_text()).get("created_at", "")
    return SessionInfo(session_id=session_id, created_at=created_at,
                       updated_at=_last_activity(session_id))


def list_sessions() -> list[SessionInfo]:
    """Existing sessions, most recently active first."""
    root = sessions_root()
    if not root.exists():
        return []
    found = [
        session_info(path.name[len(SESSION_PREFIX):])
        for path in root.iterdir()
        if path.is_dir() and path.name.startswith(SESSION_PREFIX)
    ]
    found.sort(key=lambda s: s.updated_at, reverse=True)
    return found


def most_recent_session_id() -> str | None:
    found = list_sessions()
    return found[0].session_id if found else None


# --- readable output (`aria log`) ------------------------------------------

def _wrap(label: str, text: str, width: int = 100) -> str:
    indent = " " * (len(label) + 2)
    return textwrap.fill(text, width=width, initial_indent=f"{label}: ",
                         subsequent_indent=indent)


def _who(session_id: str) -> str:
    if is_heartbeat(session_id):
        return "ARIA (self)"
    match = _CONV_ID.match(session_id)
    return match.group(1) if match else "user"


def _tool_line(call: ToolCall) -> str:
    args = ", ".join(f"{k}={json.dumps(v)}" for k, v in call.input.items())
    if len(args) > 80:
        args = args[:77] + "..."
    size = f"{len(call.result)} chars" if call.result else "no result"
    flag = " !" if call.status == "error" else ""
    return f"  ⚙ {call.name}({args}) → {size}{flag}"


def format_turn(turn: Turn) -> str:
    stamp = turn.started_at.replace("T", " ").split("+")[0].split(".")[0]
    kind = "heartbeat" if is_heartbeat(turn.session_id) else "chat"
    lines = [
        f"── {stamp} UTC · {kind} · {turn.session_id} · turn {turn.index} ──",
        _wrap(_who(turn.session_id), turn.input),
    ]
    lines.extend(_tool_line(call) for call in turn.tools)
    lines.append("")
    lines.append(_wrap("ARIA", turn.response or "(no reply)"))
    return "\n".join(lines)


def print_log(session_id: str | None = None, tail: int | None = None) -> None:
    if session_id:
        recent = turns(session_id)
    else:
        recent = [turn for info in list_sessions() for turn in turns(info.session_id)]
        recent.sort(key=lambda t: t.started_at)
    if tail:
        recent = recent[-tail:]
    if not recent:
        print("No turns yet.")
        return
    for turn in recent:
        print(format_turn(turn))
        print()


def follow_log(session_id: str | None = None) -> None:
    """Poll for new turns and print them as they land, like tail -f.

    Only re-reads a session when its message count changes, so idle polling
    is a directory listing per session, not a JSON parse.
    """
    def watched() -> list[str]:
        return [session_id] if session_id else [s.session_id for s in list_sessions()]

    seen_messages = {sid: message_count(sid) for sid in watched()}
    seen_turns = {sid: len(turns(sid)) for sid in watched()}
    print(f"Watching {sessions_root()} — Ctrl+C to stop.\n")
    try:
        while True:
            for sid in watched():
                count = message_count(sid)
                if count == seen_messages.get(sid):
                    continue
                seen_messages[sid] = count
                folded = turns(sid)
                for turn in folded[seen_turns.get(sid, 0):]:
                    # only the newest turn can still be in flight -- hold it
                    # until its reply lands; an older turn with no reply was
                    # interrupted and prints as such
                    if turn is folded[-1] and not turn.response:
                        break
                    print(format_turn(turn))
                    print()
                    seen_turns[sid] = turn.index + 1
            time.sleep(2)
    except KeyboardInterrupt:
        pass
