from strands import Agent, tool
from strands.agent.conversation_manager import SummarizingConversationManager
from strands_tools import file_read, journal
from aria.prompts.ARIA_prompts import REFLECTOR_PROMPT
from aria.memory_loader import load_identity, FILE_SYSTEM_ARCHITECTURE
from aria.modelprovider import ModelProviderHandler


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
        model_provider = ModelProviderHandler()
        model = model_provider.create()
        agent = Agent(
            name="reflection_agent",
            system_prompt=REFLECTOR_PROMPT.format(
                identity=load_identity(),
                file_system_architecture=FILE_SYSTEM_ARCHITECTURE,
            ),
            model=model,
            tools=[file_read, journal],
            conversation_manager=SummarizingConversationManager(),
        )
        response = agent(actions)
        return str(response)
    except Exception as e:
        return f"Error initializing reflection agent: {str(e)}"
