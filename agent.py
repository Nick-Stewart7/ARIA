from pathlib import Path
from datetime import datetime

from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.session.file_session_manager import FileSessionManager
from strands_tools import file_read, file_write

from subagents.planner import planner
from subagents.programmer import programmer
from subagents.researcher import researcher_agent
from subagents.observer import observer
from subagents.reflector import reflector
from prompts.ARIA_prompts import ORCHESTRATOR_PROMPT
from memory_loader import load_identity, load_user_context, FILE_SYSTEM_ARCHITECTURE

_ROOT = Path(__file__).parent


def create_aria_instance(session_id: str, user_id: str = "user"):
    """Factory function to create an instance of Aria."""
    today = datetime.today().strftime('%Y-%m-%d')

    prompt = ORCHESTRATOR_PROMPT.format(
        identity=load_identity(),
        user_context=load_user_context(user_id),
        file_system_architecture=FILE_SYSTEM_ARCHITECTURE,
    )

    aria = Agent(
        name="ARIA",
        system_prompt=prompt,
        tools=[file_read, file_write, programmer, researcher_agent, observer, reflector, planner],
        conversation_manager=SummarizingConversationManager(),
        session_manager=FileSessionManager(
            session_id=session_id,
            storage_dir=_ROOT / "memory" / "sessions" / {today},
        ),
        callback_handler=None
    )
    return aria
