"""Unit tests for installation type detection."""

import json
import unittest.mock as mock
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import (
    _get_installation_type_display,
    _is_editable_installation,
    _is_installed_with_pipx,
)


class TestInstallationDetection(TestCase):
    """Test installation type detection logic."""

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pipx_regular_detection(self, mock_editable, mock_pipx):
        """Test detection of pipx regular installation."""
        mock_pipx.return_value = True
        mock_editable.return_value = False

        result = _get_installation_type_display()
        self.assertEqual(result, "pipx")

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pipx_editable_detection(self, mock_editable, mock_pipx):
        """Test detection of pipx editable installation."""
        mock_pipx.return_value = True
        mock_editable.return_value = True

        result = _get_installation_type_display()
        self.assertEqual(result, "pipx editable")

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pip_regular_detection(self, mock_editable, mock_pipx):
        """Test detection of pip regular installation."""
        mock_pipx.return_value = False
        mock_editable.return_value = False

        result = _get_installation_type_display()
        self.assertEqual(result, "pip")

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_pip_editable_detection(self, mock_editable, mock_pipx):
        """Test detection of pip editable installation."""
        mock_pipx.return_value = False
        mock_editable.return_value = True

        result = _get_installation_type_display()
        self.assertEqual(result, "pip editable")

    @mock.patch("subprocess.run")
    def test_pipx_detection_with_cli_installed(self, mock_run):
        """Test pipx detection when CLI is installed."""
        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"venvs": {"caylent-devcontainer-cli": {}}})
        mock_run.return_value = mock_result

        result = _is_installed_with_pipx()
        self.assertTrue(result)

    @mock.patch("subprocess.run")
    def test_pipx_detection_without_cli_installed(self, mock_run):
        """Test pipx detection when CLI is not installed."""
        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"venvs": {}})
        mock_run.return_value = mock_result

        result = _is_installed_with_pipx()
        self.assertFalse(result)

    @mock.patch("subprocess.run")
    def test_pipx_detection_command_not_found(self, mock_run):
        """Test pipx detection when pipx is not installed."""
        mock_run.side_effect = FileNotFoundError()

        result = _is_installed_with_pipx()
        self.assertFalse(result)

    def test_editable_installation_detection(self):
        """Test editable installation detection."""
        result = _is_editable_installation()
        self.assertIsInstance(result, bool)
