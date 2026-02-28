from strands import Agent, tool
from strands.agent.conversation_manager import SummarizingConversationManager
from strands_tools import file_read, file_write
from prompts.prompts import PLANNER_PROMPT, FILE_LOCATIONS, IDENTITY


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
        planner_agent = Agent(
            name="planner",
            system_prompt=PLANNER_PROMPT.format(file_locations=FILE_LOCATIONS, identity=IDENTITY),
            tools=[file_read, file_write],
            conversation_manager=SummarizingConversationManager(),
        )
        response = planner_agent(task)
        return str(response)
    except Exception as e:
        return f"Error initializing planner agent: {str(e)}"
