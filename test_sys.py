import asyncio
import websockets
import sys
import ssl

async def test_auth_and_cmd():
    # Bypass verification for the self-signed test certificate
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with websockets.connect("wss://localhost:8765", ssl=ssl_context) as ws:
            # 1. Authenticate
            print("Sending AUTH...")
            await ws.send("AUTH:admin:password123")
            response = await ws.recv()
            print(f"Auth Response: {response}")
            if not response.startswith("AUTH_SUCCESS"):
                print("Failed!")
                sys.exit(1)
            
            # 2. Send Command
            print("Sending CMD...")
            await ws.send("CMD:admin:fan1:ON")
            
            # 3. Wait for Responses
            for _ in range(3):
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    print(f"Received: {msg}")
                    if msg.startswith("STATUS:fan1:ON"):
                        print("SUCCESS!")
                        break
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"Connection Error: {e}")

asyncio.run(test_auth_and_cmd())
