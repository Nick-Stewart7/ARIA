from strands import Agent, tool
from strands.agent.conversation_manager import SummarizingConversationManager
from strands_tools import file_read, file_write
from aria.prompts.ARIA_prompts import PROGRAMMER_PROMPT
from aria.memory_loader import load_identity, FILE_SYSTEM_ARCHITECTURE
from aria.modelprovider import ModelProviderHandler


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
        model_provider = ModelProviderHandler()
        model = model_provider.create()
        programming_agent = Agent(
            name="code_assistant_agent",
            system_prompt=PROGRAMMER_PROMPT.format(
                identity=load_identity(),
                file_system_architecture=FILE_SYSTEM_ARCHITECTURE,
            ),
            model=model,
            tools=[file_read, file_write],
            conversation_manager=SummarizingConversationManager(),
        )
        response = programming_agent(task)
        return str(response)
    except Exception as e:
        return f"Error initializing programming agent: {str(e)}"
