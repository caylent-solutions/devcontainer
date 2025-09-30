#!/usr/bin/env python3
import os
import sys


# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def test_version_consistency():
    """Test that __init__.py version matches pyproject.toml version."""
    import re

    from caylent_devcontainer_cli import __version__

    # Read version from pyproject.toml
    pyproject_path = os.path.join(os.path.dirname(__file__), "../../pyproject.toml")
    with open(pyproject_path, "r") as f:
        content = f.read()
        match = re.search(r'version = "([^"]+)"', content)
        toml_version = match.group(1) if match else None

    # Verify versions match
    assert toml_version is not None, "Could not find version in pyproject.toml"
    assert __version__ == toml_version, f"Version mismatch: __init__.py={__version__}, pyproject.toml={toml_version}"
