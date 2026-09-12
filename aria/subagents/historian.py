from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager
from aria.prompts.ARIA_prompts import HISTORIAN_PROMPT
from aria.context import gather
from aria.tools.history_tools import read_session
from aria.modelprovider import ModelProviderHandler

_FIRST_SECTION = "## What happened"


def historian(session_id: str, start_turn: int, end_turn: int, existing_digest: str = "") -> str:
    """
    A memory consolidation agent that digests a session's history into the compact record
    ARIA carries into later sessions.

    Same shape as the other sub-agents, with two differences on purpose: it is not a @tool,
    because the orchestrator never calls it (aria.digest does now, the consolidation daemon
    will later); and it lets errors raise, because an "Error ..." string returned here would
    be written to disk as a digest.

    Args:
        session_id: The session to digest
        start_turn: First turn not yet covered by the existing digest (0 for a fresh one)
        end_turn: Last completed turn to cover
        existing_digest: Body of the current digest, if any, to update rather than replace

    Returns:
        The digest markdown, starting at "## What happened"
    """
    model_provider = ModelProviderHandler()
    model = model_provider.create()
    agent = Agent(
        name="historian",
        system_prompt=HISTORIAN_PROMPT.format(**gather().slots()),
        model=model,
        tools=[read_session],
        conversation_manager=SummarizingConversationManager(),
        callback_handler=None,
    )

    task = (f"Digest session {session_id}: turns {start_turn}..{end_turn}. "
            f"Read them with read_session starting at start_turn={start_turn}.")
    if existing_digest:
        task += (f"\n\nThis is the current digest, covering turns 0..{start_turn - 1}. "
                 f"Update it with what the new turns add:\n\n{existing_digest}")

    response = str(agent(task))
    cut = response.find(_FIRST_SECTION)   # drop any preamble the model adds anyway
    return response[cut:].strip() if cut >= 0 else response.strip()
