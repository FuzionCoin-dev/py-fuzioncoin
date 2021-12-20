import os
import datetime

def get_time():
    return datetime.datetime.today().strftime('%d-%m-%Y %H:%M:%S')

def setup(color_usage: bool, logs_directory: str, debug: bool):
    global use_color
    global _log_file
    global _debug
    use_color = color_usage

    if logs_directory is not None:
        _log_file = os.path.join(logs_directory, f"{datetime.datetime.today().strftime('%d-%m-%Y_%H:%M:%S')}.log")
    else:
        _log_file = None

    _debug = debug

    if _log_file is None:
        return

    if not os.path.exists(logs_directory):
        os.mkdir(logs_directory)

try:
    import colorama
    color_support = True

    if os.name == "nt":
        colorama.init(convert=True, autoreset=True)
    else:
        colorama.init(autoreset=True)
except ImportError:
    # Colorama not found
    # Falling back to uncolored output
    color_support = False

class Colors:
    MODNAME = colorama.Fore.WHITE + colorama.Style.BRIGHT
    GRAY = colorama.Fore.WHITE + colorama.Style.RESET_ALL
    INFO = colorama.Fore.CYAN + colorama.Style.BRIGHT
    WARN = colorama.Fore.YELLOW + colorama.Style.BRIGHT
    ERROR = colorama.Fore.RED + colorama.Style.BRIGHT
    OK = colorama.Fore.GREEN + colorama.Style.BRIGHT


class Logger:
    def __init__(self, module_name: str):
        self.module_name = module_name
        if use_color and (not color_support):
            print(
                "\nColorama module isn't installed, so colored output is not available!\n" +
                "Install the colorama module or disable colored output in config file.\n"
            )
            raise SystemExit
        self.use_color = use_color

    def info(self, message):
        if self.use_color:
            print(f"{Colors.GRAY}[{Colors.MODNAME}{self.module_name}/INFO {Colors.GRAY}{get_time()}]: {Colors.INFO}{message}")
        else:
            print(f"[{self.module_name}/INFO {get_time()}]: {message}")

        if _log_file is not None:
            with open(_log_file, "a") as f:
                print(f"[{self.module_name}/INFO {get_time()}]: {message}", file=f)

    def warn(self, message):
        if self.use_color:
            print(f"{Colors.GRAY}[{Colors.MODNAME}{self.module_name}/WARN {Colors.GRAY}{get_time()}]: {Colors.WARN}{message}")
        else:
            print(f"[{self.module_name}/WARN {get_time()}]: {message}")

        if _log_file is not None:
            with open(_log_file, "a") as f:
                print(f"[{self.module_name}/WARN {get_time()}]: {message}", file=f)

    def error(self, message):
        if self.use_color:
            print(f"{Colors.GRAY}[{Colors.MODNAME}{self.module_name}/ERROR {Colors.GRAY}{get_time()}]: {Colors.ERROR}{message}")
        else:
            print(f"[{self.module_name}/ERROR {get_time()}]: {message}")

        if _log_file is not None:
            with open(_log_file, "a") as f:
                print(f"[{self.module_name}/ERROR {get_time()}]: {message}", file=f)

    def ok(self, message):
        if self.use_color:
            print(f"{Colors.GRAY}[{Colors.MODNAME}{self.module_name}/OK {Colors.GRAY}{get_time()}]: {Colors.OK}{message}")
        else:
            print(f"[{self.module_name}/OK {get_time()}]: {message}")

        if _log_file is not None:
            with open(_log_file, "a") as f:
                print(f"[{self.module_name}/OK {get_time()}]: {message}", file=f)

    def debug(self, message):
        if not _debug:
            return

        if self.use_color:
            print(f"{Colors.GRAY}[{Colors.MODNAME}{self.module_name}/DEBUG {Colors.GRAY}{get_time()}]: {Colors.GRAY}{message}")
        else:
            print(f"[{self.module_name}/DEBUG {get_time()}]: {message}")

        if _log_file is not None:
            with open(_log_file, "a") as f:
                print(f"[{self.module_name}/DEBUG {get_time()}]: {message}", file=f)
