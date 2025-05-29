#!/usr/bin/env python3
import json
import os
import sys
from unittest.mock import mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands.template import load_template, save_template, upgrade_template_file


def test_save_template_adds_version():
    """Test that save_template adds the CLI version to the template data."""
    mock_env_data = {"key": "value"}

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_env_data))), patch(
        "os.path.exists", return_value=True
    ), patch("json.load", return_value=mock_env_data), patch("json.dump") as mock_dump, patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ):

        save_template("/test/path", "test-template")

        # Verify json.dump was called with the env_data that includes cli_version
        mock_dump.assert_called_once()
        # First arg is the data dict, second arg is the file object
        saved_data = mock_dump.call_args[0][0]
        assert "cli_version" in saved_data
        assert saved_data["cli_version"] == __version__


def test_load_template_version_mismatch():
    """Test that load_template handles version mismatches correctly."""
    mock_template_data = {"key": "value", "cli_version": "1.0.0"}  # Old version

    # Mock current version to be 2.0.0
    with patch("caylent_devcontainer_cli.__version__", "2.0.0"), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_template_data))
    ), patch("os.path.exists", return_value=True), patch("builtins.input", return_value="4"), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "json.load", return_value=mock_template_data
    ), patch(
        "json.dump"
    ):
        # No need to mock sys.exit since it's not called in this test case
        load_template("/test/path", "test-template")


def test_load_template_upgrade_choice():
    """Test that load_template handles the upgrade choice correctly."""
    mock_template_data = {"key": "value", "cli_version": "1.0.0"}  # Old version
    upgraded_data = {"upgraded": True, "cli_version": "2.0.0"}

    # Mock current version to be 2.0.0
    with patch("caylent_devcontainer_cli.__version__", "2.0.0"), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_template_data))
    ), patch("os.path.exists", return_value=True), patch("builtins.input", return_value="1"), patch(
        "caylent_devcontainer_cli.commands.template.upgrade_template", return_value=upgraded_data
    ), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "json.load", return_value=mock_template_data
    ), patch(
        "json.dump"
    ):
        # Removed the mock_upgrade variable since it's not used
        load_template("/test/path", "test-template")


def test_load_template_new_profile_choice():
    """Test that load_template handles the new profile choice correctly."""
    mock_template_data = {"key": "value", "cli_version": "1.0.0"}  # Old version

    # Mock current version to be 2.0.0
    with patch("caylent_devcontainer_cli.__version__", "2.0.0"), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_template_data))
    ), patch("os.path.exists", return_value=True), patch("builtins.input", return_value="2"), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "json.load", return_value=mock_template_data
    ), patch(
        "json.dump"
    ):
        # No need to mock sys.exit since it's not called in this test case
        load_template("/test/path", "test-template")


def test_load_template_use_anyway_choice():
    """Test that load_template handles the 'use anyway' choice correctly."""
    mock_template_data = {"key": "value", "cli_version": "1.0.0"}  # Old version

    # Mock current version to be 2.0.0
    with patch("caylent_devcontainer_cli.__version__", "2.0.0"), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_template_data))
    ), patch("os.path.exists", return_value=True), patch("builtins.input", return_value="3"), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "json.load", return_value=mock_template_data
    ), patch(
        "json.dump"
    ):

        load_template("/test/path", "test-template")


def test_load_template_invalid_choice():
    """Test that load_template handles invalid choices correctly."""
    mock_template_data = {"key": "value", "cli_version": "1.0.0"}  # Old version

    # Mock current version to be 2.0.0
    with patch("caylent_devcontainer_cli.__version__", "2.0.0"), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_template_data))
    ), patch("os.path.exists", return_value=True), patch("builtins.input", side_effect=["invalid", "4"]), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "json.load", return_value=mock_template_data
    ), patch(
        "json.dump"
    ):
        # No need to mock sys.exit since it's not called in this test case
        load_template("/test/path", "test-template")


def test_upgrade_template_file():
    """Test that upgrade_template_file works correctly."""
    mock_template_data = {"key": "value", "cli_version": "1.0.0"}  # Old version
    mock_upgraded_data = {"key": "value", "cli_version": __version__}

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_template_data))), patch(
        "os.path.exists", return_value=True
    ), patch("json.load", return_value=mock_template_data), patch(
        "caylent_devcontainer_cli.commands.template.upgrade_template", return_value=mock_upgraded_data
    ) as mock_upgrade, patch(
        "json.dump"
    ):

        upgrade_template_file("test-template")
        mock_upgrade.assert_called_once_with(mock_template_data)
