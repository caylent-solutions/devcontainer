#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.utils.fs import generate_shell_env


def test_generate_shell_env_new_file():
    """Test generate_shell_env when creating a new file."""
    with patch("caylent_devcontainer_cli.utils.fs.load_json_config", return_value={"containerEnv": {"TEST": "value"}}):
        with patch("os.path.exists", return_value=False):
            with patch("caylent_devcontainer_cli.utils.fs.confirm_action", return_value=True):
                with patch("builtins.open", MagicMock()):
                    generate_shell_env("/test/input.json", "/test/output.env")
