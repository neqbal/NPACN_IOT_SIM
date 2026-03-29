import socket
import time
import threading
import sys

# Allow launching multiple distinct devices e.g. `python device.py light1`
DEVICE_ID = sys.argv[1] if len(sys.argv) > 1 else "fan1"
HOST = "127.0.0.1"
PORT = 9000

def device_loop():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, PORT))
    except Exception as e:
        print(f"Could not connect to {HOST}:{PORT}: {e}")
        return

    s.send(f"REGISTER_DEVICE:{DEVICE_ID}\n".encode())
    print(f"Registered as device: {DEVICE_ID}")

    status = "OFF"

    # Thread to receive commands
    def listen():
        nonlocal status
        while True:
            try:
                data = s.recv(1024)
                if not data:
                    print("Connection closed by server.")
                    break
                msg = data.decode().strip()
                print(f"Received Command: {msg}")
                
                # Update status based on command
                if f"CMD:{DEVICE_ID}:ON" in msg:
                    status = "ON"
                    s.send(f"STATUS:{DEVICE_ID}:{status}\n".encode())
                elif f"CMD:{DEVICE_ID}:OFF" in msg:
                    status = "OFF"
                    s.send(f"STATUS:{DEVICE_ID}:{status}\n".encode())
            except Exception as e:
                print(f"Listen thread error: {e}")
                break

    threading.Thread(target=listen, daemon=True).start()

    # Periodic STATUS broadcast
    try:
        while True:
            s.send(f"STATUS:{DEVICE_ID}:{status}\n".encode())
            time.sleep(5)
    except KeyboardInterrupt:
        print("Device terminating...")
    finally:
        s.close()

if __name__ == "__main__":
    device_loop()
