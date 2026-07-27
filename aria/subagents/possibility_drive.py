from pathlib import Path
from datetime import datetime

from strands import Agent
from strands_tools import file_read, file_write

from aria.prompts.ARIA_prompts import POSSIBILITY_DRIVE
from aria.memory_loader import load_identity, FILE_SYSTEM_ARCHITECTURE
from aria.modelprovider import ModelProviderHandler


def run_possibility_drive():
    """Runs self prompt generation"""
    try:
        model_provider = ModelProviderHandler()
        model = model_provider.create()
        today = datetime.today().strftime('%Y-%m-%d')

        prompt = POSSIBILITY_DRIVE.format(
            identity=load_identity(),
            file_system_architecture=FILE_SYSTEM_ARCHITECTURE
        )

        print(f"\035[36m {prompt}\033[0m")

        probability_drive = Agent(
            name="ARIA",
            system_prompt=prompt,
            model=model,
            tools=[file_read, file_write]
        )

        response = probability_drive("Generate the input for ARIA's next autonomous cycle")
        return str(response)
    except Exception as e:
        return f"Error running probability drive: {str(e)}"