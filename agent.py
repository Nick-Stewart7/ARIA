import os

from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.session.file_session_manager import FileSessionManager
from strands_tools import file_read, file_write

from subagents.planner import planner
from subagents.programmer import programmer
from subagents.researcher import researcher_agent
from subagents.observer import observer
from subagents.reflector import reflector
from prompts.prompts import ORCHESTRATOR_PROMPT, FILE_LOCATIONS, SUB_AGENTS, IDENTITY

def create_aria_instance(session_id: str, memory_context: str, soul: str):
    """Factory function to create an instance of Aria"""

    aria = Agent(
        name="ARIA",
        system_prompt=ORCHESTRATOR_PROMPT.format(memory_context=memory_context, file_locations=FILE_LOCATIONS, identity=IDENTITY, soul=soul, sub_agents=SUB_AGENTS),
        tools=[file_read, file_write, programmer, researcher_agent, observer, reflector, planner],
        conversation_manager=SummarizingConversationManager(),
        session_manager=FileSessionManager(session_id=session_id, storage_dir=os.path.expanduser("C:\\Users\\Nick\\OneDrive\\Desktop\\Div\\Projects\\ARIA\\memory")),
        callback_handler=None
    )
    return aria
