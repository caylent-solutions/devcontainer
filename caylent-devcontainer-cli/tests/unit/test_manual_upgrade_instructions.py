"""Unit tests for manual upgrade instructions."""

import unittest.mock as mock
from io import StringIO
from unittest import TestCase

from caylent_devcontainer_cli.utils.version import _show_manual_upgrade_instructions


class TestManualUpgradeInstructions(TestCase):
    """Test manual upgrade instructions for different installation types."""

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_pipx_regular_instructions(self, mock_stdout):
        """Test manual upgrade instructions for pipx regular installation."""
        _show_manual_upgrade_instructions("pipx")

        output = mock_stdout.getvalue()
        self.assertIn("Upgrade with pipx:", output)
        self.assertIn("pipx upgrade caylent-devcontainer-cli", output)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_pipx_editable_instructions(self, mock_stdout):
        """Test manual upgrade instructions for pipx editable installation."""
        _show_manual_upgrade_instructions("pipx editable")

        output = mock_stdout.getvalue()
        self.assertIn("Upgrade editable installation:", output)
        self.assertIn("cd /path/to/caylent-devcontainer-cli", output)
        self.assertIn("git pull", output)
        self.assertIn("pipx reinstall -e .", output)
        self.assertIn("Or switch to regular pipx installation:", output)
        self.assertIn("pipx uninstall caylent-devcontainer-cli", output)
        self.assertIn("pipx install caylent-devcontainer-cli", output)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_pip_editable_instructions(self, mock_stdout):
        """Test manual upgrade instructions for pip editable installation."""
        _show_manual_upgrade_instructions("pip editable")

        output = mock_stdout.getvalue()
        self.assertIn("Upgrade editable installation:", output)
        self.assertIn("cd /path/to/caylent-devcontainer-cli", output)
        self.assertIn("git pull", output)
        self.assertIn("pip install -e .", output)
        self.assertIn("Or switch to pipx (recommended):", output)
        self.assertIn("pip uninstall caylent-devcontainer-cli", output)
        self.assertIn("pipx install caylent-devcontainer-cli", output)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_pip_regular_instructions(self, mock_stdout):
        """Test manual upgrade instructions for pip regular installation."""
        _show_manual_upgrade_instructions("pip")

        output = mock_stdout.getvalue()
        self.assertIn("Switch to pipx:", output)
        self.assertIn("pip uninstall caylent-devcontainer-cli", output)
        self.assertIn("pipx install caylent-devcontainer-cli", output)
