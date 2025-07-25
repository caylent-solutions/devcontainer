#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.commands.code import handle_code, register_command


def test_register_command():
    mock_subparsers = MagicMock()
    mock_parser = MagicMock()
    mock_subparsers.add_parser.return_value = mock_parser

    register_command(mock_subparsers)

    mock_subparsers.add_parser.assert_called_once_with("code", help="Launch VS Code with the devcontainer environment")
    assert mock_parser.add_argument.call_count >= 2
    mock_parser.set_defaults.assert_called_once_with(func=handle_code)


@patch("caylent_devcontainer_cli.commands.code.find_project_root", return_value="/test/path")
@patch("os.path.isfile", side_effect=[False])
def test_handle_code_missing_config(mock_isfile, mock_find_project_root, capsys):
    args = MagicMock()
    args.project_root = "/test/path"

    with pytest.raises(SystemExit):
        handle_code(args)

    mock_find_project_root.assert_called_once_with("/test/path")
    mock_isfile.assert_called_once()

    captured = capsys.readouterr()
    assert "Configuration file not found" in captured.err


@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.code.find_project_root", return_value="/test/path")
@patch("os.path.isfile", side_effect=[True, True])
@patch("os.path.getmtime", side_effect=[200, 100])  # env_json is newer than shell_env
@patch("caylent_devcontainer_cli.commands.code.generate_shell_env")
@patch("subprocess.Popen")
def test_handle_code_regenerate_env(
    mock_popen, mock_generate, mock_getmtime, mock_isfile, mock_find_project_root, mock_gitignore, capsys
):
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    args = MagicMock()
    args.project_root = "/test/path"

    handle_code(args)

    mock_find_project_root.assert_called_once_with("/test/path")
    assert mock_isfile.call_count == 2
    assert mock_getmtime.call_count == 2
    mock_generate.assert_called_once()
    mock_popen.assert_called_once()

    captured = capsys.readouterr()
    assert "Generating environment variables" in captured.err


@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("subprocess.Popen")
@patch("os.environ.get", return_value="/bin/zsh")
def test_handle_code_custom_shell(mock_environ_get, mock_popen, mock_gitignore, capsys):
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    with patch("caylent_devcontainer_cli.commands.code.find_project_root", return_value="/test/path"):
        with patch("os.path.isfile", side_effect=[True, True]):
            with patch("os.path.getmtime", side_effect=[100, 200]):  # shell_env is newer than env_json
                args = MagicMock()
                args.project_root = "/test/path"

                handle_code(args)

                mock_popen.assert_called_once()
                mock_environ_get.assert_called_once_with("SHELL", "/bin/bash")

                # Check that the command uses the custom shell
                cmd_args = mock_popen.call_args[0][0]
                assert "source" in cmd_args
                assert "shell.env" in cmd_args
                assert "code" in cmd_args

                captured = capsys.readouterr()
                assert "Using existing shell.env file" in captured.err
                assert "VS Code launched" in captured.err
