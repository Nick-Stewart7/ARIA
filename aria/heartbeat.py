import asyncio
import logging
import os

from aria.agent import run_turn
from aria.subagents.possibility_drive import run_possibility_drive

logger = logging.getLogger("aria")

HEARTBEAT_SESSION_ID = os.getenv("HEARTBEAT_SESSION_ID", "heartbeat")
HEARTBEAT_USER_ID = "aria"


async def heartbeat_loop():
    """Background task: ARIA prompts itself on a timer, in its own stable session.

    Runs alongside the server in the same process — no separate process, no
    HTTP round-trip to itself. Shares run_turn with the /chat route, just
    self-triggered instead of triggered by an incoming request.
    """
    period_seconds = int(os.getenv("HEARTBEAT_PERIOD", "10")) * 60
    logger.info(f"Heartbeat started (every {period_seconds}s, session={HEARTBEAT_SESSION_ID})")

    while True:
        try:
            await asyncio.sleep(period_seconds)

            # run_possibility_drive() is a blocking LLM call — push it off the
            # event loop so it doesn't stall chat requests while it runs.
            self_prompt = await asyncio.to_thread(run_possibility_drive)
            logger.info(f"Heartbeat firing: {self_prompt}")

            response = await run_turn(
                session_id=HEARTBEAT_SESSION_ID,
                user_id=HEARTBEAT_USER_ID,
                user_input=self_prompt,
            )
            logger.info(f"Heartbeat response: {response}")

        except asyncio.CancelledError:
            logger.info("Heartbeat shutting down.")
            break
        except Exception as e:
            logger.error(f"Heartbeat error: {e}", exc_info=True)
