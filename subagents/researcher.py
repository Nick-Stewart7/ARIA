from strands import Agent, tool
from strands.agent.conversation_manager import SummarizingConversationManager
from strands_tools import file_read, file_write, current_time
from tools.web_search import web_search
from prompts.prompts import RESEARCHER_PROMPT, FILE_LOCATIONS, IDENTITY


@tool
def researcher_agent(query: str) -> str:
    """
    A research assistant tool that can perform web searches, read and write files, and access the current time.

    Args:
        query: A research query or task to be executed

    Returns:
        A detailed response with research findings, relevant information, and actionable insights
    """
    try:
        agent = Agent(
            name="researcher_agent",
            system_prompt=RESEARCHER_PROMPT.format(file_locations=FILE_LOCATIONS, identity=IDENTITY),
            tools=[web_search, file_read, file_write, current_time],
            conversation_manager=SummarizingConversationManager(),
        )

        response = agent(query)
        return str(response)
    except Exception as e:
        return f"Error initializing researcher agent: {str(e)}"
