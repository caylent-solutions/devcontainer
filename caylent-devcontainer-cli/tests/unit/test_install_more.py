#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.install import (
    handle_install,
    handle_uninstall,
)


def test_handle_install_with_path():
    """Test handling install command with custom path."""
    args = MagicMock()
    args.path = "/custom/path"

    with patch("caylent_devcontainer_cli.commands.install.install_cli") as mock_install:
        handle_install(args)
        mock_install.assert_called_once()


def test_handle_uninstall_with_path():
    """Test handling uninstall command with custom path."""
    args = MagicMock()
    args.path = "/custom/path"

    with patch("caylent_devcontainer_cli.commands.install.uninstall_cli") as mock_uninstall:
        handle_uninstall(args)
        mock_uninstall.assert_called_once()
