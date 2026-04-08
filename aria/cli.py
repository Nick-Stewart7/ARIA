import sys
import asyncio
import time
from pathlib import Path
import os
from aria.server import ARIAServer
from aria.setup_wizard import run_setup
from aria.heartbeat import send_event
from aria.interface import chat
from aria.summary import run_memory_consolidation

def start_server():
    server = ARIAServer()
    asyncio.run(server.start())

def run_heartbeat():
    interval = int(os.getenv("HEARTBEAT_MAX_CYCLES", "6"))
    period = int(os.getenv("HEARTBEAT_PERIOD", "10"))
    period_seconds = period * 60
    i = 0
    while True:
        asyncio.run(send_event())
        time.sleep(period_seconds)
        if i == interval:
            break
        i+=1


def main():
    match sys.argv[1] if len(sys.argv) > 1 else "help":
        case "serve": start_server()
        case "setup": run_setup()
        case "heartbeat": run_heartbeat()
        case "chat": asyncio.run(chat())
        case "compact": pass #Todo add smart compact
        case "summarize": run_memory_consolidation()
        case _: print("Please provide a valid command for ARIA || Commands: serve | setup | heartbeat | chat | compact | summarize")