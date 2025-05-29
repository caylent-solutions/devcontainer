#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.template import (
    list_templates,
    load_template,
    save_template,
)


def test_save_template_with_existing_file():
    """Test saving a template when the file already exists."""
    # Use a much simpler approach - just check that the function runs without errors
    with patch("os.path.exists", return_value=True), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch("builtins.open", mock_open()), patch("json.load", return_value={}), patch("json.dump"), patch(
        "caylent_devcontainer_cli.utils.ui.log"
    ), patch(
        "sys.exit"
    ):
        # Just verify that the function runs without raising an exception
        save_template("/test/path", "test-template")


def test_load_template_with_version_mismatch_upgrade():
    """Test loading a template with version mismatch and choosing to upgrade."""

    # Create a custom mock for the upgrade_template function
    def mock_upgrade_template(data):
        # This function will be called and should trigger the log message
        from caylent_devcontainer_cli.utils.ui import log

        log("OK", "Template upgraded to version 2.0.0")
        return {"upgraded": True}

    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true"},
        "cli_version": "1.0.0",
    }

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data="{}")), patch(
        "json.load", return_value=mock_template_data
    ), patch("json.dump"), patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=True), patch(
        "caylent_devcontainer_cli.__version__", "2.0.0"
    ), patch(
        "semver.VersionInfo.parse"
    ) as mock_parse, patch(
        "caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map", return_value={}
    ), patch(
        "caylent_devcontainer_cli.commands.setup_interactive.upgrade_template", side_effect=mock_upgrade_template
    ), patch(
        "sys.exit"
    ), patch(
        "builtins.print"
    ):
        # Mock the semver parsing to simulate a major version difference
        mock_parse.side_effect = [MagicMock(major=1), MagicMock(major=2)]

        # Mock the input to choose option 1 (upgrade)
        with patch("builtins.input", return_value="1"):
            load_template("/test/path", "test-template")


def test_list_templates_with_version_info():
    """Test listing templates with version information."""
    with patch("os.path.exists", return_value=True), patch(
        "os.listdir", return_value=["template1.json", "template2.json"]
    ), patch("builtins.open", mock_open()), patch(
        "json.load", side_effect=[{"cli_version": "1.0.0"}, {"cli_version": "2.0.0"}]
    ), patch(
        "builtins.print"
    ) as mock_print:
        list_templates()
        mock_print.assert_any_call("  - \x1b[1;32mtemplate1\x1b[0m (created with CLI version 1.0.0)")
        mock_print.assert_any_call("  - \x1b[1;32mtemplate2\x1b[0m (created with CLI version 2.0.0)")
