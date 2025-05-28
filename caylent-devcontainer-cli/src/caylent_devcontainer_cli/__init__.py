"""Caylent Devcontainer CLI package."""

import os
import importlib.metadata

try:
    # Try to get version from package metadata
    __version__ = importlib.metadata.version("caylent-devcontainer-cli")
except importlib.metadata.PackageNotFoundError:
    # If package is not installed, try to get version from environment variable (CI/CD)
    __version__ = os.environ.get("GITHUB_REF_NAME", "0.1.0")
    # Remove 'v' prefix if present (from git tags)
    if __version__.startswith("v"):
        __version__ = __version__[1:]