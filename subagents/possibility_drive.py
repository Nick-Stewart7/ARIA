from pathlib import Path
from datetime import datetime

from strands import Agent
from strands_tools import file_read, file_write

from prompts.ARIA_prompts import POSSIBILITY_DRIVE
from memory_loader import load_identity, load_related_memories, FILE_SYSTEM_ARCHITECTURE

_ROOT = Path(__file__).parent


def run_possibility_drive():
    """Runs self prompt generation"""
    try:
        today = datetime.today().strftime('%Y-%m-%d')

        prompt = POSSIBILITY_DRIVE.format(
            identity=load_identity(),
            file_system_architecture=FILE_SYSTEM_ARCHITECTURE,
            memories=load_related_memories(f"Memories about ARIA, goals, projects, and beliefs. Include relevant recent memories as well. Today is {today}.")
        )

        print(f"\035[36m {prompt}\033[0m")

        probability_drive = Agent(
            name="ARIA",
            system_prompt=prompt,
            tools=[file_read, file_write]
        )

        response = probability_drive("Generate the input for ARIA's next autonomous cycle")
        return str(response)
    except Exception as e:
        return f"Error running probability drive: {str(e)}"