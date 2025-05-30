#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.commands.install import (
    handle_install,
    handle_uninstall,
    install_cli,
    register_command,
    uninstall_cli,
)


def test_register_command():
    mock_subparsers = MagicMock()
    mock_parser = MagicMock()
    mock_subparsers.add_parser.return_value = mock_parser

    register_command(mock_subparsers)

    assert mock_subparsers.add_parser.call_count >= 1
    assert mock_parser.set_defaults.call_count >= 1


def test_handle_install():
    with patch("caylent_devcontainer_cli.commands.install.install_cli") as mock_install:
        args = MagicMock()
        handle_install(args)
        mock_install.assert_called_once()


def test_handle_uninstall():
    with patch("caylent_devcontainer_cli.commands.install.uninstall_cli") as mock_uninstall:
        args = MagicMock()
        handle_uninstall(args)
        mock_uninstall.assert_called_once()


@patch("caylent_devcontainer_cli.commands.install.confirm_action", return_value=True)
@patch("shutil.copy2")
@patch("os.chmod")
@patch("os.environ.get", return_value="/usr/local/bin:/usr/bin")
def test_install_cli(mock_environ_get, mock_chmod, mock_copy, mock_confirm, capsys):
    with patch("os.makedirs") as mock_makedirs:
        with patch("caylent_devcontainer_cli.commands.install.INSTALL_DIR", "/usr/local/bin"):
            with patch("os.path.exists", return_value=True):
                install_cli()

                mock_makedirs.assert_called_once()
                mock_copy.assert_called_once()
                mock_chmod.assert_called_once()

                captured = capsys.readouterr()
                assert "installed successfully" in captured.err


@patch("os.path.exists", return_value=True)
@patch("os.remove")
@patch("caylent_devcontainer_cli.commands.install.confirm_action", return_value=True)
def test_uninstall_cli(mock_confirm, mock_remove, mock_exists, capsys):
    uninstall_cli()

    mock_exists.assert_called_once()
    mock_confirm.assert_called_once()
    mock_remove.assert_called_once()

    captured = capsys.readouterr()
    assert "uninstalled successfully" in captured.err


@patch("os.path.exists", return_value=False)
def test_uninstall_cli_not_installed(mock_exists, capsys):
    uninstall_cli()

    mock_exists.assert_called_once()

    captured = capsys.readouterr()
    assert "not installed" in captured.err


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


def test_install_cli_script_not_found():
    """Test install_cli when script is not found."""
    with patch("os.path.exists", return_value=False):
        with pytest.raises(SystemExit):
            install_cli()


def test_install_cli_with_path_in_env():
    """Test install_cli when INSTALL_DIR is already in PATH."""
    with patch("os.path.exists", side_effect=[True, True, True]):
        with patch("caylent_devcontainer_cli.commands.install.confirm_action", return_value=True):
            with patch("shutil.copy2"):
                with patch("os.chmod"):
                    with patch("os.makedirs"):
                        with patch("os.environ.get") as mock_env_get:
                            # Mock PATH to include INSTALL_DIR
                            mock_env_get.return_value = "/usr/local/bin:/usr/bin:/bin"
                            with patch("caylent_devcontainer_cli.commands.install.INSTALL_DIR", "/usr/local/bin"):
                                install_cli()
