import asyncio
import websockets

TCP_HOST = "127.0.0.1"
TCP_PORT = 9000

connected_websockets = set()

async def tcp_to_ws(tcp_reader):
    """ Reads from C TCP server and broadcasts to all WebSocket clients """
    while True:
        try:
            data = await tcp_reader.readline()
            if not data:
                print("TCP connection lost")
                break
            
            message = data.decode().strip()
            print(f"TCP -> WS: {message}")
            if connected_websockets:
                websockets.broadcast(connected_websockets, message)
        except Exception as e:
            print(f"TCP read error: {e}")
            break

async def handler(*args):
    """ Handles new WebSocket connections and forwards their messages to TCP """
    websocket = args[0]
    tcp_writer = args[-1]
    
    connected_websockets.add(websocket)
    print("New WebSocket client connected")
    try:
        async for message in websocket:
            print(f"WS -> TCP: {message}")
            tcp_writer.write((message + "\n").encode())
            await tcp_writer.drain()
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_websockets.remove(websocket)
        print("WebSocket client disconnected")

async def main():
    try:
        reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)
        writer.write(b"REGISTER_CLIENT\n")
        await writer.drain()
        print("Connected to C server.")
    except Exception as e:
        print(f"Could not connect to C server: {e}")
        return

    # Start task to pump messages from TCP to WS
    asyncio.create_task(tcp_to_ws(reader))

    # Start the local WebSocket Server
    ws_server = await websockets.serve(lambda *args: handler(*args, writer), "0.0.0.0", 8765)
    print("WebSocket bridge running on ws://0.0.0.0:8765")
    
    await ws_server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
