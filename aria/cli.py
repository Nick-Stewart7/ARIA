import sys
import asyncio
from aria.server import ARIAServer
from aria.setup_wizard import run_setup
from aria.heartbeat import send_event
from aria.interface import chat
from aria.summary import run_memory_consolidation

def start_server():
    server = ARIAServer()
    asyncio.run(server.start())



def main():
    match sys.argv[1] if len(sys.argv) > 1 else "help":
        case "serve": start_server()
        case "setup": run_setup()
        case "heartbeat": send_event()
        case "chat": asyncio.run(chat())
        case "compact": pass #Todo add smart compact
        case "summarize": run_memory_consolidation()
        case "help": print("Commands: serve | setup | heartbeat | chat | compact | summarize")
        case _: print("Please provide a command for ARIA || Commands: serve | setup | heartbeat | chat | compact | summarize")