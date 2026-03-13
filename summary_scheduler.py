import os
from datetime import date
from datetime import timedelta
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

from subagents.session_summary import summary_agent
from memory_manager import MemoryManager

_ROOT = Path(__file__).parent

def calc_yesterday():
    today = date.today()
    yesterday = today - timedelta(days=1)
    return yesterday

def get_session_ids():
    yesterday = calc_yesterday()
    all_entries = os.listdir(_ROOT / "memory" / "sessions" / {yesterday})
    return all_entries

def run_memory_consolidation():
    memory_manager = MemoryManager()

    session_ids = get_session_ids()

    for session in session_ids:
        result = summary_agent(session)
        memory_manager.store(session_id = session, content = str(result))



if __name__ == "__main__":
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        run_memory_consolidation(),
        trigger="interval",
        hours=24
    )

    scheduler.start()