"""Unit tests for version checking functionality."""

import json
import os
import unittest.mock as mock
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import (
    EXIT_OK,
    EXIT_UPGRADE_REQUESTED_ABORT,
    _debug_log,
    _get_installation_type_display,
    _get_latest_version,
    _is_editable_installation,
    _is_installed_with_pipx,
    _is_interactive_shell,
    _show_manual_upgrade_instructions,
    _show_update_prompt,
    _version_is_newer,
    check_for_updates,
)


class TestVersionUtils(TestCase):
    """Test version utility functions."""

    def test_version_is_newer(self):
        """Test version comparison logic."""
        self.assertTrue(_version_is_newer("1.11.0", "1.10.0"))
        self.assertFalse(_version_is_newer("1.10.0", "1.11.0"))

    @mock.patch("subprocess.run")
    def test_is_installed_with_pipx_true(self, mock_run):
        """Test pipx installation detection when installed."""
        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"venvs": {"caylent-devcontainer-cli": {}}})
        mock_run.return_value = mock_result
        self.assertTrue(_is_installed_with_pipx())

    @mock.patch.dict(os.environ, {"CI": "true"})
    def test_is_interactive_shell_ci(self):
        """Test interactive shell detection in CI."""
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

    @mock.patch.dict(os.environ, {"CDEVCONTAINER_SKIP_UPDATE": "1"})
    def test_check_for_updates_skip_env(self):
        """Test update check with skip environment variable."""
        result = check_for_updates()
        self.assertTrue(result)

    @mock.patch("builtins.input", return_value="2")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_installation_type_display", return_value="pipx")
    def test_show_update_prompt_continue(self, mock_display, mock_input):
        """Test update prompt with continue option."""
        result = _show_update_prompt("1.0.0", "1.1.0")
        self.assertEqual(result, EXIT_OK)

    @mock.patch("builtins.input", return_value="1")
    @mock.patch("caylent_devcontainer_cli.utils.version._show_manual_upgrade_instructions")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_installation_type_display", return_value="pipx")
    def test_show_update_prompt_exit(self, mock_display, mock_instructions, mock_input):
        """Test update prompt with exit option."""
        result = _show_update_prompt("1.0.0", "1.1.0")
        self.assertEqual(result, EXIT_UPGRADE_REQUESTED_ABORT)

    @mock.patch("builtins.print")
    def test_show_manual_upgrade_instructions(self, mock_print):
        """Test manual upgrade instructions."""
        _show_manual_upgrade_instructions("pipx")
        _show_manual_upgrade_instructions("pipx editable")
        _show_manual_upgrade_instructions("pip editable")
        _show_manual_upgrade_instructions("pip")
        mock_print.assert_called()

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

    @mock.patch("subprocess.run")
    def test_is_installed_with_pipx_python_m(self, mock_run):
        """Test pipx installation detection with python -m pipx."""
        # First call fails, second succeeds
        mock_run.side_effect = [
            FileNotFoundError(),
            mock.MagicMock(returncode=0, stdout=json.dumps({"venvs": {"caylent-devcontainer-cli": {}}})),
        ]
        self.assertTrue(_is_installed_with_pipx())

    def test_is_editable_installation(self):
        """Test editable installation detection."""
        result = _is_editable_installation()
        self.assertIsInstance(result, bool)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation", return_value=False)
    def test_get_installation_type_display_pipx(self, mock_editable, mock_pipx):
        """Test installation type display for pipx."""
        result = _get_installation_type_display()
        self.assertEqual(result, "pipx")

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation", return_value=True)
    def test_get_installation_type_display_pipx_editable(self, mock_editable, mock_pipx):
        """Test installation type display for pipx editable."""
        result = _get_installation_type_display()
        self.assertEqual(result, "pipx editable")

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", return_value=False)
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation", return_value=True)
    def test_get_installation_type_display_pip_editable(self, mock_editable, mock_pipx):
        """Test installation type display for pip editable."""
        result = _get_installation_type_display()
        self.assertEqual(result, "pip editable")

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", return_value=False)
    @mock.patch("caylent_devcontainer_cli.utils.version._is_editable_installation", return_value=False)
    def test_get_installation_type_display_pip(self, mock_editable, mock_pipx):
        """Test installation type display for pip."""
        result = _get_installation_type_display()
        self.assertEqual(result, "pip")

    @mock.patch("sys.stdin.isatty", return_value=False)
    @mock.patch("sys.stdout.isatty", return_value=True)
    def test_is_interactive_shell_no_stdin_tty(self, mock_stdout, mock_stdin):
        """Test interactive shell detection without stdin TTY."""
        self.assertFalse(_is_interactive_shell())

    @mock.patch("sys.stdin.isatty", return_value=True)
    @mock.patch("sys.stdout.isatty", return_value=True)
    def test_is_interactive_shell_both_tty(self, mock_stdout, mock_stdin):
        """Test interactive shell detection with both TTY."""
        self.assertTrue(_is_interactive_shell())

    @mock.patch("sys.argv", ["pytest"])
    @mock.patch("sys.stdin.isatty", return_value=False)
    def test_is_interactive_shell_pytest_no_tty(self, mock_stdin):
        """Test pytest without TTY detection."""
        self.assertFalse(_is_interactive_shell())

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_network_error(self, mock_urlopen):
        """Test version fetch with network error."""
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("Network error")
        version = _get_latest_version()
        self.assertIsNone(version)

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_http_error(self, mock_urlopen):
        """Test version fetch with HTTP error."""
        mock_response = mock.MagicMock()
        mock_response.status = 404
        mock_urlopen.return_value.__enter__.return_value = mock_response
        version = _get_latest_version()
        self.assertIsNone(version)

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_oversized_response(self, mock_urlopen):
        """Test version fetch with oversized response."""
        mock_response = mock.MagicMock()
        mock_response.status = 200
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

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_key_error(self, mock_urlopen):
        """Test version fetch with missing key."""
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"info": {}}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        version = _get_latest_version()
        self.assertIsNone(version)

    @mock.patch("caylent_devcontainer_cli.utils.version.urlopen")
    def test_get_latest_version_socket_timeout(self, mock_urlopen):
        """Test version fetch with socket timeout."""
        import socket

        mock_urlopen.side_effect = socket.timeout()
        version = _get_latest_version()
        self.assertIsNone(version)

    def test_version_is_newer_invalid_versions(self):
        """Test version comparison with invalid versions."""
        result = _version_is_newer("invalid", "1.0.0")
        self.assertFalse(result)

    @mock.patch.dict(os.environ, {"CDEVCONTAINER_DEBUG_UPDATE": "1"})
    @mock.patch("sys.stderr")
    def test_debug_log_enabled(self, mock_stderr):
        """Test debug logging when enabled."""
        _debug_log("test message")
        mock_stderr.write.assert_called()

    @mock.patch.dict(os.environ, {}, clear=True)
    @mock.patch("sys.stderr")
    def test_debug_log_disabled(self, mock_stderr):
        """Test debug logging when disabled."""
        _debug_log("test message")
        mock_stderr.write.assert_not_called()

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell", return_value=False)
    def test_check_for_updates_non_interactive(self, mock_interactive):
        """Test update check in non-interactive environment."""
        result = check_for_updates()
        self.assertTrue(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version", return_value=None)
    def test_check_for_updates_no_version(self, mock_get_version, mock_interactive):
        """Test update check when version fetch fails."""
        result = check_for_updates()
        self.assertTrue(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version", return_value="1.0.0")
    @mock.patch("caylent_devcontainer_cli.utils.version._version_is_newer", return_value=False)
    @mock.patch("builtins.print")
    def test_check_for_updates_up_to_date(self, mock_print, mock_newer, mock_get_version, mock_interactive):
        """Test update check when already up to date."""
        result = check_for_updates()
        self.assertTrue(result)
        mock_print.assert_called()

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version", return_value="2.0.0")
    @mock.patch("caylent_devcontainer_cli.utils.version._version_is_newer", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._show_update_prompt", return_value=EXIT_OK)
    def test_check_for_updates_continue(self, mock_prompt, mock_newer, mock_get_version, mock_interactive):
        """Test update check with continue choice."""
        result = check_for_updates()
        self.assertTrue(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version", return_value="2.0.0")
    @mock.patch("caylent_devcontainer_cli.utils.version._version_is_newer", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._show_update_prompt", return_value=EXIT_UPGRADE_REQUESTED_ABORT)
    @mock.patch("sys.exit")
    def test_check_for_updates_exit(self, mock_exit, mock_prompt, mock_newer, mock_get_version, mock_interactive):
        """Test update check with exit choice."""
        check_for_updates()
        mock_exit.assert_called_with(EXIT_UPGRADE_REQUESTED_ABORT)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell", return_value=True)
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version", side_effect=Exception("error"))
    def test_check_for_updates_exception(self, mock_get_version, mock_interactive):
        """Test update check with exception."""
        result = check_for_updates()
        self.assertTrue(result)

    @mock.patch("subprocess.run")
    def test_is_installed_with_pipx_timeout(self, mock_run):
        """Test pipx detection with timeout."""
        import subprocess

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
    def test_is_installed_with_pipx_called_process_error(self, mock_run):
        """Test pipx detection with CalledProcessError."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "pipx")
        result = _is_installed_with_pipx()
        self.assertFalse(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", return_value=True)
    @mock.patch("os.walk")
    def test_is_editable_installation_pipx_with_egg_link(self, mock_walk, mock_pipx):
        """Test editable installation detection with pipx and egg-link."""
        mock_walk.return_value = [("/path", [], ["test.egg-link"])]
        result = _is_editable_installation()
        self.assertTrue(result)

    @mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", return_value=True)
    @mock.patch("os.walk")
    def test_is_editable_installation_pipx_no_egg_link(self, mock_walk, mock_pipx):
        """Test editable installation detection with pipx but no egg-link."""
        mock_walk.return_value = [("/path", [], ["other.file"])]
        result = _is_editable_installation()
        self.assertFalse(result)

    def test_is_editable_installation_exception(self):
        """Test editable installation detection with exception."""
        with mock.patch("caylent_devcontainer_cli.utils.version._is_installed_with_pipx", side_effect=Exception()):
            result = _is_editable_installation()
            self.assertFalse(result)
