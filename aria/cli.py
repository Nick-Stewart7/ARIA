import sys
import os
from dotenv import load_dotenv

load_dotenv()  # must run before anything reads SESSION_DIR/HOST/PORT/etc.

from aria.logging_setup import configure_logging

configure_logging()  # must run before any aria module logs or calls basicConfig

import argparse
import uvicorn
from aria.setup_wizard import run_setup
from aria.tui import run as run_tui
from aria.app import app
from aria.history import print_log, follow_log, list_sessions, last_turn
from aria.client import _base_url


def start_server():
    # Heartbeat runs inside app's lifespan — starting the server is enough
    # to bring ARIA's autonomous cycle alive, no separate command needed.
    uvicorn.run(app, host=os.getenv("HOST", "localhost"), port=int(os.getenv("PORT", "65535")))


def show_log(argv):
    parser = argparse.ArgumentParser(prog="aria log", add_help=False)
    parser.add_argument("--session", dest="session_id", default=None,
                         help="only show this session's turns")
    parser.add_argument("--tail", type=int, default=20,
                         help="how many recent turns to show (default 20)")
    parser.add_argument("--follow", "-f", action="store_true",
                         help="keep watching and print new turns as they land")
    opts = parser.parse_args(argv)

    if opts.follow:
        follow_log(session_id=opts.session_id)
    else:
        print_log(session_id=opts.session_id, tail=opts.tail)


def show_sessions():
    sessions = list_sessions()
    if not sessions:
        print("No sessions yet.")
        return

    for s in sessions:
        turn = last_turn(s.session_id)
        preview = turn.input.strip().replace("\n", " ")[:70] if turn else "(no turns yet)"
        print(f"{s.session_id:<28} {s.updated_at[:19]}  {preview}")


def heartbeat_control(argv):
    import httpx

    action = argv[0] if argv else "status"
    route = {"pause": "/heartbeat/pause", "resume": "/heartbeat/resume", "status": "/heartbeat"}.get(action)
    if route is None:
        print("Usage: aria heartbeat [pause|resume|status]")
        return

    try:
        method = httpx.post if route != "/heartbeat" else httpx.get
        response = method(f"{_base_url()}{route}")
        response.raise_for_status()
        enabled = response.json().get("enabled")
        print(f"Heartbeat is {'running' if enabled else 'paused'}.")
    except httpx.ConnectError:
        print("[error] Could not reach ARIA server. Is 'aria serve' running?")


def main():
    match sys.argv[1] if len(sys.argv) > 1 else "help":
        case "serve": start_server()
        case "setup": run_setup()
        case "chat": run_tui(sys.argv[2:])
        case "compact": pass #Todo add smart compact
        case "log": show_log(sys.argv[2:])
        case "sessions": show_sessions()
        case "heartbeat": heartbeat_control(sys.argv[2:])
        case _: print("Please provide a valid command for ARIA || Commands: serve | setup | chat | compact | log | sessions | heartbeat")