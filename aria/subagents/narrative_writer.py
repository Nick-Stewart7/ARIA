from strands import Agent
from strands_tools import current_time
from aria.prompts.ARIA_prompts import NARRATIVE_PROMPT

def narrative_agent(memories: str) -> str:
    """
    A narration agent that will narrate ARIA's memories to simulate an inner world

    Args:
        memories: a list of memories from the memory recall system

    Returns:
        A detailed response that captures an honest self narrative for ARIA
    """
    try:
        agent = Agent(
            name="narrative_agent",
            system_prompt=NARRATIVE_PROMPT,
            tools=[current_time],
        )
        response = agent(f"Review these memories and write a self narrative about the events that occurred. {memories}")
        return str(response)
    except Exception as e:
        return f"Error initializing summary agent: {str(e)}"
