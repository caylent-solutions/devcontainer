"""Functional tests for interactive upgrade flows."""

import unittest.mock as mock
from io import StringIO
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import (
    EXIT_OK,
    EXIT_UPGRADE_PERFORMED,
    EXIT_UPGRADE_REQUESTED_ABORT,
    _show_update_prompt,
)


class TestInteractiveUpgradeFlow(TestCase):
    """Test interactive upgrade user flows."""

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_pipx_upgrade_choice_continue(self, mock_stdout, mock_editable, mock_pipx, mock_input):
        """Test pipx installation with continue choice."""
        mock_pipx.return_value = True
        mock_editable.return_value = False
        mock_input.return_value = "2"  # Continue without upgrading (now option 2)

        result = _show_update_prompt("1.10.0", "1.11.0")

        self.assertEqual(result, EXIT_OK)
        output = mock_stdout.getvalue()
        self.assertIn("Update Available", output)
        # Remove ANSI color codes for comparison
        clean_output = output.replace("\x1b[1;31m", "").replace("\x1b[0m", "")
        self.assertIn("Current version: 1.10.0", clean_output)
        self.assertIn("Latest version:  1.11.0", output)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_pipx_upgrade_choice_manual(self, mock_stdout, mock_editable, mock_pipx, mock_input):
        """Test pipx installation with manual upgrade choice."""
        mock_pipx.return_value = True
        mock_editable.return_value = False
        mock_input.return_value = "1"  # Exit and upgrade manually (now option 1)

        result = _show_update_prompt("1.10.0", "1.11.0")

        self.assertEqual(result, EXIT_UPGRADE_REQUESTED_ABORT)
        output = mock_stdout.getvalue()
        self.assertIn("Exiting so you can upgrade manually", output)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_pip_installation_flow(self, mock_stdout, mock_editable, mock_pipx, mock_input):
        """Test pip installation upgrade flow."""
        mock_pipx.return_value = False
        mock_editable.return_value = False
        mock_input.return_value = "1"  # Exit and upgrade manually

        result = _show_update_prompt("1.10.0", "1.11.0")

        self.assertEqual(result, EXIT_UPGRADE_REQUESTED_ABORT)  # Now exits for manual upgrade
        output = mock_stdout.getvalue()
        self.assertIn("Select an option:", output)
        self.assertIn("Exit and upgrade manually", output)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_editable_installation_flow(self, mock_stdout, mock_editable, mock_pipx, mock_input):
        """Test editable installation upgrade flow."""
        mock_pipx.return_value = False
        mock_editable.return_value = True
        mock_input.return_value = "1"  # Exit and upgrade manually

        result = _show_update_prompt("1.10.0", "1.11.0")

        self.assertEqual(result, EXIT_UPGRADE_REQUESTED_ABORT)  # Now exits for manual upgrade
        output = mock_stdout.getvalue()
        self.assertIn("Select an option:", output)
        self.assertIn("Exit and upgrade manually", output)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_default_choice_handling(self, mock_editable, mock_pipx, mock_input):
        """Test default choice handling (empty input)."""
        mock_pipx.return_value = True
        mock_editable.return_value = False
        mock_input.return_value = ""  # Empty input should use default [1]

        result = _show_update_prompt("1.10.0", "1.11.0")
        self.assertEqual(result, EXIT_UPGRADE_REQUESTED_ABORT)  # Default is now manual upgrade

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_invalid_choice_handling(self, mock_editable, mock_pipx, mock_input):
        """Test invalid choice defaults to continue."""
        mock_pipx.return_value = True
        mock_editable.return_value = False
        mock_input.return_value = "99"  # Invalid choice

        result = _show_update_prompt("1.10.0", "1.11.0")
        self.assertEqual(result, EXIT_OK)  # Should default to continue
