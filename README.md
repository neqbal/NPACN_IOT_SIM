# Simple IoT Smart Home Controller

This is a minimal, framework-less, and DB-free IoT architecture implementation. It demonstrates fundamental socket programming, `epoll` concurrency handling for multiple TCP connections, and basic system routing capabilities.

## Code Components
1. **`server.c`**: The central backend server built using vanilla C sockets and `epoll` for non-blocking I/O routing.
2. **`ws_bridge.py`**: A python script that seamlessly translates WebSocket traffic (`ws://`) to Raw TCP packets to interface with the C server.
3. **`device.py`**: A simulated IoT device acting as a TCP client responding to `CMD` tokens and publishing `STATUS` tokens.
4. **`index.html`**: The UI interface with vanilla JavaScript WebSockets capable of managing devices manually.

## Prerequisites
- C Compiler (`gcc`)
- Python 3
- The `websockets` package for the python bridge (`pip install websockets`)

## Steps to Compile and Run

Open up 4 distinct terminal instances to observe the live interactions between all system layers:

### 1. Start the C Server
Establish the core logic hub on `localhost:9000`.
```bash
gcc server.c -o server
./server
```

### 2. Start the WebSocket Bridge
In the second terminal, spin up the translation layer to accept `ws://localhost:8765` incoming clients.
```bash
python ws_bridge.py
```

### 3. Spin up the Device Simulator
In the third terminal, initiate your target IoT node. It will handshake and periodically publish its state.
```bash
python device.py
```

### 4. Access the Web UI
Open the interface directly via your browser. You can usually double-click the `index.html` file in your local file explorer, or serve it:
```bash
python -m http.server 8080
```
Then connect via `http://localhost:8080/index.html`. 

You can click **Turn ON Fan** or **Turn OFF Fan**. When you do:
1. The JS script fires `CMD:fan1:ON` through the WebSocket...
2. `ws_bridge.py` intercepts it and passes it as raw TCP to `server.c`...
3. `server.c` correctly iterates its mapped dictionary of clients and routes the string straight to the `device.py` socket...
4. `device.py` flips its internal state from `OFF` to `ON` and shouts back `STATUS:fan1:ON`...
5. Which the server then broadcasts backwards all the way to your browser UI!
