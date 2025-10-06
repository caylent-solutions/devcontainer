"""Unit tests for version checking functionality."""

import json
import os
import subprocess
import unittest.mock as mock
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import (
    _acquire_lock,
    _debug_log,
    _get_installation_type_display,
    _get_latest_version,
    _install_pipx,
    _is_editable_installation,
    _is_installed_with_pipx,
    _is_interactive_shell,
    _is_pipx_available,
    _release_lock,
    _show_manual_upgrade_instructions,
    _show_pip_instructions,
    _show_pipx_instructions,
    _show_reinstall_instructions,
    _show_update_prompt,
    _upgrade_to_pipx_from_pypi,
    _upgrade_with_pipx,
    _version_is_newer,
    check_for_updates,
)


class TestVersionUtils(TestCase):
    """Test version utility functions."""

    def test_version_is_newer(self):
        """Test version comparison logic."""
        self.assertTrue(_version_is_newer("1.11.0", "1.10.0"))
        self.assertTrue(_version_is_newer("2.0.0", "1.11.0"))
        self.assertFalse(_version_is_newer("1.10.0", "1.11.0"))
        self.assertFalse(_version_is_newer("1.10.0", "1.10.0"))

    @mock.patch("subprocess.run")
    def test_is_installed_with_pipx_true(self, mock_run):
        """Test pipx installation detection when installed."""
        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"venvs": {"caylent-devcontainer-cli": {}}})
        mock_run.return_value = mock_result

        self.assertTrue(_is_installed_with_pipx())

    @mock.patch("subprocess.run")
    def test_is_installed_with_pipx_false(self, mock_run):
        """Test pipx installation detection when not installed."""
        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"venvs": {}})
        mock_run.return_value = mock_result

        self.assertFalse(_is_installed_with_pipx())

    @mock.patch("subprocess.run")
    def test_is_installed_with_pipx_error(self, mock_run):
        """Test pipx installation detection with error."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(_is_installed_with_pipx())

    @mock.patch.dict(os.environ, {"CI": "true"})
    def test_is_interactive_shell_ci(self):
        """Test interactive shell detection in CI."""
        self.assertFalse(_is_interactive_shell())

    @mock.patch("sys.stdin.isatty")
    @mock.patch("sys.stdout.isatty")
    def test_is_interactive_shell_no_tty(self, mock_stdout_tty, mock_stdin_tty):
        """Test interactive shell detection without TTY."""
        mock_stdin_tty.return_value = False
        mock_stdout_tty.return_value = True
        self.assertFalse(_is_interactive_shell())

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_success(self, mock_urlopen):
        """Test successful version fetch from PyPI."""
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"info": {"version": "1.12.0"}}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        version = _get_latest_version()
        self.assertEqual(version, "1.12.0")

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_network_error(self, mock_urlopen):
        """Test version fetch with network error."""
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("Network error")

        version = _get_latest_version()
        self.assertIsNone(version)

    @mock.patch.dict(os.environ, {"CDEVCONTAINER_SKIP_UPDATE": "1"})
    def test_check_for_updates_skip_env(self):
        """Test update check with skip environment variable."""
        result = check_for_updates()
        self.assertTrue(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell")
    def test_check_for_updates_non_interactive(self, mock_interactive):
        """Test update check in non-interactive environment."""
        mock_interactive.return_value = False
        result = check_for_updates()
        self.assertTrue(result)


class TestEdgeCase(TestCase):
    """Test edge cases and error handling."""

    def test_is_editable_installation(self):
        """Test editable installation detection."""
        # This will depend on how the test is run, but should not crash
        result = _is_editable_installation()
        self.assertIsInstance(result, bool)

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_oversized_response(self, mock_urlopen):
        """Test version fetch with oversized response."""
        mock_response = mock.MagicMock()
        mock_response.status = 200
        # Create response larger than 200KB
        large_data = "x" * (201 * 1024)
        mock_response.read.return_value = large_data.encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        version = _get_latest_version()
        self.assertIsNone(version)

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_invalid_json(self, mock_urlopen):
        """Test version fetch with invalid JSON."""
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"invalid json"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        version = _get_latest_version()
        self.assertIsNone(version)

    def test_version_is_newer_invalid_versions(self):
        """Test version comparison with invalid versions."""
        # Should handle gracefully and return False
        result = _version_is_newer("invalid", "1.0.0")
        self.assertFalse(result)

        result = _version_is_newer("1.0.0", "invalid")
        self.assertFalse(result)

    @mock.patch.dict(os.environ, {"CDEVCONTAINER_DEBUG_UPDATE": "1"})
    @mock.patch("sys.stderr")
    def test_debug_log(self, mock_stderr):
        """Test debug logging."""
        _debug_log("test message")
        mock_stderr.write.assert_called()

    @mock.patch.dict(os.environ, {"-": "sh"})
    def test_is_interactive_shell_non_interactive(self):
        """Test non-interactive shell detection."""
        self.assertFalse(_is_interactive_shell())

    @mock.patch("sys.argv", ["pytest"])
    @mock.patch("sys.stdin.isatty", return_value=False)
    def test_is_interactive_shell_pytest_no_tty(self, mock_tty):
        """Test pytest without TTY."""
        self.assertFalse(_is_interactive_shell())

    @mock.patch("tempfile.mkdtemp")
    @mock.patch("pathlib.Path.mkdir")
    @mock.patch("pathlib.Path.exists", return_value=False)
    @mock.patch("os.open")
    @mock.patch("os.fdopen")
    def test_acquire_lock_success(self, mock_fdopen, mock_open, mock_exists, mock_mkdir, mock_mkdtemp):
        """Test successful lock acquisition."""
        mock_open.return_value = 3
        mock_file = mock.MagicMock()
        mock_fdopen.return_value.__enter__.return_value = mock_file

        result = _acquire_lock()
        self.assertTrue(result)

    @mock.patch("time.time", return_value=1000)
    @mock.patch("builtins.open")
    @mock.patch("pathlib.Path.exists", return_value=True)
    def test_acquire_lock_stale_lock(self, mock_exists, mock_open, mock_time):
        """Test stale lock handling."""
        mock_file = mock.MagicMock()
        mock_file.__enter__.return_value.read.return_value = '{"created": 500, "pid": 123}'
        mock_open.return_value = mock_file

        with mock.patch("json.load", return_value={"created": 500, "pid": 123}):
            with mock.patch("os.open", return_value=3):
                with mock.patch("os.fdopen"):
                    result = _acquire_lock()
                    self.assertTrue(result)

    @mock.patch("pathlib.Path.exists", return_value=True)
    @mock.patch("pathlib.Path.unlink")
    def test_release_lock(self, mock_unlink, mock_exists):
        """Test lock release."""
        _release_lock()
        mock_unlink.assert_called_once()

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_http_error(self, mock_urlopen):
        """Test version fetch with HTTP error."""
        mock_response = mock.MagicMock()
        mock_response.status = 404
        mock_urlopen.return_value.__enter__.return_value = mock_response

        version = _get_latest_version()
        self.assertIsNone(version)

    @mock.patch("subprocess.run")
    def test_is_pipx_available_true(self, mock_run):
        """Test pipx availability check."""
        mock_run.return_value = mock.MagicMock(returncode=0)
        self.assertTrue(_is_pipx_available())

    @mock.patch("subprocess.run")
    def test_is_pipx_available_false(self, mock_run):
        """Test pipx unavailable."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(_is_pipx_available())

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation", return_value=False)
    def test_get_installation_type_display_pipx(self, mock_editable, mock_pipx):
        """Test installation type display for pipx."""
        result = _get_installation_type_display()
        self.assertEqual(result, "pipx")

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", return_value=False)
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation", return_value=True)
    def test_get_installation_type_display_pip_editable(self, mock_editable, mock_pipx):
        """Test installation type display for pip editable."""
        result = _get_installation_type_display()
        self.assertEqual(result, "pip editable")

    @mock.patch("subprocess.run")
    def test_install_pipx_success(self, mock_run):
        """Test pipx installation success."""
        mock_run.return_value = mock.MagicMock(returncode=0)
        result = _install_pipx()
        self.assertTrue(result)

    @mock.patch("subprocess.run")
    def test_install_pipx_failure(self, mock_run):
        """Test pipx installation failure."""
        mock_run.return_value = mock.MagicMock(returncode=1, stderr="error")
        result = _install_pipx()
        self.assertFalse(result)

    @mock.patch("builtins.print")
    def test_show_pipx_instructions(self, mock_print):
        """Test pipx upgrade instructions."""
        _show_pipx_instructions()
        mock_print.assert_called()

    @mock.patch("builtins.print")
    def test_show_pip_instructions(self, mock_print):
        """Test pip upgrade instructions."""
        _show_pip_instructions()
        mock_print.assert_called()

    @mock.patch("builtins.print")
    def test_show_reinstall_instructions(self, mock_print):
        """Test reinstall instructions."""
        _show_reinstall_instructions()
        mock_print.assert_called()

    @mock.patch("builtins.print")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available", return_value=True)
    def test_show_manual_upgrade_instructions_pipx(self, mock_available, mock_print):
        """Test manual upgrade instructions for pipx."""
        _show_manual_upgrade_instructions("pipx")
        mock_print.assert_called()

    @mock.patch("caylent_devcontainer_cli.utils.version._get_pipx_command", return_value=["pipx"])
    @mock.patch("subprocess.run")
    def test_upgrade_with_pipx_success(self, mock_run, mock_get_pipx):
        """Test successful pipx upgrade."""
        mock_run.return_value = mock.MagicMock(returncode=0)
        from caylent_devcontainer_cli.utils.version import EXIT_UPGRADE_PERFORMED

        result = _upgrade_with_pipx()
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("caylent_devcontainer_cli.utils.version._get_pipx_command", return_value=["pipx"])
    @mock.patch("subprocess.run")
    def test_upgrade_with_pipx_failure(self, mock_run, mock_get_pipx):
        """Test failed pipx upgrade."""
        mock_run.return_value = mock.MagicMock(returncode=1, stderr="error")
        from caylent_devcontainer_cli.utils.version import EXIT_UPGRADE_FAILED

        result = _upgrade_with_pipx()
        self.assertEqual(result, EXIT_UPGRADE_FAILED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._get_pipx_command", return_value=["pipx"])
    @mock.patch("subprocess.run")
    def test_upgrade_to_pipx_from_pypi_success(self, mock_run, mock_get_pipx, mock_available):
        """Test successful upgrade to pipx from PyPI."""
        mock_run.return_value = mock.MagicMock(returncode=0)
        from caylent_devcontainer_cli.utils.version import EXIT_UPGRADE_PERFORMED

        result = _upgrade_to_pipx_from_pypi("pip")
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("builtins.input", return_value="3")
    @mock.patch("builtins.print")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_installation_type_display", return_value="pipx")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation", return_value=False)
    def test_show_update_prompt_continue(self, mock_editable, mock_pipx, mock_display, mock_print, mock_input):
        """Test update prompt with continue option."""
        from caylent_devcontainer_cli.utils.version import EXIT_OK

        result = _show_update_prompt("1.0.0", "1.1.0")
        self.assertEqual(result, EXIT_OK)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._acquire_lock", return_value=False)
    def test_check_for_updates_lock_failed(self, mock_lock, mock_interactive):
        """Test update check when lock acquisition fails."""
        result = check_for_updates()
        self.assertTrue(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._acquire_lock", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version", return_value=None)
    @mock.patch("caylent_devcontainer_cli.utils.version._release_lock")
    def test_check_for_updates_no_version(self, mock_release, mock_version, mock_lock, mock_interactive):
        """Test update check when version fetch fails."""
        result = check_for_updates()
        self.assertTrue(result)
        mock_release.assert_called_once()

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._acquire_lock", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version", return_value="1.0.0")
    @mock.patch("caylent_devcontainer_cli.utils.version._version_is_newer", return_value=False)
    @mock.patch("caylent_devcontainer_cli.utils.version._release_lock")
    @mock.patch("builtins.print")
    def test_check_for_updates_up_to_date(
        self, mock_print, mock_release, mock_newer, mock_version, mock_lock, mock_interactive
    ):
        """Test update check when already up to date."""
        result = check_for_updates()
        self.assertTrue(result)
        mock_print.assert_called()
        mock_release.assert_called_once()

    @mock.patch("os.open")
    @mock.patch("pathlib.Path.exists", return_value=False)
    def test_acquire_lock_file_exists_error(self, mock_exists, mock_open):
        """Test lock acquisition when file already exists."""
        mock_open.side_effect = FileExistsError()
        result = _acquire_lock()
        self.assertFalse(result)

    @mock.patch("pathlib.Path.mkdir")
    def test_acquire_lock_permission_error(self, mock_mkdir):
        """Test lock acquisition with permission error."""
        mock_mkdir.side_effect = PermissionError()
        result = _acquire_lock()
        self.assertTrue(result)  # Should proceed without lock

    @mock.patch("pathlib.Path.unlink")
    def test_release_lock_error(self, mock_unlink):
        """Test lock release with error."""
        mock_unlink.side_effect = OSError()
        _release_lock()  # Should not raise

    @mock.patch("socket.setdefaulttimeout")
    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_timeout(self, mock_urlopen, mock_timeout):
        """Test version fetch with timeout."""
        import socket

        mock_urlopen.side_effect = socket.timeout()
        version = _get_latest_version()
        self.assertIsNone(version)

    @mock.patch("subprocess.run")
    def test_is_installed_with_pipx_timeout(self, mock_run):
        """Test pipx detection with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("pipx", 10)
        result = _is_installed_with_pipx()
        self.assertFalse(result)

    @mock.patch("subprocess.run")
    def test_is_installed_with_pipx_json_error(self, mock_run):
        """Test pipx detection with JSON decode error."""
        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result
        result = _is_installed_with_pipx()
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
        mock_run.side_effect = Exception("error")
        result = _install_pipx()
        self.assertFalse(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._get_pipx_command", return_value=["pipx"])
    @mock.patch("subprocess.run")
    def test_upgrade_with_pipx_timeout(self, mock_run, mock_get_pipx):
        """Test pipx upgrade with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("pipx", 60)
        from caylent_devcontainer_cli.utils.version import EXIT_UPGRADE_FAILED

        result = _upgrade_with_pipx()
        self.assertEqual(result, EXIT_UPGRADE_FAILED)

    @mock.patch("caylent_devcontainer_cli.utils.version._get_pipx_command", return_value=["pipx"])
    @mock.patch("subprocess.run")
    def test_upgrade_with_pipx_already_latest(self, mock_run, mock_get_pipx):
        """Test pipx upgrade when already at latest version."""
        # First call (upgrade) returns "already at latest"
        # Second call (uninstall) succeeds
        # Third call (install) succeeds
        mock_run.side_effect = [
            mock.MagicMock(returncode=0, stdout="is already at latest version"),
            mock.MagicMock(returncode=0),  # uninstall
            mock.MagicMock(returncode=0),  # install
        ]
        from caylent_devcontainer_cli.utils.version import EXIT_UPGRADE_PERFORMED

        result = _upgrade_with_pipx()
        self.assertEqual(result, EXIT_UPGRADE_PERFORMED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available", return_value=False)
    @mock.patch("caylent_devcontainer_cli.utils.version._install_pipx", return_value=False)
    def test_upgrade_to_pipx_no_pipx(self, mock_install, mock_available):
        """Test upgrade to pipx when pipx unavailable."""
        from caylent_devcontainer_cli.utils.version import EXIT_UPGRADE_FAILED

        result = _upgrade_to_pipx_from_pypi("pip")
        self.assertEqual(result, EXIT_UPGRADE_FAILED)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._get_pipx_command", return_value=["pipx"])
    @mock.patch("subprocess.run")
    def test_upgrade_to_pipx_exception(self, mock_run, mock_get_pipx, mock_available):
        """Test upgrade to pipx with exception."""
        mock_run.side_effect = Exception("error")
        from caylent_devcontainer_cli.utils.version import EXIT_UPGRADE_FAILED

        result = _upgrade_to_pipx_from_pypi("pip")
        self.assertEqual(result, EXIT_UPGRADE_FAILED)

    @mock.patch("builtins.input", return_value="1")
    @mock.patch("builtins.print")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_installation_type_display", return_value="pip editable")
    @mock.patch("caylent_devcontainer_cli.utils.version._show_manual_upgrade_instructions")
    def test_show_update_prompt_editable_exit(
        self, mock_instructions, mock_display, mock_print, mock_input
    ):
        """Test update prompt for editable installation with exit option."""
        from caylent_devcontainer_cli.utils.version import EXIT_UPGRADE_REQUESTED_ABORT

        result = _show_update_prompt("1.0.0", "1.1.0")
        self.assertEqual(result, EXIT_UPGRADE_REQUESTED_ABORT)

    @mock.patch("builtins.input", return_value="2")
    @mock.patch("builtins.print")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_installation_type_display", return_value="pip")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", return_value=False)
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation", return_value=False)
    def test_show_update_prompt_pip_continue(self, mock_editable, mock_pipx, mock_display, mock_print, mock_input):
        """Test update prompt for pip installation with continue option."""
        from caylent_devcontainer_cli.utils.version import EXIT_OK

        result = _show_update_prompt("1.0.0", "1.1.0")
        self.assertEqual(result, EXIT_OK)

    @mock.patch("builtins.print")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available", return_value=False)
    def test_show_manual_upgrade_instructions_no_pipx(self, mock_available, mock_print):
        """Test manual upgrade instructions when pipx not available."""
        _show_manual_upgrade_instructions("pip")
        mock_print.assert_called()

    @mock.patch("builtins.print")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_pipx_available", return_value=True)
    def test_show_manual_upgrade_instructions_pip_editable(self, mock_available, mock_print):
        """Test manual upgrade instructions for pip editable."""
        _show_manual_upgrade_instructions("pip editable")
        mock_print.assert_called()

    @mock.patch("time.time", return_value=100)
    @mock.patch("builtins.open")
    @mock.patch("pathlib.Path.exists", return_value=True)
    def test_acquire_lock_active_lock(self, mock_exists, mock_open, mock_time):
        """Test lock acquisition with active lock."""
        mock_file = mock.MagicMock()
        mock_open.return_value = mock_file

        with mock.patch("json.load", return_value={"created": 50, "pid": 123}):
            with mock.patch("builtins.print"):
                result = _acquire_lock()
                self.assertFalse(result)

    @mock.patch("pathlib.Path.exists", return_value=True)
    @mock.patch("builtins.open")
    def test_acquire_lock_json_error(self, mock_open, mock_exists):
        """Test lock acquisition with JSON decode error."""
        mock_file = mock.MagicMock()
        mock_open.return_value = mock_file

        with mock.patch("json.load", side_effect=json.JSONDecodeError("error", "doc", 0)):
            with mock.patch("os.open", return_value=3):
                with mock.patch("os.fdopen"):
                    result = _acquire_lock()
                    self.assertTrue(result)

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_key_error(self, mock_urlopen):
        """Test version fetch with missing key."""
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"info": {}}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        version = _get_latest_version()
        self.assertIsNone(version)

    def test_is_editable_installation_site_packages(self):
        """Test editable installation detection with site-packages."""
        with mock.patch(
            "caylent_devcontainer_cli.__file__",
            "/usr/lib/python3.12/site-packages/caylent_devcontainer_cli/__init__.py",
        ):
            result = _is_editable_installation()
            self.assertFalse(result)

    def test_is_editable_installation_pipx_with_egg_link(self):
        """Test editable installation detection doesn't crash."""
        # This function has complex import logic that's hard to mock
        # Just ensure it doesn't crash and returns a boolean
        result = _is_editable_installation()
        self.assertIsInstance(result, bool)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", return_value=True)
    @mock.patch("os.walk")
    def test_is_editable_installation_pipx_no_egg_link(self, mock_walk, mock_pipx):
        """Test editable installation detection with pipx but no egg-link."""
        mock_walk.return_value = [("/path", [], ["other.file"])]
        result = _is_editable_installation()
        self.assertFalse(result)
