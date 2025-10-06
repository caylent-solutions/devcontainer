"""Functional tests for CLI update checking."""

import os
import subprocess
import sys
import unittest.mock as mock
from unittest import TestCase


class TestUpdateCheckIntegration(TestCase):
    """Test update check integration with CLI."""

    def test_skip_update_check_flag(self):
        """Test --skip-update-check flag works."""
        # This should run without any update checks
        result = subprocess.run(
            [sys.executable, "-m", "caylent_devcontainer_cli.cli", "--skip-update-check", "--help"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)

    @mock.patch.dict(os.environ, {"CDEVCONTAINER_SKIP_UPDATE": "1"})
    def test_skip_update_env_var(self):
        """Test CDEVCONTAINER_SKIP_UPDATE environment variable."""
        result = subprocess.run(
            [sys.executable, "-m", "caylent_devcontainer_cli.cli", "--help"], capture_output=True, text=True
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)

    @mock.patch.dict(os.environ, {"CI": "true"})
    def test_ci_environment_skip(self):
        """Test update check is skipped in CI environment."""
        result = subprocess.run(
            [sys.executable, "-m", "caylent_devcontainer_cli.cli", "--help"], capture_output=True, text=True
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)

    def test_version_command_works(self):
        """Test --version command still works with update checking."""
        result = subprocess.run(
            [sys.executable, "-m", "caylent_devcontainer_cli.cli", "--version"], capture_output=True, text=True
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Caylent Devcontainer CLI", result.stdout)

    def test_non_interactive_bash_command(self):
        """Test CLI works in non-interactive bash context."""
        # Simulate bash -c execution
        result = subprocess.run(
            ["bash", "-c", f"{sys.executable} -m caylent_devcontainer_cli.cli --help"], capture_output=True, text=True
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)
