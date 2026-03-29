import asyncio
import websockets

async def test():
    async with websockets.connect("ws://127.0.0.1:8765") as websocket:
        await websocket.send("CMD:test_user:fan1:ON")
        response = await websocket.recv()
        print(response)

asyncio.run(test())
