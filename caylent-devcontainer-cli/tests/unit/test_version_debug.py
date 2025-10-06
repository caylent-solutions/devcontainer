"""Tests for debug logging and error handling in version checking."""

import os
import tempfile
import unittest.mock as mock
from io import StringIO
from pathlib import Path
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import (
    _acquire_lock,
    _debug_log,
    check_for_updates,
)


class TestDebugLogging(TestCase):
    """Test debug logging functionality."""

    @mock.patch.dict(os.environ, {"CDEVCONTAINER_DEBUG_UPDATE": "1"})
    @mock.patch("sys.stderr", new_callable=StringIO)
    def test_debug_log_enabled(self, mock_stderr):
        """Test debug logging when enabled."""
        _debug_log("test message")
        self.assertIn("DEBUG: test message", mock_stderr.getvalue())

    @mock.patch.dict(os.environ, {}, clear=True)
    @mock.patch("sys.stderr", new_callable=StringIO)
    def test_debug_log_disabled(self, mock_stderr):
        """Test debug logging when disabled."""
        _debug_log("test message")
        self.assertEqual("", mock_stderr.getvalue())


class TestLockHandling(TestCase):
    """Test lock file handling."""

    def setUp(self):
        """Set up test with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cache_dir = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "cdevcontainer"

    def tearDown(self):
        """Clean up test files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch("caylent_devcontainer_cli.utils.version.CACHE_DIR")
    def test_acquire_lock_success(self, mock_cache_dir):
        """Test successful lock acquisition."""
        mock_cache_dir.__truediv__ = lambda self, other: Path(self.temp_dir) / other
        mock_cache_dir.mkdir = mock.MagicMock()

        with mock.patch("caylent_devcontainer_cli.utils.version.LOCK_FILE", Path(self.temp_dir) / "test.lock"):
            result = _acquire_lock()
            self.assertTrue(result)

    @mock.patch("caylent_devcontainer_cli.utils.version.CACHE_DIR")
    def test_acquire_lock_permission_error(self, mock_cache_dir):
        """Test lock acquisition with permission error."""
        mock_cache_dir.mkdir.side_effect = PermissionError()

        result = _acquire_lock()
        self.assertTrue(result)  # Should proceed without lock

    @mock.patch.dict(os.environ, {"CDEVCONTAINER_DEBUG_UPDATE": "1"})
    @mock.patch("sys.stderr", new_callable=StringIO)
    def test_debug_messages_in_check_for_updates(self, mock_stderr):
        """Test debug messages are logged during update check."""
        with mock.patch.dict(os.environ, {"CDEVCONTAINER_SKIP_UPDATE": "1"}):
            check_for_updates()
            self.assertIn("Update check skipped (reason: global disable env)", mock_stderr.getvalue())


class TestErrorHandlingMatrix(TestCase):
    """Test specific error handling scenarios from requirements."""

    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell")
    @mock.patch("caylent_devcontainer_cli.utils.version._acquire_lock")
    def test_network_timeout_handling(self, mock_lock, mock_interactive, mock_get_version):
        """Test network timeout is handled silently."""
        mock_lock.return_value = True
        mock_interactive.return_value = True
        mock_get_version.return_value = None  # Simulates network failure

        result = check_for_updates()
        self.assertTrue(result)  # Should continue silently

    @mock.patch("caylent_devcontainer_cli.utils.version._version_is_newer")
    @mock.patch("caylent_devcontainer_cli.utils.version._get_latest_version")
    @mock.patch("caylent_devcontainer_cli.utils.version._is_interactive_shell")
    @mock.patch("caylent_devcontainer_cli.utils.version._acquire_lock")
    def test_version_parse_error_handling(self, mock_lock, mock_interactive, mock_get_version, mock_version_newer):
        """Test version parse error handling."""
        mock_lock.return_value = True
        mock_interactive.return_value = True
        mock_get_version.return_value = "1.12.0"
        mock_version_newer.return_value = False  # Simulates parse error

        result = check_for_updates()
        self.assertTrue(result)  # Should treat as no update available
