"""UI utilities for the Caylent Devcontainer CLI."""

import sys

from caylent_devcontainer_cli import __version__

# ANSI Colors
COLORS = {
    "CYAN": "\033[1;36m",
    "GREEN": "\033[1;32m",
    "YELLOW": "\033[1;33m",
    "RED": "\033[1;31m",
    "BLUE": "\033[1;34m",
    "PURPLE": "\033[1;35m",
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
}

# Global variables
AUTO_YES = False


def set_auto_yes(value):
    """Set the global AUTO_YES flag."""
    global AUTO_YES
    AUTO_YES = value


def log(level, message):
    """Log a message with the specified level."""
    icons = {"INFO": "ℹ️ ", "OK": "✅ ", "WARN": "⚠️ ", "ERR": "❌ "}
    color_map = {
        "INFO": COLORS["CYAN"],
        "OK": COLORS["GREEN"],
        "WARN": COLORS["YELLOW"],
        "ERR": COLORS["RED"],
    }
    reset = COLORS["RESET"]
    icon = icons.get(level, "")
    color = color_map.get(level, "")
    print(f"{color}[{level}]{reset} {icon}{message}", file=sys.stderr)


def confirm_action(message):
    """Ask for user confirmation before proceeding."""
    if AUTO_YES:
        print(f"{COLORS['YELLOW']}⚠️  {message}{COLORS['RESET']}")
        print(f"{COLORS['GREEN']}✓ Automatically confirmed with --yes flag{COLORS['RESET']}")
        print()
        return True

    print(f"{COLORS['YELLOW']}⚠️  {message}{COLORS['RESET']}")
    response = input(f"{COLORS['BOLD']}Do you want to continue? [y/N]{COLORS['RESET']} ")
    if not response.lower().startswith("y"):
        log("ERR", "Operation cancelled by user")
        return False
    print()
    return True


def show_banner():
    """Display a fancy banner."""
    print(f"{COLORS['BLUE']}╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print(f"║   {COLORS['CYAN']}🐳 Caylent Devcontainer CLI v{__version__}{COLORS['BLUE']}                      ║")
    print("║                                                           ║")
    print(f"╚═══════════════════════════════════════════════════════════╝{COLORS['RESET']}")
    print()
