import sys
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()  # must run before anything reads SESSION_DIR/HOST/PORT/etc.

import uvicorn
from aria.setup_wizard import run_setup
from aria.client import chat
from aria.summary import run_memory_consolidation
from aria.app import app


def start_server():
    # Heartbeat runs inside app's lifespan — starting the server is enough
    # to bring ARIA's autonomous cycle alive, no separate command needed.
    uvicorn.run(app, host=os.getenv("HOST", "localhost"), port=int(os.getenv("PORT", "65535")))


def main():
    match sys.argv[1] if len(sys.argv) > 1 else "help":
        case "serve": start_server()
        case "setup": run_setup()
        case "chat": asyncio.run(chat(sys.argv[2:]))
        case "compact": pass #Todo add smart compact
        case "summarize": run_memory_consolidation()
        case _: print("Please provide a valid command for ARIA || Commands: serve | setup | chat | compact | summarize")