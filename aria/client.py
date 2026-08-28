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


async def chat(argv=None):
    opts = _parse_args(argv or [])
    user_id = os.getenv("USER_ID", "user")

    print("Connected to ARIA. Type 'exit' to quit.\n")
    timeout = httpx.Timeout(180.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            session_id = await _resolve_session_id(client, opts)
        except httpx.ConnectError:
            print("[error] Could not reach ARIA server. Is 'aria serve' running?\n")
            return

        while True:
            user_input = input('⌾ ')
            if user_input.strip().lower() in ('exit', 'quit'):
                break

            try:
                response = await client.post(f"{_base_url()}/chat", json={
                    "user_id": user_id,
                    "session_id": session_id,
                    "message": user_input,
                })
                if response.status_code == 404:
                    print(f"\n[error] No session found with id '{session_id}'. "
                          f"Use 'aria chat --new' to start one, or 'aria chat --continue' "
                          f"to resume the most recent.\n")
                    break
                response.raise_for_status()
                data = response.json()
                session_id = data.get("session_id")  # pin the minted id after the first turn
                print(f"\n{data.get('response')}\n")
            except httpx.ConnectError:
                print("\n[error] Could not reach ARIA server. Is 'aria serve' running?\n")
                break
            except httpx.HTTPStatusError as e:
                print(f"\n[error] {e.response.status_code}: {e.response.text}\n")


if __name__ == "__main__":
    import asyncio
    import sys
    asyncio.run(chat(sys.argv[1:]))
