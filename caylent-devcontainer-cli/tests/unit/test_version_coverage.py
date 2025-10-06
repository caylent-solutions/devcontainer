"""Additional unit tests to improve version.py coverage."""

import json
import os
import subprocess
import unittest.mock as mock
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import (
    EXIT_UPGRADE_FAILED,
    EXIT_UPGRADE_PERFORMED,
    _acquire_lock,
    _debug_log,
    _get_latest_version,
    _install_pipx,
    _is_installed_with_pipx,
    _is_interactive_shell,
    _is_pipx_available,
    _release_lock,
    _upgrade_to_pipx_from_pypi,
    _version_is_newer,
    check_for_updates,
)


class TestVersionCoverage(TestCase):
    """Additional tests to improve version.py coverage."""

    @mock.patch.dict(os.environ, {"CDEVCONTAINER_DEBUG_UPDATE": "0"})
    @mock.patch("sys.stderr")
    def test_debug_log_disabled(self, mock_stderr):
        """Test debug logging when disabled."""
        _debug_log("test message")
        mock_stderr.write.assert_not_called()

    @mock.patch.dict(os.environ, {"CI": "false"})
    @mock.patch("sys.stdin.isatty")
    @mock.patch("sys.stdout.isatty")
    def test_is_interactive_shell_tty_false(self, mock_stdout_tty, mock_stdin_tty):
        """Test interactive shell detection with TTY false."""
        mock_stdin_tty.return_value = False
        mock_stdout_tty.return_value = True
        result = _is_interactive_shell()
        self.assertFalse(result)

    @mock.patch.dict(os.environ, {"-": "hmBH", "TERM": ""})  # No 'i' flag, no TERM
    @mock.patch("sys.stdin.isatty")
    @mock.patch("sys.stdout.isatty")
    def test_is_interactive_shell_no_i_flag(self, mock_stdout_tty, mock_stdin_tty):
        """Test interactive shell detection without 'i' flag."""
        mock_stdin_tty.return_value = False
        mock_stdout_tty.return_value = True
        result = _is_interactive_shell()
        self.assertFalse(result)

    @mock.patch("sys.argv", ["pytest"])
    @mock.patch("sys.stdin.isatty")
    @mock.patch("sys.stdout.isatty")
    def test_is_interactive_shell_pytest_no_tty(self, mock_stdout_tty, mock_stdin_tty):
        """Test interactive shell detection for pytest without TTY."""
        mock_stdin_tty.return_value = False
        mock_stdout_tty.return_value = True
        result = _is_interactive_shell()
        self.assertFalse(result)

    def test_acquire_lock_permission_error(self):
        """Test lock acquisition with permission error."""
        with mock.patch("caylent_devcontainer_cli.utils.version.CACHE_DIR") as mock_cache_dir:
            mock_cache_dir.mkdir.side_effect = PermissionError()
            result = _acquire_lock()
            self.assertTrue(result)

    def test_release_lock_os_error(self):
        """Test lock release with OS error."""
        with mock.patch("caylent_devcontainer_cli.utils.version.LOCK_FILE") as mock_lock_file:
            mock_lock_file.exists.return_value = True
            mock_lock_file.unlink.side_effect = OSError()
            _release_lock()  # Should not raise exception

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_http_error(self, mock_urlopen):
        """Test version fetch with HTTP error."""
        mock_response = mock.MagicMock()
        mock_response.status = 404
        mock_urlopen.return_value.__enter__.return_value = mock_response

        version = _get_latest_version()
        self.assertIsNone(version)

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_json_decode_error(self, mock_urlopen):
        """Test version fetch with JSON decode error."""
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"invalid json"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        version = _get_latest_version()
        self.assertIsNone(version)

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_key_error(self, mock_urlopen):
        """Test version fetch with missing key."""
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"missing": "version"}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        version = _get_latest_version()
        self.assertIsNone(version)

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_socket_timeout_finally(self, mock_urlopen):
        """Test version fetch socket timeout cleanup."""
        import socket

        mock_urlopen.side_effect = socket.timeout()

        with mock.patch("socket.setdefaulttimeout") as mock_set_timeout:
            version = _get_latest_version()
            self.assertIsNone(version)
            # Verify finally block was called
            self.assertTrue(mock_set_timeout.called)

    def test_version_is_newer_exception(self):
        """Test version comparison with exception."""
        with mock.patch("packaging.version.parse") as mock_parse:
            mock_parse.side_effect = Exception("Parse error")
            result = _version_is_newer("1.11.0", "1.10.0")
            self.assertFalse(result)

    @mock.patch("subprocess.run")
    def test_is_pipx_available_timeout(self, mock_run):
        """Test pipx availability with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("pipx", 5)
        result = _is_pipx_available()
        self.assertFalse(result)

    @mock.patch("subprocess.run")
    def test_install_pipx_exception(self, mock_run):
        """Test pipx installation with exception."""
        mock_run.side_effect = Exception("Install error")
        result = _install_pipx()
        self.assertFalse(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("caylent_devcontainer_cli.utils.version._install_pipx")
    def test_upgrade_to_pipx_pipx_install_failed(self, mock_install_pipx, mock_pipx_available):
        """Test upgrade when pipx installation fails."""
        mock_pipx_available.return_value = False
        mock_install_pipx.return_value = False

        result = _upgrade_to_pipx_from_pypi("pip")
        self.assertEqual(result, EXIT_UPGRADE_FAILED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_pipx_command")
    @mock.patch("subprocess.run")
    def test_upgrade_to_pipx_exception(self, mock_run, mock_get_pipx, mock_pipx_available):
        """Test upgrade with exception."""
        mock_pipx_available.return_value = True
        mock_get_pipx.return_value = ["pipx"]
        mock_run.side_effect = Exception("Upgrade error")

        result = _upgrade_to_pipx_from_pypi("pipx")
        self.assertEqual(result, EXIT_UPGRADE_FAILED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell")
    @mock.patch("caylent_devcontainer_cli.utils.version._acquire_lock")
    def test_check_for_updates_no_lock(self, mock_acquire_lock, mock_interactive):
        """Test update check when lock acquisition fails."""
        mock_interactive.return_value = True
        mock_acquire_lock.return_value = False

        result = check_for_updates()
        self.assertTrue(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell")
    @mock.patch("caylent_devcontainer_cli.utils.version._acquire_lock")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version")
    def test_check_for_updates_no_version(self, mock_get_version, mock_acquire_lock, mock_interactive):
        """Test update check when version fetch fails."""
        mock_interactive.return_value = True
        mock_acquire_lock.return_value = True
        mock_get_version.return_value = None

        with mock.patch("caylent_devcontainer_cli.utils.version._release_lock") as mock_release:
            result = check_for_updates()
            self.assertTrue(result)
            mock_release.assert_called_once()

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell")
    @mock.patch("caylent_devcontainer_cli.utils.version._acquire_lock")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version")
    @mock.patch("caylent_devcontainer_cli.utils.version._version_is_newer")
    def test_check_for_updates_no_newer_version(
        self, mock_version_newer, mock_get_version, mock_acquire_lock, mock_interactive
    ):
        """Test update check when no newer version available."""
        mock_interactive.return_value = True
        mock_acquire_lock.return_value = True
        mock_get_version.return_value = "1.10.0"
        mock_version_newer.return_value = False

        with mock.patch("caylent_devcontainer_cli.utils.version._release_lock") as mock_release:
            with mock.patch("builtins.print") as mock_print:
                result = check_for_updates()
                self.assertTrue(result)
                mock_print.assert_called()
                mock_release.assert_called_once()

    @mock.patch("subprocess.run")
    def test_is_installed_with_pipx_timeout_expired(self, mock_run):
        """Test pipx detection with timeout expired."""
        mock_run.side_effect = subprocess.TimeoutExpired("pipx", 10)
        result = _is_installed_with_pipx()
        self.assertFalse(result)

    @mock.patch("subprocess.run")
    def test_is_installed_with_pipx_called_process_error(self, mock_run):
        """Test pipx detection with called process error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "pipx")
        result = _is_installed_with_pipx()
        self.assertFalse(result)

    @mock.patch("subprocess.run")
    def test_is_installed_with_pipx_json_decode_error(self, mock_run):
        """Test pipx detection with JSON decode error."""
        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result

        result = _is_installed_with_pipx()
        self.assertFalse(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_pipx_command")
    @mock.patch("subprocess.run")
    def test_upgrade_to_pipx_pip_editable_success(self, mock_run, mock_get_pipx, mock_pipx_available):
        """Test upgrade for pip editable installation."""
        mock_pipx_available.return_value = True
        mock_get_pipx.return_value = ["pipx"]
        mock_run.return_value = mock.MagicMock(returncode=0)

        result = _upgrade_to_pipx_from_pypi("pip editable")
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

        # Verify uninstall and install were called
        calls = mock_run.call_args_list
        self.assertTrue(any("pip" in str(call) and "uninstall" in str(call) for call in calls))
        self.assertTrue(any("pipx" in str(call) and "install" in str(call) for call in calls))

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_pipx_command")
    @mock.patch("subprocess.run")
    def test_upgrade_to_pipx_upgrade_failure(self, mock_run, mock_get_pipx, mock_pipx_available):
        """Test upgrade failure scenario."""
        mock_pipx_available.return_value = True
        mock_get_pipx.return_value = ["pipx"]
        mock_run.return_value = mock.MagicMock(returncode=1, stderr="upgrade failed")

        result = _upgrade_to_pipx_from_pypi("pipx")
        self.assertEqual(result, EXIT_UPGRADE_FAILED)
