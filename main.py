import argparse
import json
import os

import logger

DEFAULT_CONFIG = {
    "colored_output": False,
    "max_servers": 10,
    "max_clients": 5,
    "trusted_nodes": [],
    "data_directory": os.path.abspath("data/"),
    "server_ip": "0.0.0.0",  # All interfaces
    "server_port": 47685,
    "log_file": None
}

def load_config():
    global CONFIG

    print("Loading configuration...")
    try:
        CONFIG = json.load(args.config)
    except:
        print("ERROR: Failed to parse configuration file!")
        print("       This is not a valid JSON file")
        raise SystemExit

    for x, y in DEFAULT_CONFIG.items():
        if not x in CONFIG:
            # Load default setting
            CONFIG[x] = y
        elif type(CONFIG[x]) is not type(y):
            if not (x == "log_file" and isinstance(CONFIG[x], str)):
                print("ERROR: Failed to parse configuration file!")
                print(f"       Bad value for key {x} (should be {type(y).__name__}, got {type(CONFIG[x]).__name__})")
                raise SystemExit

        if x == "data_directory" or x == "log_file":
            if CONFIG[x] is not None:
                CONFIG[x] = os.path.abspath(CONFIG[x])

    args.config.close()


def setup_logger():
    global MAIN_LOGGER
    logger.setup(color_usage=CONFIG["colored_output"], log_file=CONFIG["log_file"])
    MAIN_LOGGER = logger.Logger("MAIN")

def disp_name(s: str):
    s = s.replace("_", " ")
    s = s[0].upper() + s[1::]
    return s

def log_config():
    MAIN_LOGGER.info("---------------[ Configuration: ]---------------")
    for x,y in sorted(CONFIG.items()):
        if isinstance(y, list):
            MAIN_LOGGER.info(f"{disp_name(x)}:" + (" None" if len(y) == 0 else ""))
            for i in y:
                MAIN_LOGGER.info(" "*(len(disp_name(x)) + 2) + i)
        else:
            MAIN_LOGGER.info(f"{disp_name(x)}: {y}" + (" (default)" if DEFAULT_CONFIG[x] == y else ""))

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
        MAIN_LOGGER.info("Got KeyboardInterrupt")
        MAIN_LOGGER.info("Stopping node...")
        SERVER.close()
        CLIENT.close()
        raise SystemExit
