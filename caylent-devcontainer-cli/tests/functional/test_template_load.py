"""Functional tests for the template load command (S1.2.3).

End-to-end tests verifying the rewritten load_template() uses
validate_template() and write_project_files(), with no raw input()
or confirm_action() calls.
"""

import json
import os
from unittest.mock import MagicMock, patch

from caylent_devcontainer_cli.commands.template import load_template

# =============================================================================
# Source inspection tests — verify implementation patterns
# =============================================================================


class TestLoadTemplateSourceInspection:
    """Verify the load_template function uses correct patterns."""

    def _get_source(self):
        import inspect

        from caylent_devcontainer_cli.commands import template

        return inspect.getsource(template.load_template)

    def test_uses_validate_template(self):
        """load_template() calls validate_template()."""
        source = self._get_source()
        assert "validate_template" in source

    def test_uses_write_project_files(self):
        """load_template() calls write_project_files()."""
        source = self._get_source()
        assert "write_project_files" in source

    def test_uses_questionary_confirm(self):
        """load_template() uses questionary.confirm for overwrite."""
        source = self._get_source()
        assert "questionary.confirm" in source

    def test_no_confirm_action(self):
        """load_template() does not use confirm_action."""
        source = self._get_source()
        assert "confirm_action" not in source

    def test_no_raw_input(self):
        """load_template() does not use raw input()."""
        source = self._get_source()
        assert "input(" not in source

    def test_no_semver_version_menu(self):
        """load_template() does not implement a version choice menu."""
        source = self._get_source()
        assert "Enter your choice" not in source
        assert "Upgrade the profile" not in source

    def test_uses_ask_or_exit(self):
        """load_template() uses ask_or_exit for questionary wrapping."""
        source = self._get_source()
        assert "ask_or_exit" in source

    def test_uses_load_json_config(self):
        """load_template() uses load_json_config to read the template."""
        source = self._get_source()
        assert "load_json_config" in source


# =============================================================================
# End-to-end flow tests
# =============================================================================


class TestLoadTemplateEndToEnd:
    """End-to-end tests for the template load flow."""

    def _make_template(self, tmp_path, template_name, template_data):
        """Helper: write a template file and return its path."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir(exist_ok=True)
        template_file = templates_dir / f"{template_name}.json"
        template_file.write_text(json.dumps(template_data))
        return str(templates_dir)

    def _make_project(self, tmp_path):
        """Helper: create a project directory with .devcontainer."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".devcontainer").mkdir()
        return str(project_root)

    def _base_container_env(self, **overrides):
        """Return a complete containerEnv dict with all required keys."""
        env = {
            "AWS_CONFIG_ENABLED": "false",
            "AWS_DEFAULT_OUTPUT": "json",
            "DEFAULT_GIT_BRANCH": "main",
            "DEVELOPER_NAME": "Test User",
            "EXTRA_APT_PACKAGES": "",
            "GIT_AUTH_METHOD": "token",
            "GIT_PROVIDER_URL": "github.com",
            "GIT_TOKEN": "ghp_test123",
            "GIT_USER": "testuser",
            "GIT_USER_EMAIL": "test@example.com",
            "HOST_PROXY": "false",
            "HOST_PROXY_URL": "",
            "PAGER": "cat",
        }
        env.update(overrides)
        return env

    def test_load_generates_both_files(self, tmp_path):
        """Loading a template generates both env JSON and shell.env."""
        template_data = {
            "containerEnv": self._base_container_env(),
            "cli_version": "2.0.0",
            "template_name": "test-tmpl",
            "template_path": "/tmp/test.json",
            "aws_profile_map": {},
        }

        templates_dir = self._make_template(tmp_path, "test-tmpl", template_data)
        project_root = self._make_project(tmp_path)

        with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", templates_dir):
            load_template(project_root, "test-tmpl")

        # Both files should exist
        env_json_path = os.path.join(project_root, "devcontainer-environment-variables.json")
        shell_env_path = os.path.join(project_root, "shell.env")

        assert os.path.exists(env_json_path)
        assert os.path.exists(shell_env_path)

        # Verify JSON content
        with open(env_json_path) as f:
            saved = json.load(f)
        assert saved["template_name"] == "test-tmpl"
        assert "containerEnv" in saved
        assert saved["containerEnv"]["DEVELOPER_NAME"] == "Test User"

        # Verify shell.env content
        with open(shell_env_path) as f:
            shell_content = f.read()
        assert "export DEVELOPER_NAME='Test User'" in shell_content
        assert "export GIT_AUTH_METHOD='token'" in shell_content

    def test_load_creates_gitignore_entries(self, tmp_path):
        """Loading a template ensures .gitignore has required entries."""
        template_data = {
            "containerEnv": self._base_container_env(),
            "cli_version": "2.0.0",
            "template_name": "test",
            "template_path": "/tmp/test.json",
            "aws_profile_map": {},
        }

        templates_dir = self._make_template(tmp_path, "test", template_data)
        project_root = self._make_project(tmp_path)

        with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", templates_dir):
            load_template(project_root, "test")

        gitignore_path = os.path.join(project_root, ".gitignore")
        assert os.path.exists(gitignore_path)

        with open(gitignore_path) as f:
            content = f.read()

        assert "shell.env" in content
        assert "devcontainer-environment-variables.json" in content

    def test_load_writes_aws_profile_map(self, tmp_path):
        """Loading a template with AWS enabled writes aws-profile-map.json."""
        template_data = {
            "containerEnv": self._base_container_env(AWS_CONFIG_ENABLED="true"),
            "cli_version": "2.0.0",
            "template_name": "aws-test",
            "template_path": "/tmp/test.json",
            "aws_profile_map": {"default": {"region": "us-east-1"}},
        }

        templates_dir = self._make_template(tmp_path, "aws-test", template_data)
        project_root = self._make_project(tmp_path)

        with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", templates_dir):
            load_template(project_root, "aws-test")

        aws_map_path = os.path.join(project_root, ".devcontainer", "aws-profile-map.json")
        assert os.path.exists(aws_map_path)

        with open(aws_map_path) as f:
            saved = json.load(f)
        assert saved == {"default": {"region": "us-east-1"}}

    def test_load_writes_ssh_key_content(self, tmp_path):
        """Loading a template with SSH auth writes actual key content to ssh-private-key."""
        key_content = "-----BEGIN KEY-----\ndata\n-----END KEY-----\n"
        template_data = {
            "containerEnv": self._base_container_env(GIT_AUTH_METHOD="ssh"),
            "ssh_private_key": key_content,
            "cli_version": "2.0.0",
            "template_name": "ssh-test",
            "template_path": "/tmp/test.json",
            "aws_profile_map": {},
        }

        templates_dir = self._make_template(tmp_path, "ssh-test", template_data)
        project_root = self._make_project(tmp_path)

        with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", templates_dir):
            load_template(project_root, "ssh-test")

        ssh_key_path = os.path.join(project_root, ".devcontainer", "ssh-private-key")
        assert os.path.exists(ssh_key_path)
        with open(ssh_key_path) as f:
            written = f.read()
        assert written == key_content

    def test_load_overwrite_prompt_with_questionary(self, tmp_path):
        """Overwrite prompt uses questionary.confirm, not confirm_action."""
        template_data = {
            "containerEnv": self._base_container_env(),
            "cli_version": "2.0.0",
            "template_name": "test",
            "template_path": "/tmp/test.json",
            "aws_profile_map": {},
        }

        templates_dir = self._make_template(tmp_path, "test", template_data)
        project_root = self._make_project(tmp_path)

        # Create existing env file
        env_file = os.path.join(project_root, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump({"old": "data"}, f)

        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with (
            patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", templates_dir),
            patch("questionary.confirm", return_value=mock_confirm) as mock_qconfirm,
        ):
            load_template(project_root, "test")

        # questionary.confirm should have been called for overwrite
        mock_qconfirm.assert_called_once()
        assert "overwrite" in mock_qconfirm.call_args[0][0].lower()

    def test_load_v1x_template_rejected(self, tmp_path):
        """v1.x template is rejected by validate_template with clear error."""
        template_data = {
            "containerEnv": {"KEY": "val"},
            "cli_version": "1.14.0",
            "template_name": "old",
            "template_path": "/tmp/old.json",
        }

        templates_dir = self._make_template(tmp_path, "old", template_data)
        project_root = self._make_project(tmp_path)

        import pytest

        with (
            patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", templates_dir),
            pytest.raises(SystemExit),
        ):
            load_template(project_root, "old")
