#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.utils.fs import find_project_root, generate_shell_env


def test_find_project_root_with_path():
    """Test find_project_root with a provided path."""
    with patch("os.path.isdir", return_value=True):
        result = find_project_root("/test/path")
        assert result == "/test/path"


def test_generate_shell_env_confirmation_cancel():
    """Test generate_shell_env when user cancels confirmation."""
    with patch("caylent_devcontainer_cli.utils.fs.load_json_config", return_value={"containerEnv": {"TEST": "value"}}):
        with patch("os.path.exists", return_value=True):
            with patch("caylent_devcontainer_cli.utils.fs.confirm_action", return_value=False):
                with pytest.raises(SystemExit):
                    generate_shell_env("/test/input.json", "/test/output.env")
