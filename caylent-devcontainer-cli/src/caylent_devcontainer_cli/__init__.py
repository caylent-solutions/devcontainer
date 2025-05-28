"""Caylent Devcontainer CLI package."""

import importlib.metadata
import os

try:
    # Try to get version from package metadata
    __version__ = importlib.metadata.version("caylent-devcontainer-cli")
except importlib.metadata.PackageNotFoundError:
    # If package is not installed, try to get version from environment variable (CI/CD)
    __version__ = os.environ.get("GITHUB_REF_NAME", "0.1.0")
