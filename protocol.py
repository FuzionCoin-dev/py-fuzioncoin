import socket

def handle_message(conn, addr, message):
    # Prints out the message (temporarily)
    # TODO: this
    message = message.decode('utf-8')
    print(message)
