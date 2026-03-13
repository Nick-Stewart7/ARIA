from pathlib import Path
from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.session.file_session_manager import FileSessionManager
from strands_tools import file_read, file_write, current_time
from tools.web_search import web_search
from prompts.ARIA_prompts import SUMMARY_PROMPT
from memory_loader import _ROOT, load_identity, FILE_SYSTEM_ARCHITECTURE
from output_models.models import Memory_Output

_ROOT = Path(__file__).parent

def summary_agent(session_id: str) -> str:
    """
    A memory consolidation tool that can extract important long-term memories from recent experiences.

    Args:
        session_id: The ID of the session to review for memory extraction

    Returns:
        A detailed yet concise summary
    """
    try:
        agent = Agent(
            name="summary_agent",
            system_prompt=SUMMARY_PROMPT.format(
                identity=load_identity(),
                file_system_architecture=FILE_SYSTEM_ARCHITECTURE,
            ),
            session_manager=FileSessionManager(
                session_id=session_id,
                storage_dir=_ROOT / "memory" / "summaries",
            ),
            tools=[current_time],
            conversation_manager=SummarizingConversationManager(),
            structured_output_model=Memory_Output
        )
        response = agent("Review the current session and extract important long-term memories.")

        memory_list = response.structured_output.memories
        return memory_list
    except Exception as e:
        return f"Error initializing summary agent: {str(e)}"
