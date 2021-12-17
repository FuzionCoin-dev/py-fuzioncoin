import argparse
import json
import random

import logger

def load_config():
    global CONFIG

    print("Loading configuration...")
    try:
        CONFIG = json.load(args.config)
    except:
        print("Failed to parse configuration file!")
        raise SystemExit

    # DEFAULTS
    if not "colored_output" in CONFIG:
        CONFIG["colored_output"] = False

    if not "max_clients" in CONFIG:
        CONFIG["max_clients"] = 5

    if not "max_servers" in CONFIG:
        CONFIG["max_servers"] = 10

    if not "trusted_nodes" in CONFIG:
        CONFIG["trusted_nodes"] = []

    args.config.close()


def setup_logger():
    global MAIN_LOGGER
    logger.setup_color_usage(CONFIG["colored_output"])
    MAIN_LOGGER = logger.Logger("MAIN")


def init_server():
    global SERVER

    import server

    if CONFIG["server_port"]:
        SERVER = server.Server(port=CONFIG["server_port"])
    else:
        SERVER = server.Server()

    SERVER.start()

def init_client():
    global CLIENT

    import client
    CLIENT = client.Client()

# yields all peers, that we are connected to
def peers_generator():
    for c in SERVER._clients:
        yield c
    for s in CLIENT._servers:
        yield s

if __name__ == "__main__":
    # Setup argparse
    ap_formatter = lambda prog: argparse.HelpFormatter(prog,max_help_position=52)

    parser = argparse.ArgumentParser(
        description="Official FuzionCoin node implementation",
        formatter_class=ap_formatter
    )

    parser.add_argument(
        "-c", "--config",
        help="Node configuration file",
        type=argparse.FileType("r"),
        required=False,
        metavar="PATH",
        dest="config",
        default="config.json"
    )

    args = parser.parse_args()

    load_config()
    setup_logger()

    MAIN_LOGGER.info("Starting node...")

    init_server()
    init_client()

    # Automatically try to connect to some of trusted nodes
    nodes = CONFIG["trusted_nodes"].copy()
    random.shuffle(nodes)
    if len(nodes) > CONFIG["max_servers"]:
        nodes = nodes[:config["max_servers"]]

    for p in nodes:
        if ":" in p:
            x = p.split(":")
            CLIENT.connect(x[0], int(x[1]))
        else:
            CLIENT.connect(p)
