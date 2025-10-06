"""Unit tests for automatic upgrade functionality."""

import unittest.mock as mock
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import (
    EXIT_UPGRADE_FAILED,
    EXIT_UPGRADE_PERFORMED,
    _install_pipx,
    _is_pipx_available,
    _upgrade_to_pipx_from_pypi,
)


class TestAutomaticUpgrade(TestCase):
    """Test automatic upgrade functionality."""

    @mock.patch("subprocess.run")
    def test_pipx_available_true(self, mock_run):
        """Test pipx availability detection when pipx is available."""
        mock_run.return_value = mock.MagicMock(returncode=0)

        result = _is_pipx_available()
        self.assertTrue(result)

    @mock.patch("subprocess.run")
    def test_pipx_available_false(self, mock_run):
        """Test pipx availability detection when pipx is not available."""
        mock_run.side_effect = FileNotFoundError()

        result = _is_pipx_available()
        self.assertFalse(result)

    @mock.patch("subprocess.run")
    def test_install_pipx_success(self, mock_run):
        """Test successful pipx installation."""
        mock_run.return_value = mock.MagicMock(returncode=0)

        result = _install_pipx()
        self.assertTrue(result)

    @mock.patch("subprocess.run")
    def test_install_pipx_failure(self, mock_run):
        """Test failed pipx installation."""
        mock_run.return_value = mock.MagicMock(returncode=1, stderr="error")

        result = _install_pipx()
        self.assertFalse(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("subprocess.run")
    def test_upgrade_pipx_regular_success(self, mock_run, mock_pipx_available):
        """Test successful upgrade for pipx regular installation."""
        mock_pipx_available.return_value = True
        mock_run.return_value = mock.MagicMock(returncode=0)

        result = _upgrade_to_pipx_from_pypi("pipx")
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("subprocess.run")
    def test_upgrade_pipx_editable_success(self, mock_run, mock_pipx_available):
        """Test successful upgrade for pipx editable installation."""
        mock_pipx_available.return_value = True
        mock_run.return_value = mock.MagicMock(returncode=0)

        result = _upgrade_to_pipx_from_pypi("pipx editable")
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("subprocess.run")
    def test_upgrade_pip_regular_success(self, mock_run, mock_pipx_available):
        """Test successful upgrade for pip regular installation."""
        mock_pipx_available.return_value = True
        mock_run.return_value = mock.MagicMock(returncode=0)

        result = _upgrade_to_pipx_from_pypi("pip")
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("subprocess.run")
    def test_upgrade_pip_editable_success(self, mock_run, mock_pipx_available):
        """Test successful upgrade for pip editable installation."""
        mock_pipx_available.return_value = True
        mock_run.return_value = mock.MagicMock(returncode=0)

        result = _upgrade_to_pipx_from_pypi("pip editable")
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("caylent_devcontainer_cli.utils.version._install_pipx")
    @mock.patch("subprocess.run")
    def test_upgrade_with_pipx_installation(self, mock_run, mock_install_pipx, mock_pipx_available):
        """Test upgrade when pipx needs to be installed first."""
        mock_pipx_available.return_value = False
        mock_install_pipx.return_value = True
        mock_run.return_value = mock.MagicMock(returncode=0)

        result = _upgrade_to_pipx_from_pypi("pip")
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)
        mock_install_pipx.assert_called_once()

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("caylent_devcontainer_cli.utils.version._install_pipx")
    def test_upgrade_pipx_install_failure(self, mock_install_pipx, mock_pipx_available):
        """Test upgrade failure when pipx installation fails."""
        mock_pipx_available.return_value = False
        mock_install_pipx.return_value = False

        result = _upgrade_to_pipx_from_pypi("pip")
        self.assertEqual(result, EXIT_UPGRADE_FAILED)
