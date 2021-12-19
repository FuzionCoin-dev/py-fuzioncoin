import threading
import socket

import protocol

class ConnHandler(threading.Thread):
    def __init__(self, conn: socket.socket, addr: tuple):
        threading.Thread.__init__(self, daemon=True)

        self.conn = conn
        self.addr = addr

        self.send_queue = []

    def run(self):
        running = True

        while running:
            message = protocol.recv_msg(self.conn)
            protocol.handle_message(self.conn, self.addr, message)

            if len(self.send_queue) > 0:
                protocol.send_msg(self.conn, self.send_queue.pop(0))


    def send(message: bytes):
        self.send_queue.append(message)
