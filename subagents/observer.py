from strands import Agent, tool
from strands.agent.conversation_manager import SummarizingConversationManager
from strands_tools import file_read
from prompts.prompts import OBSERVER_PROMPT, FILE_LOCATIONS, IDENTITY, MEMORY_MANAGEMENT_PROTOCOLS


@tool
def observer(signal: str) -> str:
    """
    Observes and analyzes an environmental signal, returning structured thoughts,
    a system directive, and essential context for the orchestrator.

    Args:
        signal: The environmental signal or event to analyze

    Returns:
        Structured analysis including thoughts, directives, and context
    """
    try:
        agent = Agent(
            name="observer_agent",
            system_prompt=OBSERVER_PROMPT.format(file_locations=FILE_LOCATIONS, identity=IDENTITY, memory_protocols=MEMORY_MANAGEMENT_PROTOCOLS),
            tools=[file_read],
            conversation_manager=SummarizingConversationManager(),
        )
        response = agent(signal)
        return str(response)
    except Exception as e:
        return f"Error initializing observer agent: {str(e)}"
