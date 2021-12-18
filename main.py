import argparse
import json

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


# yields all peers, that we are connected to
def peers_generator():
    for c in SERVER._clients:
        yield c
    for s in CLIENT._servers:
        yield s

def disp_name(s: str):
    s = s.replace("_", " ")
    s = s[0].upper() + s[1::]
    return s


def log_config():
    MAIN_LOGGER.info("---------------[ Configuration: ]---------------")
    for x,y in sorted(CONFIG.items()):
        if isinstance(y, list):
            MAIN_LOGGER.info(f"{disp_name(x)}:")
            for i in y:
                MAIN_LOGGER.info(" "*(len(disp_name(x)) + 2) + i)
        else:
            MAIN_LOGGER.info(f"{disp_name(x)}: {y}")

    MAIN_LOGGER.info("------------------------------------------------")

def main():
    global SERVER
    global CLIENT

    MAIN_LOGGER.info("Starting node...")
    MAIN_LOGGER.info("""
    _____       ______
    |  __ \     |  ____|
    | |__) |   _| |__ _   _ _______
    |  ___/ | | |  __| | | |_  / __|
    | |   | |_| | |  | |_| |/ / (__
    |_|    \__, |_|   \__,_/___\___|
            __/ |
           |___/
    """)

    log_config()

    import server
    if CONFIG["server_port"]:
        SERVER = server.Server(port=CONFIG["server_port"])
    else:
        SERVER = server.Server()

    SERVER.start()

    import client
    CLIENT = client.Client()

    client.connect_to_trusted_nodes(CLIENT, CONFIG["trusted_nodes"].copy(), CONFIG["max_servers"])

    while True:
        pass

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

    try:
        main()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        MAIN_LOGGER.info("Stopping node...")
        SERVER.close()
        CLIENT.close()
        raise SystemExit
