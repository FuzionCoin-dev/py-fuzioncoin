import threading
import socket

import connection
import logger
import protocol

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
                sock.connect((addr, port))

                (connected, error_message) = protocol.welcome_message_client(sock)
                if not connected:
                    _logger.error(f"Failed to connect to {addr}:{port}! {error_message}")
                    return

                _logger.ok(f"Successfully connected to {addr}:{port}!")
            except OSError:
                _logger.error(f"Failed to connect to {addr}:{port}" + ("! Retrying..." if trynum < 3 else " 3 times!"))
                if trynum == 3:
                    return
                trynum += 1

        handler = connection.ConnHandler(sock, (addr, port))
        handler.start()

        self._servers.append(handler)
