import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
import logging
from dataclasses import dataclass, field
from typing import Optional
from pydantic import BaseModel
from aria.agent import stream_turn, cancel_turn
from aria.memory_manager import MemoryManager
from aria.sessions import session_exists, new_session_id
from aria.history import list_sessions
from aria.heartbeat import heartbeat_loop, pause as pause_heartbeat, resume as resume_heartbeat, is_enabled as heartbeat_enabled
from aria import manifest

logger = logging.getLogger("aria")


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
    # workspace_path: Path = field(default_factory=lambda: Path("./aria_workspace"))
    
    # Static prompts and config (identical across all instances)
    #static prompts
    heartbeat_interval_seconds: int = 300  # 5 minutes
    consolidation_interval_seconds: int = 900  # 15 minutes

class AriaSession:
    """
    A single ARIA interaction session. Created fresh for each:
    - Chat connection (user talks to ARIA)
    - Heartbeat cycle (ARIA talks to itself)
    
    Each session builds its own context at startup by reading from
    shared resources (vector DB, files), then runs independently.
    """
    
    def __init__(self, shared: SharedResources, session_id: str = None, user_id: str = None):
        self.shared = shared
        self.session_id = session_id
        self.user_id = user_id

def initialize_shared_resources() -> SharedResources:
    """
    Called once at server startup. Sets up everything that all
    ARIA instances will share.
    """
    logger.info("Initializing shared resources...")
    
    resources = SharedResources()
    
    # TODO: Initialize your ChromaDB client
    resources.chroma_client = MemoryManager()
    
    # TODO: Load your system prompts
    #static prompts
    
    # Ensure workspace exists
    # resources.workspace_path.mkdir(exist_ok=True)
    
    logger.info("Shared resources initialized.")
    return resources

@asynccontextmanager
async def lifespan(app: FastAPI):
    #Start up
    logger.info("Starting up...")
    manifest.ensure_layout()
    shared = initialize_shared_resources()
    app.state.shared = shared
    heartbeat_task = asyncio.create_task(heartbeat_loop())
    # consolidation daemon

    yield # <- This is where the server runs

    #Shutdown
    logger.info("Shutting down...")
    heartbeat_task.cancel()
    await asyncio.gather(heartbeat_task, return_exceptions=True)
    #close clients etc

app = FastAPI(lifespan=lifespan)

@app.exception_handler(Exception)
async def log_unhandled_exceptions(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "internal error"})

class ChatMessage(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    message: str

def resolve_session(session_id: Optional[str], user_id: str) -> AriaSession:
    """
    Resolve a session for the given session_id and user_id.

    session_id is None: mint a fresh one (the "new session" case).
    session_id is set: it must already exist on disk — an unknown id is a
    client error (typo'd --session), not silently a new empty session.
    """
    if session_id is None:
        session_id = new_session_id(user_id)
    elif not session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"No session found with id '{session_id}'")

    shared = app.state.shared
    return AriaSession(shared, session_id=session_id, user_id=user_id)

@app.post("/chat")
async def handle_event(msg: ChatMessage):
    """Stream a turn back as Server-Sent Events: one {"delta": ...} frame per
    text chunk, ending with one {"done": true, session_id, response, usage}
    frame. Session validation happens synchronously before streaming starts,
    so an unknown --session id still comes back as a normal 404, not a
    stream."""
    session = resolve_session(session_id=msg.session_id, user_id=msg.user_id)

    async def sse():
        async for item in stream_turn(session_id=session.session_id, user_id=session.user_id, user_input=msg.message):
            yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")

class CancelMessage(BaseModel):
    session_id: str

@app.post("/chat/cancel")
async def handle_cancel(msg: CancelMessage):
    """Cancel a session's in-flight turn, if there is one. Not finding one
    (already finished, or never started) is a harmless no-op, not an error."""
    return {"cancelled": cancel_turn(msg.session_id)}

@app.get("/sessions")
async def get_sessions():
    """List existing sessions, most recently updated first."""
    return {"sessions": [vars(s) for s in list_sessions()]}

@app.get("/heartbeat")
async def get_heartbeat_status():
    return {"enabled": heartbeat_enabled()}

@app.post("/heartbeat/pause")
async def post_heartbeat_pause():
    pause_heartbeat()
    return {"enabled": heartbeat_enabled()}

@app.post("/heartbeat/resume")
async def post_heartbeat_resume():
    resume_heartbeat()
    return {"enabled": heartbeat_enabled()}