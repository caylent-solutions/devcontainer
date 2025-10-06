"""Functional tests for upgrade scenarios."""

import unittest.mock as mock
from io import StringIO
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import (
    EXIT_UPGRADE_REQUESTED_ABORT,
    _show_manual_upgrade_instructions,
    _show_update_prompt,
)


class TestUpgradeScenarios(TestCase):
    """Test upgrade scenarios for different installation types."""

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pipx_regular_option1_upgrade(self, mock_editable, mock_pipx, mock_input):
        """Test Option 1 manual upgrade for pipx regular installation."""
        mock_pipx.return_value = True
        mock_editable.return_value = False
        mock_input.return_value = "1"

        result = _show_update_prompt("1.10.0", "1.11.0")

        self.assertEqual(result, EXIT_UPGRADE_REQUESTED_ABORT)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pipx_editable_option1_upgrade(self, mock_editable, mock_pipx, mock_input):
        """Test Option 1 manual upgrade for pipx editable installation."""
        mock_pipx.return_value = True
        mock_editable.return_value = True
        mock_input.return_value = "1"

        result = _show_update_prompt("1.10.0", "1.11.0")

        self.assertEqual(result, EXIT_UPGRADE_REQUESTED_ABORT)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pip_regular_option1_upgrade(self, mock_editable, mock_pipx, mock_input):
        """Test Option 1 manual upgrade for pip regular installation."""
        mock_pipx.return_value = False
        mock_editable.return_value = False
        mock_input.return_value = "1"

        result = _show_update_prompt("1.10.0", "1.11.0")

        self.assertEqual(result, EXIT_UPGRADE_REQUESTED_ABORT)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pip_editable_option1_upgrade(self, mock_editable, mock_pipx, mock_input):
        """Test Option 1 manual upgrade for pip editable installation."""
        mock_pipx.return_value = False
        mock_editable.return_value = True
        mock_input.return_value = "1"

        result = _show_update_prompt("1.10.0", "1.11.0")

        self.assertEqual(result, EXIT_UPGRADE_REQUESTED_ABORT)


class TestManualInstructionsWithPipxDetection(TestCase):
    """Test manual instructions adapt based on pipx availability."""

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_manual_instructions_pip(self, mock_stdout):
        """Test manual instructions for pip installation."""
        _show_manual_upgrade_instructions("pip")

        output = mock_stdout.getvalue()
        self.assertIn("First, install pipx:", output)
        self.assertIn("python -m pip install pipx", output)
        self.assertIn("Switch to pipx:", output)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_manual_instructions_pipx(self, mock_stdout):
        """Test manual instructions for pipx installation."""
        _show_manual_upgrade_instructions("pipx")

        output = mock_stdout.getvalue()
        self.assertIn("First, install pipx:", output)
        self.assertIn("Upgrade with pipx:", output)
        self.assertIn("pipx upgrade caylent-devcontainer-cli", output)
