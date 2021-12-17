import threading
import socket

import protocol

class ConnHandler(threading.Thread):
    def __init__(self, conn: socket.socket, addr: tuple):
        threading.Thread.__init__(self)

        self.conn = conn
        self.addr = addr

        self.send_queue = []

    def run(self):
        running = True

        while running:
            message = b""

        while True:
            packet = self.conn.recv(1024)
            if not packet:
                break
            message += packet

            if len(message) > 0:
                for m in message.split(bytes(0x00)):
                    protocol.handle_message(conn, addr, m)


            if len(message_queue) > 0:
                self.conn.sendall(self.message_queue.pop(0))


    def send(message: bytes):
        self.send_queue.append(message)
