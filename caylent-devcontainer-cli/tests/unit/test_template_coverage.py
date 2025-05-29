#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.template import (
    handle_template_delete,
    handle_template_list,
    handle_template_load,
    handle_template_save,
    handle_template_upgrade,
)


def test_handle_template_save():
    """Test handle_template_save function."""
    args = MagicMock()
    args.project_root = "/test/path"
    args.name = "test-template"

    with patch("caylent_devcontainer_cli.commands.template.save_template") as mock_save:
        handle_template_save(args)
        mock_save.assert_called_once_with("/test/path", "test-template")


def test_handle_template_save_no_project_root():
    """Test handle_template_save function with no project_root."""
    args = MagicMock()
    args.project_root = None
    args.name = "test-template"

    with patch("caylent_devcontainer_cli.commands.template.save_template") as mock_save, patch(
        "os.getcwd", return_value="/current/dir"
    ):
        handle_template_save(args)
        mock_save.assert_called_once_with("/current/dir", "test-template")


def test_handle_template_load():
    """Test handle_template_load function."""
    args = MagicMock()
    args.project_root = "/test/path"
    args.name = "test-template"

    with patch("caylent_devcontainer_cli.commands.template.load_template") as mock_load:
        handle_template_load(args)
        mock_load.assert_called_once_with("/test/path", "test-template")


def test_handle_template_load_no_project_root():
    """Test handle_template_load function with no project_root."""
    args = MagicMock()
    args.project_root = None
    args.name = "test-template"

    with patch("caylent_devcontainer_cli.commands.template.load_template") as mock_load, patch(
        "os.getcwd", return_value="/current/dir"
    ):
        handle_template_load(args)
        mock_load.assert_called_once_with("/current/dir", "test-template")


def test_handle_template_list():
    """Test handle_template_list function."""
    args = MagicMock()

    with patch("caylent_devcontainer_cli.commands.template.list_templates") as mock_list:
        handle_template_list(args)
        mock_list.assert_called_once()


def test_handle_template_delete():
    """Test handle_template_delete function."""
    args = MagicMock()
    args.names = ["template1", "template2"]

    with patch("caylent_devcontainer_cli.commands.template.delete_template") as mock_delete:
        handle_template_delete(args)
        assert mock_delete.call_count == 2
        mock_delete.assert_any_call("template1")
        mock_delete.assert_any_call("template2")


def test_handle_template_upgrade():
    """Test handle_template_upgrade function."""
    args = MagicMock()
    args.name = "test-template"

    with patch("caylent_devcontainer_cli.commands.template.upgrade_template_file") as mock_upgrade:
        handle_template_upgrade(args)
        mock_upgrade.assert_called_once_with("test-template")
