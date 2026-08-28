"""
ARIA Unified Server
====================
Single entry point that runs:
  1. WebSocket server (reactive - handles chat connections)
  2. Heartbeat loop (proactive - autonomous thinking cycles)
  3. Memory consolidation (proactive - summarizes sessions into long-term memory)

Run with: python server.py

Concepts explained inline for reference.
"""

import asyncio
import websockets
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aria")


# =============================================================================
# SHARED RESOURCES
# =============================================================================
# These are the "communal" layer - accessible to all ARIA instances (chat
# sessions, heartbeat sessions, consolidation). They represent ARIA's
# persistent world: files, long-term memory, and configuration.
#
# Each individual session gets its OWN conversation state, but reads from
# these shared resources at startup.
# =============================================================================

@dataclass
class SharedResources:
    """
    Everything that persists across sessions and is shared between
    chat instances, heartbeat, and memory consolidation.
    
    This is NOT session state. Session state (conversation history,
    current context) is created fresh for each chat or heartbeat cycle.
    """
    # Long-term vector memory (ChromaDB client)
    # All sessions read from this at startup to build their context narrative.
    # The consolidation task writes to this when summarizing completed sessions.
    chroma_client: object = None  # Your ChromaDB client goes here
    
    # File-based shared state (ARIA.md files, artifacts, etc.)
    # Any session can read these. Heartbeat might write to them.
    # Other sessions pick up changes on their NEXT startup, not mid-session.
    workspace_path: Path = field(default_factory=lambda: Path("./aria_workspace"))
    
    # Static prompts and config (identical across all instances)
    system_prompt: str = ""
    heartbeat_interval_seconds: int = 300  # 5 minutes
    consolidation_interval_seconds: int = 900  # 15 minutes
    
    # Track active sessions (for consolidation to know what's finished)
    # This is metadata ABOUT sessions, not session state itself.
    completed_sessions: list = field(default_factory=list)


def initialize_shared_resources() -> SharedResources:
    """
    Called once at server startup. Sets up everything that all
    ARIA instances will share.
    """
    logger.info("Initializing shared resources...")
    
    resources = SharedResources()
    
    # TODO: Initialize your ChromaDB client
    # resources.chroma_client = chromadb.PersistentClient(path="./aria_memory")
    
    # TODO: Load your system prompts
    # resources.system_prompt = Path("prompts/system.md").read_text()
    
    # Ensure workspace exists
    resources.workspace_path.mkdir(exist_ok=True)
    
    logger.info("Shared resources initialized.")
    return resources


# =============================================================================
# ARIA SESSION
# =============================================================================
# Each chat connection or heartbeat cycle creates one of these.
# It has its own conversation history but reads from shared resources.
# This is the "consciousness boundary" - the session is private,
# the world it reads from is communal.
# =============================================================================

class AriaSession:
    """
    A single ARIA interaction session. Created fresh for each:
    - Chat connection (user talks to ARIA)
    - Heartbeat cycle (ARIA talks to itself)
    
    Each session builds its own context at startup by reading from
    shared resources (vector DB, files), then runs independently.
    """
    
    def __init__(self, shared: SharedResources, session_type: str = "chat"):
        self.shared = shared
        self.session_type = session_type  # "chat" or "heartbeat"
        self.conversation_history = []
        self.context_narrative = ""
    
    async def initialize(self):
        """
        Session startup: gather memories and build context.
        This is where the shared->private boundary happens.
        The session reads from the communal memory store and
        constructs its own narrative/context from it.
        """
        # TODO: Query ChromaDB for relevant memories
        # memories = self.shared.chroma_client.query(...)
        
        # TODO: Read relevant ARIA.md files from workspace
        # files = list(self.shared.workspace_path.glob("*.md"))
        
        # TODO: Construct the narrative that becomes this session's context
        # self.context_narrative = build_narrative(memories, files)
        
        logger.info(f"Session initialized (type={self.session_type})")
    
    async def process_message(self, user_input: str) -> str:
        """
        Process a single message through the Strands agent.
        Returns ARIA's response.
        """
        # TODO: Your Strands SDK agent call goes here.
        # This is where Observer/Reflector cognitive tools are available.
        # 
        # response = agent.invoke(
        #     input=user_input,
        #     context=self.context_narrative,
        #     history=self.conversation_history,
        # )
        
        # Track conversation history (private to this session)
        self.conversation_history.append({"role": "user", "content": user_input})
        # self.conversation_history.append({"role": "assistant", "content": response})
        
        return "TODO: agent response"
    
    def get_session_summary(self) -> dict:
        """
        Called when the session ends. Returns the conversation
        history and metadata for later consolidation into long-term memory.
        """
        return {
            "type": self.session_type,
            "history": self.conversation_history,
            "context_used": self.context_narrative,
        }


# =============================================================================
# WEBSOCKET HANDLER (Reactive)
# =============================================================================
# This handles incoming chat connections. Each connection gets its own
# AriaSession. Multiple people (or tabs) can connect simultaneously,
# each with independent sessions, all reading from the same shared resources.
# =============================================================================

async def handle_chat_connection(websocket, shared: SharedResources):
    """
    Called for each new WebSocket connection.
    Creates a fresh AriaSession and runs the chat loop.
    """
    session = AriaSession(shared, session_type="chat")
    await session.initialize()
    
    logger.info("New chat connection established.")
    
    try:
        async for raw_message in websocket:
            # Parse incoming message
            data = json.loads(raw_message)
            user_input = data.get("message", "")
            
            # Process through ARIA
            response = await session.process_message(user_input)
            
            # Send response back
            await websocket.send(json.dumps({
                "type": "response",
                "content": response,
            }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info("Chat connection closed.")
    
    finally:
        # Session is over. Store it for later consolidation.
        summary = session.get_session_summary()
        shared.completed_sessions.append(summary)
        logger.info("Session archived for consolidation.")


# =============================================================================
# HEARTBEAT LOOP (Proactive)
# =============================================================================
# This is the "ARIA is alive" loop. It runs on a timer, creates its own
# ephemeral session each cycle, generates a self-prompt, thinks, and
# writes any artifacts/files back to the shared workspace.
#
# This is an asyncio background task - it runs concurrently with the
# WebSocket server in the same process and event loop.
# =============================================================================

async def heartbeat_loop(shared: SharedResources):
    """
    Autonomous thinking loop. Runs forever alongside the server.
    
    Each heartbeat cycle:
    1. Creates a fresh AriaSession (just like a chat would)
    2. Generates a self-prompt (your upgraded self-prompting mechanism)
    3. Processes the self-prompt through the agent
    4. Archives the session for memory consolidation
    """
    logger.info(f"Heartbeat started (interval: {shared.heartbeat_interval_seconds}s)")
    
    while True:
        try:
            # Wait for the interval
            # asyncio.sleep is NON-BLOCKING - this is the key difference from
            # time.sleep(). While this coroutine sleeps, the WebSocket server
            # and other tasks continue running normally.
            await asyncio.sleep(shared.heartbeat_interval_seconds)
            
            logger.info("Heartbeat firing...")
            
            # Create an ephemeral session for this heartbeat cycle
            session = AriaSession(shared, session_type="heartbeat")
            await session.initialize()
            
            # TODO: Generate the self-prompt.
            # This is your upgraded mechanism where ARIA poses a targeted
            # question to itself based on current context, recent memories,
            # and workspace state.
            self_prompt = await generate_self_prompt(shared)
            
            # Process the self-prompt through the full agent pipeline
            response = await session.process_message(self_prompt)
            
            # Archive for consolidation
            summary = session.get_session_summary()
            shared.completed_sessions.append(summary)
            
            logger.info("Heartbeat cycle complete.")
        
        except asyncio.CancelledError:
            # This fires when the server is shutting down (see main()).
            # CancelledError is how asyncio tells a task "time to stop."
            logger.info("Heartbeat shutting down gracefully.")
            break
        
        except Exception as e:
            # Don't let a single heartbeat failure kill the loop.
            # Log it and keep going.
            logger.error(f"Heartbeat error: {e}", exc_info=True)
            # Wait a bit before retrying to avoid tight error loops
            await asyncio.sleep(10)


async def generate_self_prompt(shared: SharedResources) -> str:
    """
    Your self-prompting mechanism. This is the piece that makes ARIA's
    heartbeat targeted rather than generic.
    
    TODO: This is where your self-prompt agent runs - the one that
    examines current workspace state, recent memories, and generates
    a thoughtful question for ARIA to explore.
    """
    return "TODO: implement self-prompt generation"


# =============================================================================
# MEMORY CONSOLIDATION LOOP (Proactive)
# =============================================================================
# Periodically takes completed sessions and summarizes them into
# long-term memory (ChromaDB). This is how experiences from individual
# sessions become available to future sessions.
# =============================================================================

async def consolidation_loop(shared: SharedResources):
    """
    Memory consolidation loop. Periodically processes completed sessions
    and writes summaries to the shared vector DB.
    
    This is what makes ARIA's experiences persist. Without this,
    each session would be isolated - with it, what ARIA learns in
    a heartbeat cycle can inform the next chat session.
    """
    logger.info(f"Consolidation started (interval: {shared.consolidation_interval_seconds}s)")
    
    while True:
        try:
            await asyncio.sleep(shared.consolidation_interval_seconds)
            
            # Grab all completed sessions that haven't been consolidated yet
            if not shared.completed_sessions:
                continue
            
            # Take the sessions and clear the list
            # (This is safe in asyncio because only one coroutine runs at a time
            # within a single event loop - no race conditions here.)
            sessions_to_process = shared.completed_sessions.copy()
            shared.completed_sessions.clear()
            
            logger.info(f"Consolidating {len(sessions_to_process)} sessions...")
            
            for session_data in sessions_to_process:
                # TODO: Summarize the session and write to ChromaDB
                # summary = await summarize_session(session_data)
                # shared.chroma_client.add(
                #     documents=[summary],
                #     metadatas=[{"type": session_data["type"]}],
                #     ids=[generate_id()],
                # )
                pass
            
            logger.info("Consolidation complete.")
        
        except asyncio.CancelledError:
            logger.info("Consolidation shutting down gracefully.")
            break
        
        except Exception as e:
            logger.error(f"Consolidation error: {e}", exc_info=True)
            await asyncio.sleep(10)


# =============================================================================
# MAIN: THE ENTRY POINT
# =============================================================================
# This is where everything comes together. One function starts everything,
# and everything shuts down cleanly when you Ctrl+C.
#
# HOW asyncio.gather WORKS:
# -------------------------
# asyncio.gather() takes multiple coroutines and runs them concurrently
# in the same event loop. It's NOT parallel (not multiple CPU cores) -
# it's concurrent (they take turns). When one coroutine hits an "await"
# (like await asyncio.sleep() or await websocket.recv()), it pauses and
# lets another coroutine run.
#
# Think of it like a single chef working multiple dishes. While the pasta
# is boiling (await sleep), the chef chops vegetables (runs another
# coroutine). Nothing happens truly simultaneously, but everything
# makes progress because most of the time is spent waiting.
#
# For ARIA this means:
# - While the heartbeat is sleeping between cycles, the WebSocket
#   server is handling chat messages normally
# - While waiting for an incoming WebSocket message, the heartbeat
#   can fire and do its thinking
# - While consolidation is processing, everything else continues
#
# They share the same process and memory space, which is WHY shared
# resources work without any IPC or message passing.
# =============================================================================

async def main():
    """
    Starts all ARIA subsystems and runs until interrupted.
    """
    # Step 1: Initialize shared resources (once, at startup)
    shared = initialize_shared_resources()
    
    # Step 2: Create the WebSocket server
    # This returns a server object that will handle connections using
    # our handle_chat_connection function. Each connection gets its
    # own call to that function (and therefore its own AriaSession).
    #
    # We pass `shared` via a lambda/closure so every connection
    # has access to the shared resources.
    server = await websockets.serve(
        lambda ws: handle_chat_connection(ws, shared),
        "localhost",
        8765,
    )
    logger.info("WebSocket server running on ws://localhost:8765")
    
    # Step 3: Start background tasks
    # asyncio.create_task() schedules a coroutine to run in the background.
    # It starts running immediately (well, at the next await point) and
    # continues independently. We keep references to the tasks so we can
    # cancel them during shutdown.
    heartbeat_task = asyncio.create_task(heartbeat_loop(shared))
    consolidation_task = asyncio.create_task(consolidation_loop(shared))
    
    logger.info("=" * 50)
    logger.info("ARIA is alive.")
    logger.info("  WebSocket: ws://localhost:8765")
    logger.info(f"  Heartbeat: every {shared.heartbeat_interval_seconds}s")
    logger.info(f"  Consolidation: every {shared.consolidation_interval_seconds}s")
    logger.info("  Press Ctrl+C to shut down.")
    logger.info("=" * 50)
    
    # Step 4: Wait forever (until Ctrl+C)
    # We need to keep main() alive so the background tasks and server
    # continue running. There are several ways to do this:
    try:
        # Option A: Wait for background tasks (they run forever, so this
        # effectively means "wait until something breaks or is cancelled")
        await asyncio.gather(heartbeat_task, consolidation_task)
    
    except asyncio.CancelledError:
        # This fires when we get a Ctrl+C (see below)
        pass
    
    finally:
        # Step 5: Graceful shutdown
        # Cancel background tasks. This sends CancelledError to each task,
        # which they catch in their except blocks above.
        logger.info("Shutting down ARIA...")
        
        heartbeat_task.cancel()
        consolidation_task.cancel()
        
        # Wait for them to finish their cleanup
        # return_exceptions=True means "don't raise if they error during cleanup"
        await asyncio.gather(heartbeat_task, consolidation_task, return_exceptions=True)
        
        # Close the WebSocket server
        server.close()
        await server.wait_closed()
        
        # TODO: Final consolidation pass - summarize any remaining sessions
        # before shutting down, so nothing is lost.
        if shared.completed_sessions:
            logger.info(f"Consolidating {len(shared.completed_sessions)} remaining sessions...")
            # ... process remaining sessions ...
        
        # TODO: Close ChromaDB client, clean up resources
        
        logger.info("ARIA has shut down.")


# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================
# asyncio.run() creates an event loop, runs main() in it, and handles
# Ctrl+C by cancelling all tasks. This is the standard way to start
# an async Python program.
# =============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # asyncio.run already handles this, but just in case
        logger.info("Interrupted.")
