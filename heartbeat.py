# Client
import asyncio
import websockets
import json
import time

async def send_event():
    async with websockets.connect("ws://localhost:8765") as ws:
        await ws.send(json.dumps({"type": "heartbeat", "entity_id": "system", "task_id": "heartbeat", "time": time.time(), "data": "Check your task list and journal for any updates."}))
        response = await ws.recv()
        print(response)  # {"status": "queued"}

if __name__ == "__main__":
    while True:
        asyncio.run(send_event())
        time.sleep(300)  # Wait for 60 seconds before sending the next heartbeat