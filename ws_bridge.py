import asyncio
import websockets
import json
import os
import ssl
from datetime import datetime

TCP_HOST = "127.0.0.1"
TCP_PORT = 9000

DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        db = {
            "users": {"admin": "password123", "guest": "guestpass"},
            "devices": {},
            "logs": []
        }
        save_db(db)
        return db
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

def log_event(db, event_msg):
    db.setdefault("logs", []).append({
        "timestamp": datetime.now().isoformat(),
        "event": event_msg
    })
    save_db(db)

db = load_db()

# Map websocket -> username
connected_websockets = {}

async def tcp_to_ws(tcp_reader):
    global db
    """ Reads from C TCP server and broadcasts to all WebSocket clients """
    while True:
        try:
            data = await tcp_reader.readline()
            if not data:
                print("TCP connection lost")
                break
            
            message = data.decode().strip()
            print(f"TCP -> WS: {message}")
            
            # Persist device status to database
            if message.startswith("STATUS:"):
                parts = message.split(":")
                if len(parts) >= 3:
                    device_id = parts[1]
                    status = parts[2]
                    db.setdefault("devices", {})[device_id] = status
                    log_event(db, f"Device {device_id} changed status to {status}")

            if connected_websockets:
                websockets.broadcast(connected_websockets.keys(), message)
        except Exception as e:
            print(f"TCP read error: {e}")
            break

async def handler(*args):
    global db
    """ Handles new WebSocket connections and forwards their messages to TCP """
    websocket = args[0]
    tcp_writer = args[-1]
    
    print("New WebSocket client connected")
    try:
        async for message in websocket:
            print(f"WS -> TCP: {message}")
            
            if message.startswith("AUTH:"):
                parts = message.split(":")
                if len(parts) == 3:
                    username = parts[1]
                    password = parts[2]
                    if db.get("users", {}).get(username) == password:
                        connected_websockets[websocket] = username
                        await websocket.send("AUTH_SUCCESS:Welcome " + username)
                        log_event(db, f"User {username} logged in")
                    else:
                        await websocket.send("AUTH_FAIL:Invalid credentials")
                else:
                    await websocket.send("AUTH_FAIL:Invalid format")
            elif message.startswith("CMD:"):
                if websocket not in connected_websockets:
                    await websocket.send("SYS:Error: Not authenticated. Please login.")
                else:
                    username = connected_websockets[websocket]
                    parts = message.split(":")
                    if len(parts) == 4 and parts[1] == username:
                        device_id = parts[2]
                        action = parts[3]
                        log_event(db, f"User {username} commanded {device_id} to turn {action}")
                        tcp_writer.write((message + "\n").encode())
                        await tcp_writer.drain()
                    else:
                        await websocket.send("SYS:Error: Username mismatch in command.")
            else:
                if websocket in connected_websockets:
                    tcp_writer.write((message + "\n").encode())
                    await tcp_writer.drain()
                else:
                    await websocket.send("SYS:Error: Not authenticated.")
                    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if websocket in connected_websockets:
            username = connected_websockets.pop(websocket)
            log_event(db, f"User {username} disconnected")
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

    # Configure SSL
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain("cert.pem", "key.pem")

    # Start the local WebSocket Server
    ws_server = await websockets.serve(lambda *args: handler(*args, writer), "0.0.0.0", 8765, ssl=ssl_context)
    print("WebSocket bridge running on wss://0.0.0.0:8765")
    
    await ws_server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
