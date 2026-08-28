from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.session.file_session_manager import FileSessionManager
from strands_tools import file_read, file_write, shell, cron

from aria.tools.memory_tools import store, recall

from aria.subagents.planner import planner
from aria.subagents.programmer import programmer
from aria.subagents.researcher import researcher_agent
from aria.subagents.observer import observer
from aria.subagents.reflector import reflector
from aria.prompts.ARIA_prompts import ORCHESTRATOR_PROMPT
from aria.memory_loader import load_identity, load_user_context, FILE_SYSTEM_ARCHITECTURE
from aria.modelprovider import ModelProviderHandler
from aria.sessions import sessions_root


def create_aria_instance(session_id: str, user_id: str = "user"):
    """Factory function to create an instance of Aria."""
    model_provider = ModelProviderHandler()
    model = model_provider.create()

    prompt = ORCHESTRATOR_PROMPT.format(
        identity=load_identity(),
        user_context=load_user_context(user_id),
        file_system_architecture=FILE_SYSTEM_ARCHITECTURE
    )

    print(f"\033[36m {prompt}\033[0m")

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

    The one place that drains stream_async and pulls out the result — chat
    and heartbeat both go through this instead of each doing it themselves.
    """
    aria = create_aria_instance(session_id=session_id, user_id=user_id)
    result = None
    async for chunk in aria.stream_async(user_input):
        if "result" in chunk:
            result = chunk["result"]
    return str(result)
