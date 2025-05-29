#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.commands.setup import handle_setup


def test_handle_setup_update_mode():
    """Test handling setup in update mode."""
    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.update = True

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=True), patch(
        "caylent_devcontainer_cli.commands.setup.clone_repo"
    ), patch("caylent_devcontainer_cli.commands.setup.interactive_setup"), patch(
        "caylent_devcontainer_cli.commands.setup.create_version_file"
    ) as mock_create_version:
        handle_setup(args)
        mock_create_version.assert_called_once_with("/test/path")


def test_handle_setup_update_mode_no_devcontainer():
    """Test handling setup in update mode when no devcontainer exists."""
    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.update = True

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=False), patch(
        "sys.exit", side_effect=SystemExit(1)
    ) as mock_exit:
        with pytest.raises(SystemExit):
            handle_setup(args)
        mock_exit.assert_called_once_with(1)


def test_handle_setup_with_existing_version():
    """Test handling setup when a version file already exists."""
    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.update = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", side_effect=[True, True]), patch(
        "builtins.open", mock_open(read_data="1.0.0")
    ), patch("caylent_devcontainer_cli.commands.setup.confirm_action", return_value=True), patch(
        "caylent_devcontainer_cli.commands.setup.clone_repo"
    ), patch(
        "caylent_devcontainer_cli.commands.setup.interactive_setup"
    ), patch(
        "caylent_devcontainer_cli.commands.setup.create_version_file"
    ):
        handle_setup(args)


def test_handle_setup_with_existing_version_cancel():
    """Test handling setup when a version file exists but user cancels."""
    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.update = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", side_effect=[True, True]), patch(
        "builtins.open", mock_open(read_data="1.0.0")
    ), patch("caylent_devcontainer_cli.commands.setup.confirm_action", return_value=False), patch(
        "sys.exit", side_effect=SystemExit(0)
    ) as mock_exit:
        with pytest.raises(SystemExit):
            handle_setup(args)
        mock_exit.assert_called_once_with(0)


def test_handle_setup_with_existing_no_version():
    """Test handling setup when devcontainer exists but has no version."""
    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.update = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", side_effect=[True, False]), patch(
        "caylent_devcontainer_cli.commands.setup.confirm_action", return_value=True
    ), patch("caylent_devcontainer_cli.commands.setup.clone_repo"), patch(
        "caylent_devcontainer_cli.commands.setup.interactive_setup"
    ), patch(
        "caylent_devcontainer_cli.commands.setup.create_version_file"
    ):
        handle_setup(args)


def test_handle_setup_with_existing_no_version_cancel():
    """Test handling setup when devcontainer exists with no version but user cancels."""
    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.update = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", side_effect=[True, False]), patch(
        "caylent_devcontainer_cli.commands.setup.confirm_action", return_value=False
    ), patch("sys.exit", side_effect=SystemExit(0)) as mock_exit:
        with pytest.raises(SystemExit):
            handle_setup(args)
        mock_exit.assert_called_once_with(0)
