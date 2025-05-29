#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands.setup import create_version_file, handle_setup


@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_creates_version_file(mock_temp_dir, mock_clone, mock_interactive, mock_create_version):
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
@patch("caylent_devcontainer_cli.commands.setup.copy_devcontainer_files")
@patch("caylent_devcontainer_cli.commands.setup.show_manual_instructions")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_manual_creates_version_file(mock_temp_dir, mock_clone, mock_show, mock_copy, mock_create_version):
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


@patch("builtins.open", new_callable=mock_open)
def test_create_version_file(mock_file):
    target_path = "/test/path"
    create_version_file(target_path)

    mock_file.assert_called_once_with(os.path.join(target_path, ".devcontainer", "VERSION"), "w")
    mock_file().write.assert_called_once_with(__version__ + "\n")


@patch("caylent_devcontainer_cli.commands.setup.confirm_action", return_value=True)
@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_with_existing_version(
    mock_temp_dir, mock_clone, mock_interactive, mock_create_version, mock_confirm
):
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.update = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data="0.1.0")
    ):
        handle_setup(args)

    mock_confirm.assert_called_once()
    mock_clone.assert_called_once()
    mock_interactive.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")


@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_update_mode(mock_temp_dir, mock_clone, mock_interactive, mock_create_version):
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.update = True

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=True):
        handle_setup(args)

    mock_clone.assert_called_once()
    mock_interactive.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")
