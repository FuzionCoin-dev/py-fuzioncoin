import argparse
import json
import os

import logger
from exception_handler import handle_exception

MAIN_LOGGER = None

DEFAULT_CONFIG = {
    "colored_output": False,
    "max_servers": 10,
    "max_clients": 5,
    "trusted_nodes": [],
    "data_directory": os.path.abspath("data/"),
    "server_ip": "0.0.0.0",  # All interfaces
    "server_port": 47685,
    "logs_directory": None,
    "debug_messages": False
}

def is_valid_address(address: str) -> tuple:
    if address.replace(".", "").isnumeric():
        # Address is IP
        for i in address.split("."):
            if i < 0 or i > 255:
                return (False, "IP byte out of valid range.")

    if not ":" in address:
        return (True, None)

    if address.count(":") > 1:
        return (False, "Too many colons in address. Is it valid IPv4 or domain name?")

    p = address.split(":")[1]

    try:
        p = int(p)
    except ValueError:
        return (False, "Port number isn't integer!")

    if p < 1 or p > 65535:
        return (False, "Port number isn't in valid ports range (1 - 65535)")

    # All checks passed
    return (True, None)


def load_config():
    global CONFIG

    print("Loading configuration...")
    if args.config is None:
        CONFIG = DEFAULT_CONFIG.copy()
    else:
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
            if not (x == "logs_directory" and isinstance(CONFIG[x], str)):
                print("ERROR: Failed to parse configuration file!")
                print(f"       Bad value for key {x} (should be {type(y).__name__}, got {type(CONFIG[x]).__name__})")
                raise SystemExit

        if x == "data_directory" or x == "logs_directory":
            if CONFIG[x] is not None:
                CONFIG[x] = os.path.abspath(CONFIG[x])

    for tn_addr in CONFIG["trusted_nodes"]:
        chk = is_valid_address(tn_addr)
        if not chk[0]:
            print("ERROR: Failed to parse configuration file!")
            print(f"       Invalid trusted node address: {tn_addr}")
            print(f"       {chk[1]}")
            raise SystemExit

    args.config.close()


def setup_logger():
    global MAIN_LOGGER
    logger.setup(color_usage=CONFIG["colored_output"], logs_directory=CONFIG["logs_directory"], debug=CONFIG["debug_messages"])
    MAIN_LOGGER = logger.Logger("MAIN")

def disp_name(s: str):
    s = s.replace("_", " ")
    s = s[0].upper() + s[1::]
    return s

@handle_exception(MAIN_LOGGER)
def log_config():
    MAIN_LOGGER.info("---------------[ Configuration: ]---------------")
    for x,y in sorted(CONFIG.items()):
        if isinstance(y, list):
            MAIN_LOGGER.info(f"{disp_name(x)}:" + (" None" if len(y) == 0 else ""))
            for i in y:
                MAIN_LOGGER.info(" "*(len(disp_name(x)) + 2) + i)
        else:
            try:
                MAIN_LOGGER.info(f"{disp_name(x)}: {y}" + (" (default)" if DEFAULT_CONFIG[x] == y else ""))
            except KeyError:
                pass

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
        "--launch-path",
        help=argparse.SUPPRESS,
        type=str,
        required=False,
        dest="launch_path",
        default=os.getcwd()
    )

    parser.add_argument(
        "-c", "--config",
        help="Node configuration file",
        type=str,
        required=False,
        metavar="PATH",
        dest="config",
        default=None
    )

    args = parser.parse_args()

    if args.config is None:
        pth = os.path.join(os.getcwd(), "config.json")
        if os.path.exists(pth):
            args.config = open(pth, "r")
        else:
            print("WARNING: config.json does not exist and another configuration file was not specified.")
            print("         Loading default configuration (with no trusted peers).")
            # args.config is still None!
    else:
        try:
            if args.config.startswith("/"):
                args.config = open(args.config, "r")
            else:
                args.config = open(os.path.join(args.launch_path, args.config), "r")
        except:
            raise TypeError("Invalid configuration file path!")

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
