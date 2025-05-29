#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.commands.template import (
    delete_template,
    handle_template_delete,
    handle_template_upgrade,
    upgrade_template_file,
)


def test_handle_template_delete():
    """Test handling template delete command."""
    args = MagicMock()
    args.names = ["template1", "template2"]

    with patch("caylent_devcontainer_cli.commands.template.delete_template") as mock_delete:
        handle_template_delete(args)
        assert mock_delete.call_count == 2
        mock_delete.assert_any_call("template1")
        mock_delete.assert_any_call("template2")


def test_handle_template_upgrade():
    """Test handling template upgrade command."""
    args = MagicMock()
    args.name = "template1"

    with patch("caylent_devcontainer_cli.commands.template.upgrade_template_file") as mock_upgrade:
        handle_template_upgrade(args)
        mock_upgrade.assert_called_once_with("template1")


def test_delete_template():
    """Test deleting a template."""
    template_name = "template1"

    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove, patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch("caylent_devcontainer_cli.utils.ui.log"), patch(
        "caylent_devcontainer_cli.commands.template.TEMPLATES_DIR", "/templates"
    ):
        delete_template(template_name)

        # Check that os.remove was called
        mock_remove.assert_called_once_with("/templates/template1.json")


def test_delete_template_not_found():
    """Test deleting a template that doesn't exist."""
    template_name = "template1"

    with patch("os.path.exists", return_value=False), patch("os.remove") as mock_remove, patch(
        "caylent_devcontainer_cli.utils.ui.log"
    ), patch("caylent_devcontainer_cli.commands.template.TEMPLATES_DIR", "/templates"):
        delete_template(template_name)

        # Check that os.remove was not called
        mock_remove.assert_not_called()


def test_delete_template_cancel():
    """Test canceling template deletion."""
    template_name = "template1"

    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove, patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=False
    ), patch("caylent_devcontainer_cli.utils.ui.log"), patch(
        "caylent_devcontainer_cli.commands.template.TEMPLATES_DIR", "/templates"
    ):
        delete_template(template_name)

        # Check that os.remove was not called
        mock_remove.assert_not_called()


def test_upgrade_template_file():
    """Test upgrading a template file."""
    template_name = "template1"
    mock_template_data = {"containerEnv": {"AWS_CONFIG_ENABLED": "true"}, "cli_version": "1.0.0"}

    with patch("os.path.exists", return_value=True), patch("builtins.open"), patch(
        "json.load", return_value=mock_template_data
    ), patch("json.dump"), patch(
        "caylent_devcontainer_cli.commands.template.upgrade_template",
        return_value={"containerEnv": {"AWS_CONFIG_ENABLED": "true"}, "cli_version": "2.0.0"},
    ), patch(
        "caylent_devcontainer_cli.__version__", "2.0.0"
    ), patch(
        "caylent_devcontainer_cli.utils.ui.log"
    ), patch(
        "caylent_devcontainer_cli.commands.template.TEMPLATES_DIR", "/templates"
    ):
        upgrade_template_file(template_name)


def test_upgrade_template_file_not_found():
    """Test upgrading a template file that doesn't exist."""
    template_name = "template1"

    with patch("os.path.exists", return_value=False), patch("caylent_devcontainer_cli.utils.ui.log"), patch(
        "sys.exit", side_effect=SystemExit(1)
    ), patch("caylent_devcontainer_cli.commands.template.TEMPLATES_DIR", "/templates"):
        with pytest.raises(SystemExit):
            upgrade_template_file(template_name)
