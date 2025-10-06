"""Functional tests for upgrade scenarios."""

import unittest.mock as mock
from io import StringIO
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import (
    EXIT_UPGRADE_PERFORMED,
    _show_manual_upgrade_instructions,
    _show_update_prompt,
)


class TestUpgradeScenarios(TestCase):
    """Test upgrade scenarios for different installation types."""

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._upgrade_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pipx_regular_option1_upgrade(self, mock_editable, mock_pipx, mock_upgrade, mock_input):
        """Test Option 1 automatic upgrade for pipx regular installation."""
        mock_pipx.return_value = True
        mock_editable.return_value = False
        mock_input.return_value = "1"
        mock_upgrade.return_value = EXIT_UPGRADE_PERFORMED

        result = _show_update_prompt("1.10.0", "1.11.0")

        mock_upgrade.assert_called_once()
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._upgrade_to_pipx_from_pypi")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pipx_editable_option1_upgrade(self, mock_editable, mock_pipx, mock_upgrade, mock_input):
        """Test Option 1 automatic upgrade for pipx editable installation."""
        mock_pipx.return_value = True
        mock_editable.return_value = True
        mock_input.return_value = "1"
        mock_upgrade.return_value = EXIT_UPGRADE_PERFORMED

        result = _show_update_prompt("1.10.0", "1.11.0")

        mock_upgrade.assert_called_once_with("pipx editable")
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._upgrade_to_pipx_from_pypi")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pip_regular_option1_upgrade(self, mock_editable, mock_pipx, mock_upgrade, mock_input):
        """Test Option 1 automatic upgrade for pip regular installation."""
        mock_pipx.return_value = False
        mock_editable.return_value = False
        mock_input.return_value = "1"
        mock_upgrade.return_value = EXIT_UPGRADE_PERFORMED

        result = _show_update_prompt("1.10.0", "1.11.0")

        mock_upgrade.assert_called_once_with("pip")
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._upgrade_to_pipx_from_pypi")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pip_editable_option1_upgrade(self, mock_editable, mock_pipx, mock_upgrade, mock_input):
        """Test Option 1 automatic upgrade for pip editable installation."""
        mock_pipx.return_value = False
        mock_editable.return_value = True
        mock_input.return_value = "1"
        mock_upgrade.return_value = EXIT_UPGRADE_PERFORMED

        result = _show_update_prompt("1.10.0", "1.11.0")

        mock_upgrade.assert_called_once_with("pip editable")
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)


class TestManualInstructionsWithPipxDetection(TestCase):
    """Test manual instructions adapt based on pipx availability."""

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_manual_instructions_without_pipx(self, mock_stdout, mock_pipx_available):
        """Test manual instructions when pipx is not available."""
        mock_pipx_available.return_value = False

        _show_manual_upgrade_instructions("pip")

        output = mock_stdout.getvalue()
        self.assertIn("First, install pipx:", output)
        self.assertIn("python -m pip install pipx", output)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_manual_instructions_with_pipx(self, mock_stdout, mock_pipx_available):
        """Test manual instructions when pipx is available."""
        mock_pipx_available.return_value = True

        _show_manual_upgrade_instructions("pip")

        output = mock_stdout.getvalue()
        self.assertNotIn("First, install pipx:", output)
        self.assertIn("Switch to pipx:", output)
