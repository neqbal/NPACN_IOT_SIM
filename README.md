# Simple IoT Smart Home Controller

This is a complete IoT architecture implementation developed to fulfill your exact assignment requirements. It demonstrates fundamental socket programming, `epoll` concurrency, database state persistence, and Secure WebSockets (WSS).

## Code Components
1. **`server.c`**: Core TCP server using `epoll` for non-blocking I/O routing. It features robust buffers for handling incomplete fragmented reads and utilizes the `TCP_NODELAY` socket option for zero-latency commands.
2. **`ws_bridge.py`**: Python script bridging secure WebSocket connections (`wss://`) to raw TCP. It securely translates traffic and natively manages the JSON database.
3. **`database.json`**: Auto-generated local DB storing user credentials, physical device states, and global timestamped activity logs.
4. **`cert.pem` / `key.pem`**: Self-signed OpenSSL certificates generated strictly to facilitate `wss://` encrypted communication.
5. **`device.py`**: A simulated physical IoT device node that issues periodic `STATUS` ticks and updates in real-time.
6. **`index.html`**: The UI interface with vanilla JavaScript WebSockets, featuring a mandatory credential login step preventing unauthorized access.
7. **`test_sys.py`**: Automated end-to-end integration test confirming auth headers.

## Steps to Compile and Run

Open up 4 distinct terminal instances to observe the live interactions between all system layers:

### 1. Start the C Server
Establish the core logic hub on `localhost:9000`. This will route all IoT activity using non-blocking epoll sockets.
```bash
gcc server.c -o server
./server
```

### 2. Start the Secure WebSocket Bridge
In the second terminal, spin up the translation layer. It will launch an encrypted SSL instance on port 8765.
```bash
python ws_bridge.py
```

### 3. Spin up the Device Simulator
In the third terminal, initiate your target IoT node. It will handshake and routinely broadcast `STATUS:fan1:OFF`.
```bash
python device.py
```

### 4. Trust the SSL Certificate (CRITICAL STEP)
Since we generated our own private SSL certificates, modern browsers will block the WebSocket connection initially because no official CA signed it! You must proactively allow it:
1. Open your browser and navigate directly to: `https://localhost:8765`
2. You will get a warning stating **"Your connection is not private."**
3. Click "Advanced" / "More Info" and select **"Proceed to localhost (unsafe)"**.
4. You should see a blank screen that says "Upgrade to WebSockets required." You can now close this tab!

### 5. Access the Web UI
Now you can safely open the interface. Instead of serving it, you can normally just double-click `index.html` in your file explorer.
1. When prompted for credentials, use the default DB login:
   - **Username**: `admin`
   - **Password**: `password123`
2. Once connected, click **Turn ON Fan**.

### Observing the Result
When you click **Turn ON Fan**:
1. `index.html` transmits your encrypted auth and command across `wss://` to `ws_bridge.py`.
2. The python bridge validates `admin:password123` against `database.json`.
3. If valid, the bridge relays it over raw TCP to the C backend.
4. `server.c` buffers the byte-stream until it identifies the `\n` message break, then strictly forwards the route to `device.py` (which immediately flips to `STATUS:fan1:ON`).
5. A system-wide log of your actions is permanently appended to `database.json`!
