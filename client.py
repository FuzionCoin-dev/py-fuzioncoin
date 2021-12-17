import threading
import socket

import connection
import logger

_logger = logger.Logger("CLIENT")

class Client:
    def __init__(self):
        self._servers = []

    def connect(self, addr: str, port: int = 47685):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        connected = False
        trynum = 1
        while (not connected) and trynum <= 3:
            try:
                sock.connect(sock.connect((addr, port)))
                _logger.ok(f"Connected to {addr}:{port}!")
                connected = True
            except OSError:
                _logger.error(f"Failed to connect to {addr}:{port}" + ("! Retrying..." if trynum < 3 else " 3 times!"))
                trynum += 1

        handler = connection.ConnHandler(sock, (addr, port))
        handler.start()

        self._servers.append(handler)
