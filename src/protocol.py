import socket
import json
import time
import struct

USER_AGENT = "FuzionCoin/v0.0.1/PyFuzc"

class DisconnectedError(Exception):
    pass


################################################################
# MESSAGING SYSTEM
################################################################

def send_msg(conn, msg):
    msg = msg.encode("utf-8")
    msg = struct.pack(">I", len(msg)) + msg
    conn.sendall(msg)

def recv_msg(conn):
    try:
        raw_msglen = recvall(conn, 4)
    except socket.error:
        # No message available
        return None

    if not raw_msglen:
        # Disconnected
        raise DisconnectedError

    msglen = struct.unpack(">I", raw_msglen)[0]
    return recvall(conn, msglen).decode("utf-8")

def recvall(conn, n):
    data = b""
    while len(data) < n:
        packet = conn.recv(n - len(data))

        if not packet:
            # Disconnected
            raise DisconnectedError

        data += packet
    return data

def broadcast(msg: str, server, client):
    for conn in server._clients:
        send_msg(conn, msg)

    for conn in client._servers:
        send_msg(conn, msg)

################################################################
# WELCOME MESSAGES (ENSTABILISHING CONNECTION)
################################################################

def welcome_message_server(conn: socket.socket):
    message_content = {
        "method": "welcome",
        "ua": USER_AGENT
    }
    message_content_json = json.dumps(message_content)
    send_msg(conn, message_content_json)

    response = None
    start_time = time.time()

    while not response:
        if time.time() - start_time >= 3:
            return (False, "Client response timeout")
        response = recv_msg(conn)

    try:
        response_dict = json.loads(response)
    except ValueError:
        return (False, "Bad response received! Cannot decode response.")

    if not ("method" in response_dict and response_dict["method"] == "welcome_response"):
        return (False, "Bad response received!")

    if not ("connected" in response_dict and response_dict["connected"] == True):
        return (False, "Client canceled connection." + ((f" reason: {response_dict['reason']}") if "reason" in response_dict else ""))

    if not ("ua" in response_dict and response_dict["ua"].split("/")[0] == "FuzionCoin"):
        return (False, "Client isn't running FuzionCoin node!")

    return (True, None)

def welcome_message_client_cancel_connection(conn: socket.socket, reason: str):
    response_dict = {
        "method": "welcome_response",
        "connected": False,
        "reason": reason,
    }

    response_dict_json = json.dumps(response_dict)
    send_msg(conn, response_dict_json)

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()



def welcome_message_client(conn: socket.socket):
    message = None
    start_time = time.time()

    while not message:
        if time.time() - start_time >= 3:
            r = "Server response timeout!"
            welcome_message_client_cancel_connection(conn, r)
            return (False, r)

        message = recv_msg(conn)

    try:
        message_dict = json.loads(message)
    except ValueError:
        r = "Bad response received! Cannot decode response."
        welcome_message_client_cancel_connection(conn, r)
        return (False, r)

    # Decide whether client should accept server's user agent
    if not ("method" in message_dict and message_dict["method"] == "welcome"):
        r = "Bad response received!"
        welcome_message_client_cancel_connection(conn, r)
        return (False, r)

    if not ("ua" in message_dict and message_dict["ua"].split("/")[0] == "FuzionCoin"):
        r = "Server isn't running FuzionCoin node!"
        welcome_message_client_cancel_connection(conn, r)
        return (False, r)

    # Accept
    response_dict = {
        "method": "welcome_response",
        "connected": True,
        "ua": USER_AGENT
    }

    response_dict_json = json.dumps(response_dict)
    send_msg(conn, response_dict_json)

    return (True, None)

################################################################
# MESSAGES HANDLER
################################################################

def handle_message(conn_handler, message: str):
    # TODO: this
    try:
        message_dict = json.loads(message)
    except ValueError:
        conn_handler.logger.error("Received invalid message: Can't parse JSON!")
        return

    conn_handler.logger.debug("Received message:")
    for x, y in message_dict.items():
        conn_handler.logger.debug(f"  {x}: {y}")
