"""Functional tests for installation type detection."""

import unittest.mock as mock
from io import StringIO
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import _show_update_prompt


class TestInstallationDisplayIntegration(TestCase):
    """Test installation type display in update prompts."""

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_pipx_regular_display(self, mock_stdout, mock_editable, mock_pipx, mock_input):
        """Test pipx regular installation display."""
        mock_pipx.return_value = True
        mock_editable.return_value = False
        mock_input.return_value = "2"  # Continue without upgrading

        _show_update_prompt("1.10.0", "1.11.0")

        output = mock_stdout.getvalue()
        self.assertIn("Current version:", output)
        self.assertIn("1.10.0", output)
        self.assertIn("(pipx)", output)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_pipx_editable_display(self, mock_stdout, mock_editable, mock_pipx, mock_input):
        """Test pipx editable installation display."""
        mock_pipx.return_value = True
        mock_editable.return_value = True
        mock_input.return_value = "2"  # Continue without upgrading

        _show_update_prompt("1.10.0", "1.11.0")

        output = mock_stdout.getvalue()
        self.assertIn("Current version:", output)
        self.assertIn("1.10.0", output)
        self.assertIn("(pipx editable)", output)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_pip_regular_display(self, mock_stdout, mock_editable, mock_pipx, mock_input):
        """Test pip regular installation display."""
        mock_pipx.return_value = False
        mock_editable.return_value = False
        mock_input.return_value = "2"  # Continue without upgrading

        _show_update_prompt("1.10.0", "1.11.0")

        output = mock_stdout.getvalue()
        self.assertIn("Current version:", output)
        self.assertIn("1.10.0", output)
        self.assertIn("(pip)", output)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_pip_editable_display(self, mock_stdout, mock_editable, mock_pipx, mock_input):
        """Test pip editable installation display."""
        mock_pipx.return_value = False
        mock_editable.return_value = True
        mock_input.return_value = "2"  # Continue without upgrading

        _show_update_prompt("1.10.0", "1.11.0")

        output = mock_stdout.getvalue()
        self.assertIn("Current version:", output)
        self.assertIn("1.10.0", output)
        self.assertIn("(pip editable)", output)
