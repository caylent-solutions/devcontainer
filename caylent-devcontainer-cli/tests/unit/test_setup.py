#!/usr/bin/env python3
import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.setup import (
    clone_repo,
    copy_devcontainer_files,
    handle_setup,
    register_command,
    show_manual_instructions,
)


def test_register_command():
    mock_subparsers = MagicMock()
    mock_parser = MagicMock()
    mock_subparsers.add_parser.return_value = mock_parser

    register_command(mock_subparsers)

    mock_subparsers.add_parser.assert_called_once_with(
        "setup-devcontainer", help="Set up a devcontainer in a project directory"
    )
    assert mock_parser.add_argument.call_count >= 1
    mock_parser.set_defaults.assert_called_once_with(func=handle_setup)


@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
@patch("caylent_devcontainer_cli.commands.setup.show_manual_instructions")
@patch("caylent_devcontainer_cli.commands.setup.copy_devcontainer_files")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_interactive(
    mock_temp_dir, mock_clone, mock_copy, mock_show, mock_interactive, mock_create_version
):
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.update = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=False):
        handle_setup(args)

    mock_clone.assert_called_once()
    mock_interactive.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")


@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
@patch("caylent_devcontainer_cli.commands.setup.show_manual_instructions")
@patch("caylent_devcontainer_cli.commands.setup.copy_devcontainer_files")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_manual(mock_temp_dir, mock_clone, mock_copy, mock_show, mock_interactive, mock_create_version):
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = True
    args.update = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=False):
        handle_setup(args)

    mock_clone.assert_called_once()
    mock_copy.assert_called_once()
    mock_show.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")


@patch("subprocess.run")
def test_clone_repo_success(mock_run):
    clone_repo("/tmp/test", "0.1.0")
    mock_run.assert_called_once()


@patch("subprocess.run", side_effect=[subprocess.CalledProcessError(1, "git"), None])
def test_clone_repo_fallback(mock_run):
    clone_repo("/tmp/test", "0.1.0")
    assert mock_run.call_count == 2


@patch("shutil.copytree")
@patch("os.path.exists", return_value=False)
def test_copy_devcontainer_files(mock_exists, mock_copytree):
    copy_devcontainer_files("/source", "/target")
    mock_copytree.assert_called_once_with("/source/.devcontainer", "/target/.devcontainer")


@patch("shutil.copytree")
@patch("os.path.exists", return_value=True)
@patch("caylent_devcontainer_cli.commands.setup.confirm_action", return_value=True)
@patch("shutil.rmtree")
def test_copy_devcontainer_files_overwrite(mock_rmtree, mock_confirm, mock_exists, mock_copytree):
    copy_devcontainer_files("/source", "/target")
    mock_rmtree.assert_called_once()
    mock_copytree.assert_called_once()


@patch("shutil.copytree")
@patch("os.path.exists", return_value=True)
@patch("caylent_devcontainer_cli.commands.setup.confirm_action", return_value=False)
@patch("sys.exit")
def test_copy_devcontainer_files_cancel(mock_exit, mock_confirm, mock_exists, mock_copytree):
    copy_devcontainer_files("/source", "/target")
    mock_exit.assert_called_once_with(0)
    mock_copytree.assert_not_called()


def test_show_manual_instructions(capsys):
    show_manual_instructions("/test/path")
    captured = capsys.readouterr()
    assert "Next steps" in captured.out
    assert "devcontainer-environment-variables.json" in captured.out
    assert "aws-profile-map.json" in captured.out
