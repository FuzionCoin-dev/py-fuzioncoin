import threading
import socket

import protocol
import logger
from exception_handler import handle_exception

class ConnHandler(threading.Thread):
    logger = None

    def __init__(self, conn: socket.socket, addr: tuple):
        threading.Thread.__init__(self, daemon=True)

        self.conn = conn
        self.addr = addr

        self.send_queue = []
        self.logger = logger.Logger(f"CONN/{self.addr[0]}:{self.addr[1]}")

    handle_exception(logger)
    def run(self):
        self.conn.setblocking(0)
        running = True

        while running:
            try:
                message = protocol.recv_msg(self.conn)
            except protocol.DisconnectedError:
                self.logger.warn("Connection has been closed by another peer.")
                self.conn.close()
                return

            if message is not None:
                protocol.handle_message(self, message)

            if len(self.send_queue) > 0:
                protocol.send_msg(self.conn, self.send_queue.pop(0))

    handle_exception(logger)
    def send(message: bytes):
        self.send_queue.append(message)
