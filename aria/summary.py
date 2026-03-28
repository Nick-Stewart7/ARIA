import os
from datetime import date
from datetime import timedelta
from pathlib import Path

from aria.subagents.session_summary import summary_agent
from aria.memory_manager import MemoryManager

_ROOT = Path(__file__).parent.parent.resolve()

def calc_yesterday():
    today = date.today()
    yesterday = today - timedelta(days=1)
    return yesterday

def get_session_ids():
    yesterday = calc_yesterday()
    all_entries = os.listdir(_ROOT / "memory" / "sessions" / str(yesterday))
    return all_entries

def run_memory_consolidation():
    memory_manager = MemoryManager()

    session_ids = get_session_ids()

    for session in session_ids:
        print(session)
        memory_list = summary_agent(session)
        for memory in memory_list:
            memory_manager.store(session_id = session, content = memory)



if __name__ == "__main__":
    run_memory_consolidation()