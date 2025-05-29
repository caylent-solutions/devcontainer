#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.commands.template import save_template, upgrade_template_file


def test_save_template_no_env_file():
    """Test save_template when environment file doesn't exist."""
    with patch("os.path.exists", return_value=False):
        with pytest.raises(SystemExit):
            save_template("/test/path", "test-template")


def test_upgrade_template_file_version_check():
    """Test upgrade_template_file with version check."""
    template_data = {"cli_version": "1.0.0"}

    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("json.load", return_value=template_data):
                with patch("json.dump"):
                    with patch("caylent_devcontainer_cli.__version__", "1.0.0"):
                        with patch("semver.VersionInfo.parse") as mock_parse:
                            mock_parse.return_value = MagicMock(major=1, minor=0)
                            upgrade_template_file("test-template")
