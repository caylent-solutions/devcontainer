"""Environment variable utilities."""

from typing import Any, Dict

from caylent_devcontainer_cli.commands.setup import EXAMPLE_ENV_VALUES


def is_single_line_env_var(value):
    """Check if an environment variable value is a single line string."""
    return isinstance(value, str) and "\n" not in value


def get_missing_env_vars(container_env: Dict[str, Any]) -> Dict[str, Any]:
    """Check container_env against EXAMPLE_ENV_VALUES and return missing single-line vars.

    Args:
        container_env: The container environment variables dict to check.

    Returns:
        A dict of missing environment variable names mapped to their default values
        from EXAMPLE_ENV_VALUES. Only includes variables whose default values are
        single-line strings.
    """
    missing_vars = {}
    for key, value in EXAMPLE_ENV_VALUES.items():
        if key not in container_env and is_single_line_env_var(value):
            missing_vars[key] = value
    return missing_vars
