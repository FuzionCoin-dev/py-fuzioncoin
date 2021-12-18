import threading
import socket

import connection
import protocol
import logger

_logger = logger.Logger("SERVER")

class Server:
    def __init__(self, addr: str = "0.0.0.0", port: int = 47685):
        self.address = (addr, port)
        self._clients = []

    def start(self):
        threading.Thread(target=self.handler).start()

    def handler(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(self.address)

        self.sock.listen()
        while True:
            conn, addr = self.sock.accept()
            (accept_bool, reject_reason) = protocol.welcome_message_server(conn)

            if accept_bool:
                _logger.info(f"Connection from {list(addr)[0]}:{list(addr)[1]} accepted!")
                handler = connection.ConnHandler(conn, addr)
                handler.start()

                self._clients.append(handler)
            else:
                _logger.warn(f"Connection from {list(addr)[0]}:{list(addr)[1]} rejected: {reject_reason}")
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
