"""Comprehensive tests to reach 90% coverage for version.py."""

import json
import subprocess
import unittest.mock as mock
from io import StringIO
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import (
    EXIT_OK,
    EXIT_UPGRADE_FAILED,
    EXIT_UPGRADE_PERFORMED,
    EXIT_UPGRADE_REQUESTED_ABORT,
    _acquire_lock,
    _show_manual_upgrade_instructions,
    _show_update_prompt,
    _upgrade_with_pipx,
    check_for_updates,
)


class TestVersionComprehensive(TestCase):
    """Comprehensive tests to reach 90% coverage."""

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._upgrade_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_show_update_prompt_pipx_option1_success(self, mock_editable, mock_pipx, mock_upgrade, mock_input):
        """Test pipx regular installation Option 1 success."""
        mock_pipx.return_value = True
        mock_editable.return_value = False
        mock_input.return_value = "1"
        mock_upgrade.return_value = EXIT_UPGRADE_PERFORMED

        result = _show_update_prompt("1.10.0", "1.11.0")
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._show_pipx_instructions")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_show_update_prompt_pipx_option2(self, mock_editable, mock_pipx, mock_show_pipx, mock_input):
        """Test pipx regular installation Option 2."""
        mock_pipx.return_value = True
        mock_editable.return_value = False
        mock_input.return_value = "2"

        result = _show_update_prompt("1.10.0", "1.11.0")
        self.assertEqual(result, EXIT_UPGRADE_REQUESTED_ABORT)
        mock_show_pipx.assert_called_once()

    @mock.patch("builtins.input")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation")
    def test_show_update_prompt_pipx_option3(self, mock_editable, mock_pipx, mock_input):
        """Test pipx regular installation Option 3."""
        mock_pipx.return_value = True
        mock_editable.return_value = False
        mock_input.return_value = "3"

        result = _show_update_prompt("1.10.0", "1.11.0")
        self.assertEqual(result, EXIT_OK)

    @mock.patch("subprocess.run")
    def test_upgrade_with_pipx_success_no_already_latest(self, mock_run):
        """Test pipx upgrade success without 'already at latest' message."""
        mock_run.return_value = mock.MagicMock(returncode=0, stdout="upgraded successfully", stderr="")

        result = _upgrade_with_pipx()
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("subprocess.run")
    def test_upgrade_with_pipx_already_latest_reinstall_success(self, mock_run):
        """Test pipx upgrade with 'already at latest' triggering reinstall."""
        # First call returns "already at latest", subsequent calls succeed
        mock_run.side_effect = [
            mock.MagicMock(returncode=0, stdout="is already at latest version", stderr=""),
            mock.MagicMock(returncode=0, stdout="", stderr=""),  # uninstall
            mock.MagicMock(returncode=0, stdout="", stderr=""),  # install
        ]

        result = _upgrade_with_pipx()
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)
        self.assertEqual(mock_run.call_count, 3)

    @mock.patch("subprocess.run")
    def test_upgrade_with_pipx_already_latest_reinstall_failure(self, mock_run):
        """Test pipx upgrade with 'already at latest' but reinstall fails."""
        mock_run.side_effect = [
            mock.MagicMock(returncode=0, stdout="is already at latest version", stderr=""),
            mock.MagicMock(returncode=0, stdout="", stderr=""),  # uninstall
            mock.MagicMock(returncode=1, stdout="", stderr="install failed"),  # install fails
        ]

        result = _upgrade_with_pipx()
        self.assertEqual(result, EXIT_UPGRADE_FAILED)

    @mock.patch("subprocess.run")
    def test_upgrade_with_pipx_timeout_expired(self, mock_run):
        """Test pipx upgrade with timeout expired."""
        mock_run.side_effect = subprocess.TimeoutExpired("pipx", 60)

        result = _upgrade_with_pipx()
        self.assertEqual(result, EXIT_UPGRADE_FAILED)

    @mock.patch("subprocess.run")
    def test_upgrade_with_pipx_file_not_found(self, mock_run):
        """Test pipx upgrade with FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError()

        result = _upgrade_with_pipx()
        self.assertEqual(result, EXIT_UPGRADE_FAILED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_show_manual_upgrade_instructions_no_pipx(self, mock_stdout, mock_pipx_available):
        """Test manual instructions when pipx is not available."""
        mock_pipx_available.return_value = False

        _show_manual_upgrade_instructions("pip")

        output = mock_stdout.getvalue()
        self.assertIn("First, install pipx:", output)
        self.assertIn("python -m pip install pipx", output)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell")
    @mock.patch("caylent_devcontainer_cli.utils.version._acquire_lock")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version")
    @mock.patch("caylent_devcontainer_cli.utils.version._version_is_newer")
    @mock.patch("caylent_devcontainer_cli.utils.version._show_update_prompt")
    @mock.patch("sys.exit")
    def test_check_for_updates_exit_upgrade_performed(
        self, mock_exit, mock_show_prompt, mock_version_newer, mock_get_version, mock_acquire_lock, mock_interactive
    ):
        """Test update check with upgrade performed exit."""
        mock_interactive.return_value = True
        mock_acquire_lock.return_value = True
        mock_get_version.return_value = "1.11.0"
        mock_version_newer.return_value = True
        mock_show_prompt.return_value = EXIT_UPGRADE_PERFORMED

        with mock.patch("caylent_devcontainer_cli.utils.version._release_lock"):
            check_for_updates()
            mock_exit.assert_called_once_with(EXIT_UPGRADE_PERFORMED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell")
    @mock.patch("caylent_devcontainer_cli.utils.version._acquire_lock")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version")
    @mock.patch("caylent_devcontainer_cli.utils.version._version_is_newer")
    @mock.patch("caylent_devcontainer_cli.utils.version._show_update_prompt")
    @mock.patch("sys.exit")
    def test_check_for_updates_exit_upgrade_failed(
        self, mock_exit, mock_show_prompt, mock_version_newer, mock_get_version, mock_acquire_lock, mock_interactive
    ):
        """Test update check with upgrade failed exit."""
        mock_interactive.return_value = True
        mock_acquire_lock.return_value = True
        mock_get_version.return_value = "1.11.0"
        mock_version_newer.return_value = True
        mock_show_prompt.return_value = EXIT_UPGRADE_FAILED

        with mock.patch("caylent_devcontainer_cli.utils.version._release_lock"):
            check_for_updates()
            mock_exit.assert_called_once_with(EXIT_UPGRADE_FAILED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell")
    @mock.patch("caylent_devcontainer_cli.utils.version._acquire_lock")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version")
    @mock.patch("caylent_devcontainer_cli.utils.version._version_is_newer")
    @mock.patch("caylent_devcontainer_cli.utils.version._show_update_prompt")
    def test_check_for_updates_unknown_exit_code(
        self, mock_show_prompt, mock_version_newer, mock_get_version, mock_acquire_lock, mock_interactive
    ):
        """Test update check with unknown exit code."""
        mock_interactive.return_value = True
        mock_acquire_lock.return_value = True
        mock_get_version.return_value = "1.11.0"
        mock_version_newer.return_value = True
        mock_show_prompt.return_value = 999  # Unknown exit code

        with mock.patch("caylent_devcontainer_cli.utils.version._release_lock"):
            result = check_for_updates()
            self.assertTrue(result)

    @mock.patch("json.load")
    @mock.patch("builtins.open")
    @mock.patch("caylent_devcontainer_cli.utils.version.LOCK_FILE")
    def test_acquire_lock_json_decode_error(self, mock_lock_file, mock_open, mock_json_load):
        """Test lock acquisition with JSON decode error."""
        mock_lock_file.exists.return_value = True
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        with mock.patch("os.open") as mock_os_open:
            with mock.patch("os.fdopen") as mock_fdopen:
                mock_os_open.return_value = 3
                mock_fdopen.return_value.__enter__ = mock.MagicMock()
                mock_fdopen.return_value.__exit__ = mock.MagicMock()

                result = _acquire_lock()
                self.assertTrue(result)

    @mock.patch("json.load")
    @mock.patch("builtins.open")
    @mock.patch("caylent_devcontainer_cli.utils.version.LOCK_FILE")
    def test_acquire_lock_key_error(self, mock_lock_file, mock_open, mock_json_load):
        """Test lock acquisition with KeyError."""
        mock_lock_file.exists.return_value = True
        mock_json_load.side_effect = KeyError("missing key")

        with mock.patch("os.open") as mock_os_open:
            with mock.patch("os.fdopen") as mock_fdopen:
                mock_os_open.return_value = 3
                mock_fdopen.return_value.__enter__ = mock.MagicMock()
                mock_fdopen.return_value.__exit__ = mock.MagicMock()

                result = _acquire_lock()
                self.assertTrue(result)
