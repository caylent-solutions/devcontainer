"""Functional tests for the template upgrade command (S1.2.4).

End-to-end tests verifying the rewritten upgrade_template_file() uses
validate_template(), updates cli_version, saves the template file,
and does not modify project files.
"""

import inspect
import json
import os
import shutil
import tempfile
from unittest.mock import patch

import pytest

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands.template import upgrade_template_file

# =============================================================================
# Source inspection tests — verify implementation patterns
# =============================================================================


class TestUpgradeTemplateSourceInspection:
    """Verify the upgrade_template_file function uses correct patterns."""

    def _get_source(self):
        from caylent_devcontainer_cli.commands import template

        return inspect.getsource(template.upgrade_template_file)

    def test_uses_validate_template(self):
        """upgrade_template_file() calls validate_template()."""
        assert "validate_template" in self._get_source()

    def test_no_force_flag(self):
        """upgrade_template_file() does not accept a force parameter."""
        source = self._get_source()
        assert "force" not in source

    def test_no_try_except(self):
        """upgrade_template_file() does not wrap in try/except."""
        source = self._get_source()
        assert "try:" not in source
        assert "except" not in source

    def test_no_semver_usage(self):
        """upgrade_template_file() does not use semver comparison."""
        assert "semver" not in self._get_source()

    def test_no_upgrade_template_from_setup_interactive(self):
        """upgrade_template_file() does not call upgrade_template from setup_interactive."""
        source = self._get_source()
        # Replace upgrade_template_file to avoid false match on itself
        cleaned = source.replace("upgrade_template_file", "")
        assert "upgrade_template(" not in cleaned

    def test_no_prompt_for_missing_vars(self):
        """prompt_for_missing_vars and upgrade_template_with_missing_vars are removed."""
        from caylent_devcontainer_cli.commands import template

        module_source = inspect.getsource(template)
        assert "def prompt_for_missing_vars" not in module_source
        assert "def upgrade_template_with_missing_vars" not in module_source

    def test_register_command_no_force_flag(self):
        """register_command() does not add --force to upgrade parser."""
        from caylent_devcontainer_cli.commands import template

        source = inspect.getsource(template.register_command)
        assert "--force" not in source


# =============================================================================
# End-to-end tests — real file I/O
# =============================================================================


def _base_container_env():
    """Return a containerEnv dict with all 13 required base keys."""
    return {
        "AWS_CONFIG_ENABLED": "true",
        "AWS_DEFAULT_OUTPUT": "json",
        "DEFAULT_GIT_BRANCH": "main",
        "DEVELOPER_NAME": "Test User",
        "EXTRA_APT_PACKAGES": "",
        "GIT_AUTH_METHOD": "token",
        "GIT_PROVIDER_URL": "github.com",
        "GIT_TOKEN": "test-token",
        "GIT_USER": "testuser",
        "GIT_USER_EMAIL": "test@example.com",
        "HOST_PROXY": "false",
        "HOST_PROXY_URL": "",
        "PAGER": "cat",
    }


class TestUpgradeTemplateEndToEnd:
    """End-to-end tests with real file I/O."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _write_template(self, name, data):
        path = os.path.join(self.temp_dir, f"{name}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def test_already_current_version(self, capsys):
        """Template at current version — info message, no file write."""
        template_data = {
            "containerEnv": _base_container_env(),
            "cli_version": __version__,
            "template_name": "test",
            "template_path": "/some/path",
        }
        self._write_template("test-template", template_data)

        with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", self.temp_dir):
            upgrade_template_file("test-template")

        captured = capsys.readouterr()
        assert "already at CLI" in captured.err
        assert "No changes needed" in captured.err

        # File should be unchanged
        with open(os.path.join(self.temp_dir, "test-template.json")) as f:
            result = json.load(f)
        assert result == template_data

    def test_v1x_template_rejected(self):
        """v1.x template rejected by validate_template()."""
        template_data = {
            "containerEnv": _base_container_env(),
            "cli_version": "1.14.0",
            "template_name": "old",
            "template_path": "/some/path",
        }
        self._write_template("old-template", template_data)

        with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", self.temp_dir):
            with pytest.raises(SystemExit):
                upgrade_template_file("old-template")

    def test_v2x_upgrade_updates_cli_version(self, capsys):
        """v2.x template with older version — cli_version updated."""
        template_data = {
            "containerEnv": _base_container_env(),
            "cli_version": "2.0.0-alpha.1",
            "template_name": "test",
            "template_path": "/some/path",
        }
        self._write_template("test-template", template_data)

        with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", self.temp_dir):
            upgrade_template_file("test-template")

        with open(os.path.join(self.temp_dir, "test-template.json")) as f:
            result = json.load(f)

        assert result["cli_version"] == __version__

    def test_success_message_content(self, capsys):
        """Success message includes template name, version, and cdevcontainer code reference."""
        template_data = {
            "containerEnv": _base_container_env(),
            "cli_version": "2.0.0-alpha.1",
            "template_name": "my-template",
            "template_path": "/some/path",
        }
        self._write_template("my-template", template_data)

        with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", self.temp_dir):
            upgrade_template_file("my-template")

        captured = capsys.readouterr()
        assert "my-template" in captured.err
        assert f"CLI v{__version__}" in captured.err
        assert "cdevcontainer code" in captured.err

    def test_template_not_found(self):
        """Non-existent template raises SystemExit."""
        with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", self.temp_dir):
            with pytest.raises(SystemExit):
                upgrade_template_file("nonexistent")

    def test_only_template_file_modified(self, capsys):
        """Upgrade modifies only the template file, not project files."""
        template_data = {
            "containerEnv": _base_container_env(),
            "cli_version": "2.0.0-alpha.1",
            "template_name": "test",
            "template_path": "/some/path",
        }
        self._write_template("test-template", template_data)

        # Create a mock project directory to prove it's not touched
        project_dir = os.path.join(self.temp_dir, "project")
        os.makedirs(project_dir)
        sentinel = os.path.join(project_dir, "untouched.txt")
        with open(sentinel, "w") as f:
            f.write("original")

        with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", self.temp_dir):
            upgrade_template_file("test-template")

        # Sentinel file should be unchanged
        with open(sentinel) as f:
            assert f.read() == "original"

        # Only the template file should have been modified
        with open(os.path.join(self.temp_dir, "test-template.json")) as f:
            result = json.load(f)
        assert result["cli_version"] == __version__
