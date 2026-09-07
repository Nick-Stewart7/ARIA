"""ARIA's chat interface — a Textual TUI over the REST /chat SSE stream.

Replaces the old input()/print() REPL (archived at archive/client_repl.py).
Reuses aria.client's session-resolution helpers (--new/--continue/--session)
so the TUI understands the exact same flags the REPL did.
"""
import json
import os

import httpx
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Input, Static
from textual.worker import get_current_worker

from aria.client import _base_url, _parse_args, _resolve_session_id


class StatusSegment(Static):
    """One slot in the status bar. A subclass sets `value` and formats it in
    `render()` -- adding a future segment means writing one more subclass and
    one more line in compose(), nothing else touched."""

    value = reactive("")

    def render(self) -> str:
        return str(self.value)


class SessionSegment(StatusSegment):
    def render(self) -> str:
        return f"session: {self.value}" if self.value else "session: —"


class TokenCostSegment(StatusSegment):
    value = reactive(0)

    def render(self) -> str:
        return f"tokens: {self.value:,}"


class AriaTUI(App):
    """ARIA chat, streamed token-by-token over Server-Sent Events."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    CSS = """
    #transcript {
        height: 1fr;
        padding: 1 2;
    }
    .user-message {
        color: $text;
        margin: 1 0 0 0;
    }
    .aria-message {
        color: $accent;
        margin: 0 0 1 0;
    }
    #status_bar {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text-muted;
    }
    StatusSegment {
        width: auto;
        padding: 0 2;
    }
    """

    def __init__(self, argv=None):
        super().__init__()
        self.opts = _parse_args(argv or [])
        self.user_id = os.getenv("USER_ID", "user")
        self.session_id: str | None = None
        self._client: httpx.AsyncClient | None = None
        self._turn_in_flight = False
        # Bumped each time a new turn starts. A superseded turn's `finally`
        # compares its own generation against this before clearing
        # _turn_in_flight, so a cancelled-but-still-unwinding old worker
        # can't clobber the flag while a newer turn is genuinely running.
        self._turn_generation = 0
        self._total_tokens = 0

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="transcript")
        yield Input(placeholder="Message ARIA…")
        yield Horizontal(SessionSegment(), TokenCostSegment(), id="status_bar")

    async def on_mount(self) -> None:
        timeout = httpx.Timeout(180.0, connect=5.0)
        self._client = httpx.AsyncClient(timeout=timeout)
        try:
            self.session_id = await _resolve_session_id(self._client, self.opts)
            self.query_one(SessionSegment).value = self.session_id or ""
        except httpx.ConnectError:
            await self._mount_static(
                "[error] Could not reach ARIA server. Is 'aria serve' running?", "aria-message"
            )
        self.query_one(Input).focus()

    async def _mount_static(self, text: str, css_class: str) -> Static:
        transcript = self.query_one("#transcript", VerticalScroll)
        widget = Static(text, classes=css_class)
        await transcript.mount(widget)
        transcript.scroll_end(animate=False)
        return widget

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        self.query_one(Input).value = ""

        if self._turn_in_flight:
            # A previous turn is still streaming -- this is a redirect, not
            # just a new message. @work(exclusive=True) below will cancel
            # the old *local* worker's read loop once the new one starts,
            # but that alone never reaches the server: the old turn would
            # keep generating (and spending tokens) invisibly. Tell the
            # server to stop it first, same as Escape does.
            await self._cancel_active_turn()

        await self._mount_static(f"You: {text}", "user-message")
        assistant_widget = await self._mount_static("ARIA: …", "aria-message")

        self._turn_generation += 1
        self.send_message(text, assistant_widget, self._turn_generation)

    async def action_cancel(self) -> None:
        """Escape: stop the in-flight turn server-side.

        Deliberately does NOT force-cancel the local worker: that would
        race the server's own graceful wind-down and usually win, leaving
        the widget stuck on the "..." placeholder instead of showing the
        authoritative "Cancelled by user" text Strands persists -- letting
        the read loop keep draining picks that final frame up naturally,
        moments later.
        """
        if not self._turn_in_flight:
            return
        await self._cancel_active_turn()

    async def _cancel_active_turn(self) -> None:
        if not self.session_id:
            return
        try:
            await self._client.post(
                f"{_base_url()}/chat/cancel", json={"session_id": self.session_id}
            )
        except httpx.HTTPError:
            pass  # best-effort -- worst case the turn just runs to completion

    @work(exclusive=True)
    async def send_message(self, text: str, assistant_widget: Static, generation: int) -> None:
        transcript = self.query_one("#transcript", VerticalScroll)
        worker = get_current_worker()
        accumulated = ""
        self._turn_in_flight = True
        try:
            async with self._client.stream(
                "POST",
                f"{_base_url()}/chat",
                json={"user_id": self.user_id, "session_id": self.session_id, "message": text},
            ) as response:
                if response.status_code == 404:
                    assistant_widget.update(
                        f"[error] No session found with id '{self.session_id}'. "
                        f"Use 'aria chat --new' to start one, or 'aria chat --continue' "
                        f"to resume the most recent."
                    )
                    return
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if worker.is_cancelled:
                        break  # cancelled mid-read -- drop anything still in flight
                    if not line.startswith("data: "):
                        continue
                    item = json.loads(line[len("data: "):])
                    if "delta" in item:
                        accumulated += item["delta"]
                        assistant_widget.update(f"ARIA: {accumulated}")
                        transcript.scroll_end(animate=False)
                    elif item.get("done"):
                        self.session_id = item.get("session_id", self.session_id)
                        self.query_one(SessionSegment).value = self.session_id or ""
                        # cumulative across the session, not just this turn --
                        # a running total is what answers "am I burning tokens".
                        usage = item.get("usage") or {}
                        self._total_tokens += usage.get("totalTokens", 0)
                        self.query_one(TokenCostSegment).value = self._total_tokens
                        # authoritative final text -- e.g. "Cancelled by
                        # user" on a cancelled turn, not just the deltas
                        # accumulated before the cancel took effect.
                        assistant_widget.update(f"ARIA: {item.get('response', accumulated)}")
                    elif "session_id" in item:
                        self.session_id = item["session_id"]
                        self.query_one(SessionSegment).value = self.session_id or ""
        except httpx.ConnectError:
            assistant_widget.update("[error] Could not reach ARIA server. Is 'aria serve' running?")
        except httpx.HTTPStatusError as e:
            assistant_widget.update(f"[error] {e.response.status_code}: {e.response.text}")
        finally:
            if generation == self._turn_generation:
                self._turn_in_flight = False


def run(argv=None):
    AriaTUI(argv).run()


if __name__ == "__main__":
    import sys
    run(sys.argv[1:])
