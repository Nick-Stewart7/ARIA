import asyncio
import websockets
import json
from dotenv import load_dotenv
import logging
from pathlib import Path
from agent import create_aria_instance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ARIA')

load_dotenv()  # Load environment variables from .env file


class ARIAServer:
    def __init__(self):
        self.active_connections = set()
        self.task_queue = asyncio.Queue()

    def get_session_id(self, event):
        event_type = event.get('type', 'unknown')
        if event_type == 'heartbeat':
            return f"task-{event.get('task_id', 'auto')}"
        else:
            return f"conv-{event.get('conversation_id', 'default')}"

    async def run_aria(self, event, websocket):
        """Process a single event through ARIA and stream results back."""
        session_id = self.get_session_id(event)
        user_id = event.get("user_id", "user")
        logger.info(f"Processing event with session: {session_id}, user: {user_id}")

        aria = create_aria_instance(session_id, user_id=user_id)

        result = None
        active_tool = None
        async for chunk in aria.stream_async(f"event: {event}"):
            if "result" in chunk:
                result = chunk["result"]
            elif "current_tool_use" in chunk:
                tool_name = chunk["current_tool_use"].get("name")
                if tool_name and tool_name != active_tool:
                    active_tool = tool_name
                    logger.info(f"Tool call: {tool_name} | chunk: {chunk}")
                    await websocket.send(json.dumps({
                        "type": "status",
                        "message": f"using tool: {tool_name}"
                    }))

        logger.info(f"Result: {result}")
        await websocket.send(json.dumps({
            "type": "result",
            "reply": str(result)
        }))

    async def process_queue(self):
        """Background worker — drains the task queue and runs ARIA for each event."""
        logger.info("Queue processor started")
        while True:
            event, websocket = await self.task_queue.get()
            logger.info(f"Dequeued event: {event.get('type')}")
            try:
                await self.run_aria(event, websocket)
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Client disconnected before response could be sent")
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
                try:
                    await websocket.send(json.dumps({"type": "error", "error": str(e)}))
                except Exception:
                    pass
            finally:
                self.task_queue.task_done()

    async def handle_client(self, websocket):
        """Accept connections and queue incoming events — nothing more."""
        self.active_connections.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")

        try:
            async for message in websocket:
                try:
                    event = json.loads(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    await websocket.send(json.dumps({"type": "error", "error": "Invalid JSON"}))
                    continue

                logger.info(f"Queuing event: {event.get('type')}")
                await self.task_queue.put((event, websocket))

        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        finally:
            self.active_connections.discard(websocket)

    async def start(self, host="localhost", port=8765):
        # Start the background queue processor alongside the server
        asyncio.create_task(self.process_queue())

        async with websockets.serve(
            self.handle_client,
            host,
            port,
            max_size=10 * 1024 * 1024,  # 10 MB
            ping_interval=None,
        ):
            logger.info(f"ARIA v1 on ws://{host}:{port}")
            await asyncio.Future()


if __name__ == "__main__":
    server = ARIAServer()
    asyncio.run(server.start())
