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
from textual.containers import VerticalScroll
from textual.widgets import Input, Static

from aria.client import _base_url, _parse_args, _resolve_session_id


class AriaTUI(App):
    """ARIA chat, streamed token-by-token over Server-Sent Events."""

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
    """

    def __init__(self, argv=None):
        super().__init__()
        self.opts = _parse_args(argv or [])
        self.user_id = os.getenv("USER_ID", "user")
        self.session_id: str | None = None
        self._client: httpx.AsyncClient | None = None

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="transcript")
        yield Input(placeholder="Message ARIA…")

    async def on_mount(self) -> None:
        timeout = httpx.Timeout(180.0, connect=5.0)
        self._client = httpx.AsyncClient(timeout=timeout)
        try:
            self.session_id = await _resolve_session_id(self._client, self.opts)
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

        await self._mount_static(f"You: {text}", "user-message")
        assistant_widget = await self._mount_static("ARIA: …", "aria-message")

        self.send_message(text, assistant_widget)

    @work(exclusive=True)
    async def send_message(self, text: str, assistant_widget: Static) -> None:
        transcript = self.query_one("#transcript", VerticalScroll)
        accumulated = ""
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
                    if not line.startswith("data: "):
                        continue
                    item = json.loads(line[len("data: "):])
                    if "delta" in item:
                        accumulated += item["delta"]
                        assistant_widget.update(f"ARIA: {accumulated}")
                        transcript.scroll_end(animate=False)
                    elif item.get("done"):
                        self.session_id = item.get("session_id", self.session_id)
                    elif "session_id" in item:
                        self.session_id = item["session_id"]
        except httpx.ConnectError:
            assistant_widget.update("[error] Could not reach ARIA server. Is 'aria serve' running?")
        except httpx.HTTPStatusError as e:
            assistant_widget.update(f"[error] {e.response.status_code}: {e.response.text}")


def run(argv=None):
    AriaTUI(argv).run()


if __name__ == "__main__":
    import sys
    run(sys.argv[1:])
