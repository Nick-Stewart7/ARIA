# Client
import asyncio
import websockets
import json
import time
import os

from aria.subagents.possibility_drive import run_possibility_drive

async def send_event():
    HOST = os.getenv("HOST", "localhost")
    PORT = os.getenv("PORT", "65535")
    async with websockets.connect(f"ws://{HOST}:{PORT}", ping_timeout=None) as ws:
        # generate input
        self_prompt = run_possibility_drive()
        print(f"\033[36m {self_prompt}\033[0m")
        await ws.send(json.dumps({"type": "heartbeat", "entity_id": "system", "task_id": "heartbeat", "time": time.time(), "data": f"{self_prompt}"}))
        # Receive until we get a final result or error
        while True:
            message = await ws.recv()
            data = json.loads(message)
            if data.get("type") == "status":
                # print(f"  [{data.get('message')}]")
                continue
            elif data.get("type") == "result":
                print(f"\n{data.get('reply')}\n")
                break
            elif data.get("type") == "error":
                print(f"\n[error] {data.get('error')}\n")
                break

if __name__ == "__main__":
    i = 0
    while True:
        asyncio.run(send_event())
        time.sleep(600)  # Wait for 10 minutes before sending the next heartbeat
        if i == 6:
            break
        i+=1