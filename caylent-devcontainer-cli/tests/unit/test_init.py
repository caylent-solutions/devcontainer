#!/usr/bin/env python3
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


@patch("importlib.metadata.PackageNotFoundError", ImportError)  # For Python < 3.8 compatibility
def test_version_from_package():
    with patch("importlib.metadata.version", return_value="1.2.3"):
        # We need to patch the import itself
        with patch.dict("sys.modules"):
            if "caylent_devcontainer_cli" in sys.modules:
                del sys.modules["caylent_devcontainer_cli"]

            from caylent_devcontainer_cli import __version__

            assert __version__ == "1.2.3"


@patch("importlib.metadata.PackageNotFoundError", ImportError)  # For Python < 3.8 compatibility
def test_version_from_env():
    # We need to patch both the version function and the environment
    with patch("importlib.metadata.version", side_effect=ImportError()):
        with patch.dict("os.environ", {"GITHUB_REF_NAME": "v2.3.4"}):
            # We need to patch the import itself
            with patch.dict("sys.modules"):
                if "caylent_devcontainer_cli" in sys.modules:
                    del sys.modules["caylent_devcontainer_cli"]

                from caylent_devcontainer_cli import __version__

                assert __version__ == "2.3.4"


@patch("importlib.metadata.PackageNotFoundError", ImportError)  # For Python < 3.8 compatibility
def test_version_default():
    # We need to patch both the version function and the environment
    with patch("importlib.metadata.version", side_effect=ImportError()):
        with patch.dict("os.environ", {}, clear=True):
            # We need to patch the import itself
            with patch.dict("sys.modules"):
                if "caylent_devcontainer_cli" in sys.modules:
                    del sys.modules["caylent_devcontainer_cli"]

                from caylent_devcontainer_cli import __version__

                assert __version__ == "0.1.0"
