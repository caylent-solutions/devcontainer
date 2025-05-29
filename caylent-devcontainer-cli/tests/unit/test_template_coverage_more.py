#!/usr/bin/env python3
import os
import sys
from unittest.mock import mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.template import (
    ensure_templates_dir,
    list_templates,
)


def test_ensure_templates_dir_creates_dir():
    """Test ensure_templates_dir creates directory if it doesn't exist."""
    with patch("os.makedirs") as mock_makedirs, patch(
        "caylent_devcontainer_cli.commands.template.TEMPLATES_DIR", "/test/templates"
    ):
        ensure_templates_dir()
        mock_makedirs.assert_called_once_with("/test/templates", exist_ok=True)


def test_list_templates_with_no_templates():
    """Test list_templates when no templates are found."""
    with patch("os.path.exists", return_value=True), patch("os.listdir", return_value=[]), patch(
        "caylent_devcontainer_cli.utils.ui.COLORS", {"YELLOW": "", "RESET": ""}
    ), patch("builtins.print") as mock_print:
        list_templates()
        mock_print.assert_called_once_with("No templates found. Create one with 'template save <n>'")


def test_list_templates_with_templates():
    """Test list_templates with templates."""
    with patch("os.path.exists", return_value=True), patch(
        "os.listdir", return_value=["template1.json", "template2.json"]
    ), patch("builtins.open", mock_open()), patch("json.load", side_effect=[{"cli_version": "1.0.0"}, {}]), patch(
        "caylent_devcontainer_cli.utils.ui.COLORS", {"CYAN": "", "GREEN": "", "RESET": ""}
    ), patch(
        "builtins.print"
    ) as mock_print:
        list_templates()
        mock_print.assert_any_call("Available templates:")
        mock_print.assert_any_call("  - template1 (created with CLI version 1.0.0)")
        mock_print.assert_any_call("  - template2 (created with CLI version unknown)")
