import socket

s = socket.socket()
s.connect(("127.0.0.1", 9000))
s.send(b"REGISTER_CLIENT\n")
s.send(b"CMD:Guest:fan1:ON\n")
data = s.recv(1024)
print("Received:", data)
