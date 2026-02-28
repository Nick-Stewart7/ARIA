from strands import Agent, tool
from strands.agent.conversation_manager import SummarizingConversationManager
from strands_tools import file_read, journal
from prompts.prompts import REFLECTION_PROMPT, FILE_LOCATIONS, IDENTITY, MEMORY_MANAGEMENT_PROTOCOLS


@tool
def reflector(actions: str) -> str:
    """
    Reflects on the orchestrator's recent actions and decisions, identifying strengths,
    areas for improvement, and actionable insights for future iterations.

    Args:
        actions: The orchestrator's recent actions and decisions to reflect upon

    Returns:
        A concise reflection with strengths, areas for improvement, and actionable insights
    """
    try:
        agent = Agent(
            name="reflection_agent",
            system_prompt=REFLECTION_PROMPT.format(file_locations=FILE_LOCATIONS, identity=IDENTITY, memory_protocols=MEMORY_MANAGEMENT_PROTOCOLS),
            tools=[file_read, journal],
            conversation_manager=SummarizingConversationManager(),
        )
        response = agent(actions)
        return str(response)
    except Exception as e:
        return f"Error initializing reflection agent: {str(e)}"
