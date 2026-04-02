import sys
import asyncio
import time
from aria.server import ARIAServer
from aria.setup_wizard import run_setup
from aria.heartbeat import send_event
from aria.interface import chat
from aria.summary import run_memory_consolidation

def start_server():
    server = ARIAServer()
    asyncio.run(server.start())

def run_heartbeat():
    i = 0
    while True:
        asyncio.run(send_event())
        time.sleep(600)  # Wait for 10 minutes before sending the next heartbeat
        # For demonstration purposes, we'll stop after 1 hour (6 heartbeats)
        if i == 6:
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