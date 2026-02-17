"""UI utilities for the Caylent Devcontainer CLI."""

import os
import subprocess
import sys
import tempfile
from typing import Any, Callable, Optional

import questionary

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


def exit_with_error(message):
    """Log an error message and exit with code 1.

    Args:
        message: The error message to log at ERR level.
    """
    log("ERR", message)
    sys.exit(1)


def exit_cancelled(message="Operation cancelled by user"):
    """Log a cancellation message and exit with code 0.

    Args:
        message: The cancellation message to log at INFO level.
    """
    log("INFO", message)
    sys.exit(0)


def ask_or_exit(question):
    """Call .ask() on a questionary question, exiting if the user cancels.

    Args:
        question: A questionary question object (before .ask() is called).

    Returns:
        The user's answer.

    Raises:
        SystemExit: If the user cancels (None return) or presses Ctrl+C.
    """
    try:
        result = question.ask()
    except KeyboardInterrupt:
        exit_cancelled()
        return  # Unreachable: exit_cancelled raises SystemExit

    if result is None:
        exit_cancelled()

    return result


def mask_password(value: str) -> str:
    """Mask a password value for safe display.

    Args:
        value: The password string to mask.

    Returns:
        A masked representation showing only the length.
    """
    return f"****** ({len(value)} characters)"


def ssh_fingerprint(key_path: str) -> str:
    """Get the SSH key fingerprint for display.

    Args:
        key_path: Path to the SSH private key file.

    Returns:
        The fingerprint string, or an error message if the key is invalid.
    """
    try:
        result = subprocess.run(
            ["ssh-keygen", "-l", "-f", key_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return f"Error reading key: {result.stderr.strip()}"
        return result.stdout.strip()
    except FileNotFoundError:
        return "Error: ssh-keygen not found in PATH"


def prompt_with_confirmation(
    prompt_fn: Callable[[], Any],
    display_fn: Optional[Callable[[Any], str]] = None,
) -> Any:
    """Prompt the user for input with a confirmation loop.

    Implements the universal input confirmation pattern:
    1. Call prompt_fn() to get a questionary question, then ask_or_exit() it
    2. Display the entered value (formatted by display_fn if provided)
    3. Ask "Is this correct?"
    4. If no: repeat from step 1
    5. If yes: return the value

    Args:
        prompt_fn: Callable that returns a questionary question object.
        display_fn: Optional callable to format the value for display.
                    If None, displays the raw value. Use mask_password
                    for password fields, ssh_fingerprint for key paths.

    Returns:
        The confirmed user input value.

    Raises:
        SystemExit: If the user cancels at any point.
    """
    while True:
        answer = ask_or_exit(prompt_fn())

        if display_fn is not None:
            display_value = display_fn(answer)
        else:
            display_value = str(answer)

        log("INFO", f"You entered: {display_value}")

        confirmed = ask_or_exit(questionary.confirm("Is this correct?", default=True))
        if confirmed:
            return answer


def validate_ssh_key_file(key_path: str) -> tuple:
    """Validate an SSH private key file.

    Checks:
    1. File exists and is readable
    2. Normalizes line endings (strips \\r, ensures trailing newline)
    3. Format check: starts with -----BEGIN and contains -----END
    4. Real key validation via ssh-keygen -y -f <keyfile>

    Args:
        key_path: Path to the SSH private key file.

    Returns:
        A tuple of (success: bool, message: str).
        On success: (True, fingerprint string)
        On failure: (False, error description)
    """
    # Expand ~ to absolute path
    key_path = os.path.expanduser(key_path)

    # Check file exists
    if not os.path.exists(key_path):
        return (False, f"File does not exist: {key_path}")

    # Check file is readable
    if not os.access(key_path, os.R_OK):
        return (False, f"File is not readable: {key_path}")

    # Read and normalize line endings
    try:
        with open(key_path, "r") as f:
            content = f.read()
    except PermissionError:
        return (False, f"Permission denied reading file: {key_path}")

    # Normalize: strip \r, ensure trailing newline
    content = content.replace("\r", "")
    if not content.endswith("\n"):
        content += "\n"

    # Format check
    if "-----BEGIN" not in content:
        return (False, "Invalid key format: file must start with -----BEGIN marker")
    if "-----END" not in content:
        return (False, "Invalid key format: file must contain -----END marker")

    # Write normalized content to a temp file for ssh-keygen validation
    with tempfile.NamedTemporaryFile(mode="w", suffix="_key", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        os.chmod(tmp_path, 0o600)

        # Real key validation via ssh-keygen -y -f (extract public key)
        # Use SSH_ASKPASS=/bin/false and DISPLAY="" to prevent interactive
        # passphrase prompts from opening /dev/tty. Also set
        # SSH_ASKPASS_REQUIRE=force so ssh-keygen uses SSH_ASKPASS instead
        # of /dev/tty. With /bin/false as the askpass program, any
        # passphrase-protected key will fail immediately instead of hanging.
        validation_env = os.environ.copy()
        validation_env["SSH_ASKPASS"] = "/bin/false"
        validation_env["SSH_ASKPASS_REQUIRE"] = "force"
        validation_env["DISPLAY"] = ""

        try:
            result = subprocess.run(
                ["ssh-keygen", "-y", "-f", tmp_path],
                capture_output=True,
                text=True,
                input="",
                timeout=10,
                env=validation_env,
            )
        except subprocess.TimeoutExpired:
            return (
                False,
                "SSH key validation timed out. The key may require a "
                "passphrase. Please use a key without a passphrase or "
                "remove the passphrase with: ssh-keygen -p -f <keyfile>",
            )

        if result.returncode != 0:
            stderr = result.stderr.strip().lower()
            if "passphrase" in stderr or "incorrect" in stderr or "bad" in stderr:
                return (
                    False,
                    "SSH key requires a passphrase. Please use a key without a "
                    "passphrase or remove the passphrase with: "
                    "ssh-keygen -p -f <keyfile>",
                )
            return (False, f"Invalid SSH key: {result.stderr.strip()}")

        # Get fingerprint (reuse ssh_fingerprint to avoid duplicating subprocess call)
        fingerprint = ssh_fingerprint(tmp_path)
        if fingerprint.startswith("Error"):
            return (False, f"Could not read key fingerprint: {fingerprint}")

        return (True, fingerprint)
    finally:
        os.unlink(tmp_path)


def confirm_action(message):
    """Ask for user confirmation before proceeding."""
    print(f"{COLORS['YELLOW']}⚠️  {message}{COLORS['RESET']}")
    response = input(f"{COLORS['BOLD']}Do you want to continue? [y/N]{COLORS['RESET']} ")
    if not response.lower().startswith("y"):
        log("ERR", "Operation cancelled by user")
        return False
    print()
    return True
