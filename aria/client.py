import argparse
import httpx
import os


def _base_url() -> str:
    host = os.getenv("HOST", "localhost")
    port = os.getenv("PORT", "65535")
    return f"http://{host}:{port}"


def _parse_args(argv):
    parser = argparse.ArgumentParser(prog="aria chat", add_help=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--continue", action="store_true", dest="cont",
                        help="resume the most recently updated session")
    group.add_argument("--session", dest="session_id", default=None,
                        help="resume a specific session by id")
    group.add_argument("--new", action="store_true",
                        help="start a fresh session (default)")
    return parser.parse_args(argv)


async def _resolve_session_id(client: httpx.AsyncClient, opts) -> str | None:
    """None means: let the server mint a new session on the first message."""
    if opts.session_id:
        return opts.session_id
    if opts.cont:
        response = await client.get(f"{_base_url()}/sessions")
        response.raise_for_status()
        sessions = response.json().get("sessions", [])
        if not sessions:
            print("No existing sessions found — starting a new one.\n")
            return None
        return sessions[0]["session_id"]
    return None
