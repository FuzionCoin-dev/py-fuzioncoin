import threading
import socket
import time

import connection
import protocol
import logger
from exception_handler import handle_exception

_logger = logger.Logger("SERVER")

class Server:
    def __init__(self, addr: str = "0.0.0.0", port: int = 47685):
        self.address = (addr, port)
        self._clients = []

    @handle_exception(_logger)
    def start(self):
        _logger.info("Starting server...")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        success = False

        while not success:
            try:
                self.sock.bind(self.address)
                success = True
            except OSError:
                _logger.error(f"Unable to bind address {self.address[0]}:{self.address[1]}! Retrying in 5 seconds...")
                time.sleep(5)

        _logger.info(f"Bound address: {self.address[0]}" + (" (all interfaces)" if self.address[0] == "0.0.0.0" else "") + f" and port: {self.address[1]}")

        threading.Thread(target=self.handler, daemon=True).start()
        threading.Thread(target=self.conn_watchdog, daemon=True).start()

    @handle_exception(_logger)
    def handler(self):
        self.sock.listen()
        _logger.info("Listening for connections...")

        self.running = True
        while self.running:
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

    @handle_exception(_logger)
    def conn_watchdog(self):
        time.sleep(0.5)
        while self.running:
            for i in range(len(self._clients)):
                if not self._clients[i].is_alive():
                    self._clients.pop(i)

    @handle_exception(_logger)
    def close(self):
        self.running = False

        for c in self._clients:
            c.running = False
            time.sleep(0.1)
            c.conn.close()
