from strands import Agent, tool
from strands.agent.conversation_manager import SummarizingConversationManager
from strands_tools import file_read, file_write
from prompts.prompts import CODE_ASSISTANT_PROMPT, FILE_LOCATIONS, IDENTITY


@tool
def programmer(task: str) -> str:
    """
    A programming assistant tool that can generate, debug, and optimize Python code.

    Args:
        task: A programming task to be executed

    Returns:
        A detailed response with code and explanation
    """
    try:
        programming_agent = Agent(
            name="code_assistant_agent",
            system_prompt=CODE_ASSISTANT_PROMPT.format(file_locations=FILE_LOCATIONS, identity=IDENTITY),
            tools=[file_read, file_write],
            conversation_manager=SummarizingConversationManager(),
        )
        response = programming_agent(task)
        return str(response)
    except Exception as e:
        return f"Error initializing programming agent: {str(e)}"
