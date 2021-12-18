import os
import datetime

use_color: bool

def setup_color_usage(color: bool):
    global use_color
    use_color = color

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

def get_time():
    return datetime.datetime.today().strftime('%d-%m-%Y %H:%M:%S')

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

    def warn(self, message):
        if self.use_color:
            print(f"{Colors.GRAY}[{Colors.MODNAME}{self.module_name}/WARN {Colors.GRAY}{get_time()}]: {Colors.WARN}{message}")
        else:
            print(f"[{self.module_name}/WARN {get_time()}]: {message}")

    def error(self, message):
        if self.use_color:
            print(f"{Colors.GRAY}[{Colors.MODNAME}{self.module_name}/ERROR {Colors.GRAY}{get_time()}]: {Colors.ERROR}{message}")
        else:
            print(f"[{self.module_name}/ERROR {get_time()}]: {message}")

    def ok(self, message):
        if self.use_color:
            print(f"{Colors.GRAY}[{Colors.MODNAME}{self.module_name}/OK {Colors.GRAY}{get_time()}]: {Colors.OK}{message}")
        else:
            print(f"[{self.module_name}/OK {get_time()}]: {message}")
