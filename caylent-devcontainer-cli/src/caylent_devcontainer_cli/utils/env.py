"""Environment variable utilities."""


def is_single_line_env_var(value):
    """Check if an environment variable value is a single line string."""
    return isinstance(value, str) and "\n" not in value
