from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.session.file_session_manager import FileSessionManager
from strands_tools import file_read, file_write, shell, cron

from aria.tools.memory_tools import store, recall

from aria.subagents.programmer import programmer
from aria.subagents.researcher import researcher_agent
from aria.prompts.ARIA_prompts import ORCHESTRATOR_PROMPT
from aria.context import gather
from aria.modelprovider import ModelProviderHandler
from aria.sessions import sessions_root


def create_aria_instance(session_id: str, user_id: str = "user"):
    """Factory function to create an instance of Aria."""
    model_provider = ModelProviderHandler()
    model = model_provider.create()

    prompt = ORCHESTRATOR_PROMPT.format(**gather(user_id).slots())

    aria = Agent(
        name="ARIA",
        system_prompt=prompt,
        model=model,
        tools=[file_read, file_write, shell, cron, store, recall, programmer, researcher_agent],
        conversation_manager=SummarizingConversationManager(),
        session_manager=FileSessionManager(
            session_id=session_id,
            storage_dir=sessions_root()
        ),
        callback_handler=None
    )
    return aria


async def run_turn(session_id: str, user_id: str, user_input: str) -> str:
    """Build an ARIA agent for this session and run one turn, returning the reply.

    The one place that drains stream_async and pulls out the result — heartbeat
    goes through this (never streams to anyone). The streaming chat path is
    stream_turn() below, which shares the same agent-creation seam.
    """
    aria = create_aria_instance(session_id=session_id, user_id=user_id)
    result = None
    async for chunk in aria.stream_async(user_input):
        if "result" in chunk:
            result = chunk["result"]
    return str(result)


# Agents with a turn currently in flight, keyed by session_id -- lets
# cancel_turn() reach into a specific in-progress turn from a separate
# request (each turn builds a brand new Agent instance, so there's no
# long-lived agent object to hold a reference to otherwise).
_active_agents: dict[str, Agent] = {}


async def stream_turn(session_id: str, user_id: str, user_input: str):
    """Like run_turn, but yields incremental text deltas as they generate
    instead of only returning the final result -- the chat/TUI streaming path.

    Cancellable mid-stream via cancel_turn(session_id): Strands persists a
    clean user/assistant pair either way ("Cancelled by user" text, zero
    token usage on cancel), so the session is always left safe to continue
    afterward -- no special-casing needed here.
    """
    aria = create_aria_instance(session_id=session_id, user_id=user_id)
    _active_agents[session_id] = aria
    yield {"session_id": session_id}  # first frame, always -- so a caller can
    # cancel a brand-new session's very first turn before it's ever seen a
    # delta, not just one it already knew the id for.
    result = None
    try:
        async for chunk in aria.stream_async(user_input):
            if "data" in chunk:
                yield {"delta": chunk["data"]}
            if "result" in chunk:
                result = chunk["result"]
    finally:
        _active_agents.pop(session_id, None)

    response = str(result)

    usage = result.metrics.accumulated_usage if result else {}
    yield {
        "done": True,
        "session_id": session_id,
        "response": response,
        "usage": {
            "inputTokens": usage.get("inputTokens", 0),
            "outputTokens": usage.get("outputTokens", 0),
            "totalTokens": usage.get("totalTokens", 0),
        },
    }


def cancel_turn(session_id: str) -> bool:
    """Cancel the in-flight turn for session_id, if there is one.

    Returns whether an active agent was found -- callers should treat "not
    found" as a harmless no-op (the turn already finished, or never started),
    not an error.
    """
    aria = _active_agents.get(session_id)
    if aria is None:
        return False
    aria.cancel()
    return True
