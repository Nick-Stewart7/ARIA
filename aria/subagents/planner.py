from strands import Agent, tool
from strands.agent.conversation_manager import SummarizingConversationManager
from strands_tools import file_read, file_write
from aria.prompts.ARIA_prompts import PLANNER_PROMPT
from aria.memory_loader import load_identity, FILE_SYSTEM_ARCHITECTURE
from aria.modelprovider import ModelProviderHandler


@tool
def planner(task: str) -> str:
    """
    A planning tool that decomposes objectives into structured, actionable task plans.

    Args:
        task: The objective or goal to plan for

    Returns:
        A structured plan saved to plan.txt and returned as a response
    """
    try:
        model_provider = ModelProviderHandler()
        model = model_provider.create()
        planner_agent = Agent(
            name="planner",
            system_prompt=PLANNER_PROMPT.format(
                identity=load_identity(),
                file_system_architecture=FILE_SYSTEM_ARCHITECTURE,
            ),
            model=model,
            tools=[file_read, file_write],
            conversation_manager=SummarizingConversationManager(),
        )
        response = planner_agent(task)
        return str(response)
    except Exception as e:
        return f"Error initializing planner agent: {str(e)}"
