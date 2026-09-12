from strands import Agent

from aria.prompts.ARIA_prompts import POSSIBILITY_DRIVE
from aria.context import gather
from aria.sessions import HEARTBEAT_USER_ID
from aria.modelprovider import ModelProviderHandler


def run_possibility_drive():
    """Generate the input for ARIA's next autonomous cycle.

    Gets the same gathered context a chat turn does -- identity, file
    system, recent digests -- so it grounds the next cycle in what's
    actually in memory instead of reading files to find out. No tools.
    """
    try:
        model_provider = ModelProviderHandler()
        model = model_provider.create()

        prompt = POSSIBILITY_DRIVE.format(**gather(HEARTBEAT_USER_ID).slots())

        possibility_drive = Agent(
            name="ARIA",
            system_prompt=prompt,
            model=model,
            tools=[],
        )

        response = possibility_drive("Generate the input for ARIA's next autonomous cycle")
        return str(response)
    except Exception as e:
        return f"Error running possibility drive: {str(e)}"
