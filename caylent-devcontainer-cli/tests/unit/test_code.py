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

    mock_subparsers.add_parser.assert_called_once_with(
        "code", help="Launch IDE (VS Code, Cursor) with the devcontainer environment"
    )
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


@patch("shutil.which", return_value="/usr/bin/code")
@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.code.find_project_root", return_value="/test/path")
@patch("os.path.isfile", side_effect=[True, True])
@patch("os.path.getmtime", side_effect=[200, 100])  # env_json is newer than shell_env
@patch("caylent_devcontainer_cli.commands.code.generate_shell_env")
@patch("subprocess.Popen")
def test_handle_code_regenerate_env(
    mock_popen, mock_generate, mock_getmtime, mock_isfile, mock_find_project_root, mock_gitignore, mock_which, capsys
):
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "vscode"

    handle_code(args)

    mock_find_project_root.assert_called_once_with("/test/path")
    assert mock_isfile.call_count == 2
    assert mock_getmtime.call_count == 2
    mock_generate.assert_called_once()
    mock_popen.assert_called_once()

    captured = capsys.readouterr()
    assert "Generating environment variables" in captured.err


@patch("shutil.which", return_value="/usr/bin/code")
@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("subprocess.Popen")
@patch("os.environ.get", return_value="/bin/zsh")
def test_handle_code_custom_shell(mock_environ_get, mock_popen, mock_gitignore, mock_which, capsys):
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    with patch("caylent_devcontainer_cli.commands.code.find_project_root", return_value="/test/path"):
        with patch("os.path.isfile", side_effect=[True, True]):
            with patch("os.path.getmtime", side_effect=[100, 200]):  # shell_env is newer than env_json
                args = MagicMock()
                args.project_root = "/test/path"
                args.ide = "vscode"

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


@patch("shutil.which", return_value="/usr/bin/cursor")
@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.code.find_project_root", return_value="/test/path")
@patch("os.path.isfile", side_effect=[True, True])
@patch("os.path.getmtime", side_effect=[200, 100])
@patch("caylent_devcontainer_cli.commands.code.generate_shell_env")
@patch("subprocess.Popen")
def test_handle_code_cursor(
    mock_popen, mock_generate, mock_getmtime, mock_isfile, mock_find_project_root, mock_gitignore, mock_which, capsys
):
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "cursor"

    handle_code(args)

    mock_which.assert_called_once_with("cursor")
    mock_popen.assert_called_once()
    cmd_args = mock_popen.call_args[0][0]
    assert "cursor" in cmd_args
    assert "/test/path" in cmd_args

    captured = capsys.readouterr()
    assert "Launching Cursor" in captured.err
    assert "Cursor launched" in captured.err


@patch("shutil.which", return_value=None)
@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.code.find_project_root", return_value="/test/path")
@patch("os.path.isfile", side_effect=[True, True])
@patch("os.path.getmtime", side_effect=[200, 100])
@patch("caylent_devcontainer_cli.commands.code.generate_shell_env")
def test_handle_code_ide_not_found(
    mock_generate, mock_getmtime, mock_isfile, mock_find_project_root, mock_gitignore, mock_which, capsys
):
    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "vscode"

    with pytest.raises(SystemExit):
        handle_code(args)

    mock_which.assert_called_once_with("code")
    captured = capsys.readouterr()
    assert "VS Code command 'code' not found in PATH" in captured.err
    assert "Please install VS Code" in captured.err


@patch("shutil.which", return_value=None)
@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.code.find_project_root", return_value="/test/path")
@patch("os.path.isfile", side_effect=[True, True])
@patch("os.path.getmtime", side_effect=[200, 100])
@patch("caylent_devcontainer_cli.commands.code.generate_shell_env")
def test_handle_code_cursor_not_found(
    mock_generate, mock_getmtime, mock_isfile, mock_find_project_root, mock_gitignore, mock_which, capsys
):
    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "cursor"

    with pytest.raises(SystemExit):
        handle_code(args)

    mock_which.assert_called_once_with("cursor")
    captured = capsys.readouterr()
    assert "Cursor command 'cursor' not found in PATH" in captured.err
    assert "Please install Cursor" in captured.err


@patch("shutil.which", return_value="/usr/bin/code")
@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.code.find_project_root", return_value="/test/path")
@patch("os.path.isfile", side_effect=[True, True])
@patch("os.path.getmtime", side_effect=[200, 100])
@patch("caylent_devcontainer_cli.commands.code.generate_shell_env")
@patch("subprocess.Popen", side_effect=Exception("Launch failed"))
def test_handle_code_launch_failure(
    mock_popen, mock_generate, mock_getmtime, mock_isfile, mock_find_project_root, mock_gitignore, mock_which, capsys
):
    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "vscode"

    with pytest.raises(SystemExit):
        handle_code(args)

    captured = capsys.readouterr()
    assert "Failed to launch VS Code: Launch failed" in captured.err


def test_register_command_ide_choices():
    """Test that register_command adds IDE choices correctly."""
    mock_subparsers = MagicMock()
    mock_parser = MagicMock()
    mock_subparsers.add_parser.return_value = mock_parser

    register_command(mock_subparsers)

    # Check that --ide argument was added with correct choices
    ide_call = None
    for call in mock_parser.add_argument.call_args_list:
        if call[0][0] == "--ide":
            ide_call = call
            break

    assert ide_call is not None
    assert ide_call[1]["choices"] == ["vscode", "cursor"]
    assert ide_call[1]["default"] == "vscode"
    assert "IDE to launch" in ide_call[1]["help"]


def test_ide_config_structure():
    """Test that IDE_CONFIG has the expected structure."""
    from caylent_devcontainer_cli.commands.code import IDE_CONFIG

    assert "vscode" in IDE_CONFIG
    assert "cursor" in IDE_CONFIG

    for ide_key, config in IDE_CONFIG.items():
        assert "command" in config
        assert "name" in config
        assert "install_instructions" in config
        assert isinstance(config["command"], str)
        assert isinstance(config["name"], str)
        assert isinstance(config["install_instructions"], str)

    # Test specific configurations
    assert IDE_CONFIG["vscode"]["command"] == "code"
    assert IDE_CONFIG["vscode"]["name"] == "VS Code"
    assert IDE_CONFIG["cursor"]["command"] == "cursor"
    assert IDE_CONFIG["cursor"]["name"] == "Cursor"
