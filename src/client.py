import threading
import socket
import random
import time

import connection
import logger
import protocol
from exception_handler import handle_exception

_logger = logger.Logger("CLIENT")

class Client:
    def __init__(self):
        self._servers = []
        self.active = True
        threading.Thread(target=self.conn_watchdog, daemon=True).start()

    @handle_exception(_logger)
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
                    return False

                _logger.ok(f"Successfully connected to {addr}:{port}!")
            except OSError:
                _logger.error(f"Failed to connect to {addr}:{port}" + ("! Retrying..." if trynum < 3 else " 3 times!"))
                if trynum == 3:
                    return False
                trynum += 1

        handler = connection.ConnHandler(sock, (addr, port))
        handler.start()

        self._servers.append(handler)
        return True

    @handle_exception(_logger)
    def conn_watchdog(self):
        while self.active:
            time.sleep(0.5)
            for i in range(len(self._servers)):
                if not self._servers[i].is_alive():
                    self._servers.pop(i)

    @handle_exception(_logger)
    def close(self):
        self.active = False

        for s in self._servers:
            s.running = False
            time.sleep(0.1)
            s.conn.close()


@handle_exception(_logger)
def connect_to_trusted_nodes(client: Client, nodes: list, max_servers: int):
    if len(nodes) == 0:
        _logger.warning("There are no trusted nodes added!")

    if max_servers >= len(nodes):
        _logger.info("Connecting to trusted nodes...")
        nodes_to_connect = dict(zip(nodes, (False for _ in range(len(nodes)))))
    else:
        _logger.info("Connecting to some of trusted nodes...")
        _logger.warn("There is more trusted nodes than maximum number of servers!")
        random.shuffle(nodes)
        nodes_to_connect = dict(zip(nodes[:max_servers], (False for _ in range(max_servers))))

    success = 0

    while nodes:
        for node in nodes_to_connect.keys():
            if ":" in node:
                x = node.split(":")
                nodes_to_connect[node] = client.connect(x[0], int(x[1]))
            else:
                nodes_to_connect[node] = client.connect(node)

        for x, y in nodes_to_connect.items():
            nodes.remove(x)
            if y:
                success += 1

        ms = max_servers - success

        if ms >= len(nodes):
            nodes_to_connect = dict(zip(nodes, (False for _ in range(len(nodes)))))
        else:
            nodes_to_connect = dict(zip(nodes[:config["max_servers"]], (False for _ in range(ms))))

        if len(nodes_to_connect) == 0:
            break

    if success > 0:
        _logger.info(f"Successfully connected to {success} nodes...")
    else:
        _logger.warn(f"Failed to connect to all of trusted nodes!")
