from strands import tool

from aria.history import render_turns


@tool
def read_session(session_id: str, start_turn: int = 0, max_turns: int = 10) -> str:
    """Read part of a session's history as turns: the input, each tool call
    ARIA made (name, arguments, result size), and the reply. The first line
    says how many turns the session has and which start_turn to continue from.

    Args:
        session_id: the session to read
        start_turn: first turn to return, 0-based
        max_turns: how many turns to return in this call
    """
    return render_turns(session_id, start_turn, max_turns)
