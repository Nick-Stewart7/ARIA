from strands import Agent, tool
from strands.agent.conversation_manager import SummarizingConversationManager
from strands_tools import file_read
from aria.prompts.ARIA_prompts import OBSERVER_PROMPT
from aria.memory_loader import load_identity, FILE_SYSTEM_ARCHITECTURE
from aria.modelprovider import ModelProviderHandler


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
        model_provider = ModelProviderHandler()
        model = model_provider.create()

        agent = Agent(
            name="observer_agent",
            system_prompt=OBSERVER_PROMPT.format(
                identity=load_identity(),
                file_system_architecture=FILE_SYSTEM_ARCHITECTURE,
            ),
            model=model,
            tools=[file_read],
            conversation_manager=SummarizingConversationManager(),
        )
        response = agent(signal)
        return str(response)
    except Exception as e:
        return f"Error runing observer agent: {str(e)}"
