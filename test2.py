import socket
import time

s = socket.socket()
s.connect(("127.0.0.1", 9000))
s.send(b"REGISTER_CLIENT\n")

time.sleep(1)
s.send(b"CMD:Guest:fan1:ON\n")

for i in range(3):
    data = s.recv(1024)
    print("Received:", data)
