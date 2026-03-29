from datetime import datetime
from pathlib import Path
import os

from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.session.file_session_manager import FileSessionManager
from strands_tools import file_read, file_write

from aria.subagents.planner import planner
from aria.subagents.programmer import programmer
from aria.subagents.researcher import researcher_agent
from aria.subagents.observer import observer
from aria.subagents.reflector import reflector
from aria.prompts.ARIA_prompts import ORCHESTRATOR_PROMPT
from aria.memory_loader import load_identity, load_user_context, load_related_memories, FILE_SYSTEM_ARCHITECTURE
from aria.modelprovider import ModelProviderHandler


def create_aria_instance(query, session_id: str, user_id: str = "user"):
    """Factory function to create an instance of Aria."""
    today = datetime.today().strftime('%Y-%m-%d')

    #todo: make session id dynamic based on conv id or task id, and user id for multi user support
    #todo: move session management to its own module and make it more robust with features like expiration, retrieval, etc. For now we just create a new session file for each run based on the date.
    SESSION_DIR = Path(os.getenv("SESSION_DIR", "sessions")) / str(today)

    model_provider = ModelProviderHandler()
    model = model_provider.create()

    prompt = ORCHESTRATOR_PROMPT.format(
        identity=load_identity(),
        user_context=load_user_context(user_id),
        file_system_architecture=FILE_SYSTEM_ARCHITECTURE,
        memories=load_related_memories(query)
    )

    print(f"\033[36m {prompt}\033[0m")

    aria = Agent(
        name="ARIA",
        system_prompt=prompt,
        model=model,
        tools=[file_read, file_write, programmer, researcher_agent, observer, reflector, planner],
        conversation_manager=SummarizingConversationManager(),
        session_manager=FileSessionManager(
            session_id=session_id,
            storage_dir=SESSION_DIR
        ),
        callback_handler=None
    )
    return aria
