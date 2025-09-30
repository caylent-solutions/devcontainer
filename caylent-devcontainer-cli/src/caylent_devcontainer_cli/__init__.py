"""Caylent Devcontainer CLI package."""

try:
    from importlib.metadata import version
    __version__ = version("caylent-devcontainer-cli")
except ImportError:
    # Fallback for Python < 3.8
    from importlib_metadata import version
    __version__ = version("caylent-devcontainer-cli")
