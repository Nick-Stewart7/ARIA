# Client
import asyncio
import websockets
import json
import time


async def chat():
    async with websockets.connect("ws://localhost:8765", ping_timeout=None) as ws:
        print("Connected to ARIA. Type 'exit' to quit.\n")
        while True:
            user_input = input('\u233e ')
            if user_input.strip().lower() in ('exit', 'quit'):
                break

            await ws.send(json.dumps({
                "type": "user",
                "user_id": "Nick",
                "conversation_id": "test",
                "time": time.time(),
                "data": user_input
            }))

            # Receive until we get a final result or error
            while True:
                message = await ws.recv()
                data = json.loads(message)
                if data.get("type") == "status":
                    print(f"  [{data.get('message')}]")
                elif data.get("type") == "result":
                    print(f"\n{data.get('reply')}\n")
                    break
                elif data.get("type") == "error":
                    print(f"\n[error] {data.get('error')}\n")
                    break


if __name__ == "__main__":
    asyncio.run(chat())
