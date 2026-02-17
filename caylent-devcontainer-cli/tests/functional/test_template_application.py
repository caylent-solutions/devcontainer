#!/usr/bin/env python3
"""Functional tests for apply_template() consolidated function.

Validates that the merged apply_template(template_data, target_path) correctly
generates all project files without copying .devcontainer/ files.
"""

import json
import os

import pytest

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands.setup_interactive import apply_template


@pytest.fixture
def project_dir(tmp_path):
    """Create a minimal project directory with .devcontainer and .tool-versions."""
    devcontainer_dir = tmp_path / ".devcontainer"
    devcontainer_dir.mkdir()
    # Pre-create .tool-versions to avoid interactive input() prompt in tests
    tool_versions = tmp_path / ".tool-versions"
    tool_versions.write_text("python 3.12.9\n")
    return str(tmp_path)


def _make_template(**overrides):
    """Build a minimal template_data dict with optional overrides."""
    template = {
        "containerEnv": {
            "AWS_CONFIG_ENABLED": "false",
            "DEFAULT_GIT_BRANCH": "main",
            "DEVELOPER_NAME": "Test Dev",
            "GIT_PROVIDER_URL": "github.com",
            "GIT_TOKEN": "test-token",
            "GIT_USER": "testuser",
            "GIT_USER_EMAIL": "test@example.com",
            "PAGER": "cat",
        },
        "aws_profile_map": {},
        "cli_version": __version__,
    }
    template.update(overrides)
    return template


class TestApplyTemplateConsolidated:
    """End-to-end tests for the consolidated apply_template() function."""

    def test_generates_project_files(self, project_dir):
        """apply_template generates env JSON and shell.env."""
        template = _make_template()
        apply_template(template, project_dir)

        env_json = os.path.join(project_dir, "devcontainer-environment-variables.json")
        shell_env = os.path.join(project_dir, "shell.env")
        assert os.path.isfile(env_json), "devcontainer-environment-variables.json not created"
        assert os.path.isfile(shell_env), "shell.env not created"

    def test_does_not_copy_devcontainer_files(self, project_dir):
        """apply_template does NOT copy any files into .devcontainer/."""
        devcontainer_dir = os.path.join(project_dir, ".devcontainer")
        # Record files before
        files_before = set(os.listdir(devcontainer_dir))

        template = _make_template()
        apply_template(template, project_dir)

        # Only aws-profile-map.json or ssh-private-key should appear if enabled
        # With AWS disabled and no SSH, no new files should be in .devcontainer/
        files_after = set(os.listdir(devcontainer_dir))
        assert files_after == files_before, f"Unexpected files added to .devcontainer/: {files_after - files_before}"

    def test_creates_gitignore_entries(self, project_dir):
        """apply_template creates .gitignore with sensitive file entries."""
        template = _make_template()
        apply_template(template, project_dir)

        gitignore_path = os.path.join(project_dir, ".gitignore")
        assert os.path.isfile(gitignore_path)

        with open(gitignore_path, "r") as f:
            content = f.read()

        assert "shell.env" in content
        assert "devcontainer-environment-variables.json" in content

    def test_env_json_has_correct_metadata(self, project_dir):
        """apply_template generates env JSON with metadata."""
        template = _make_template(template_name="my-template", template_path="/templates/test.json")
        apply_template(template, project_dir)

        env_json_path = os.path.join(project_dir, "devcontainer-environment-variables.json")
        with open(env_json_path, "r") as f:
            data = json.load(f)

        assert data["template_name"] == "my-template"
        assert data["template_path"] == "/templates/test.json"
        assert data["cli_version"] == __version__
        assert "containerEnv" in data

    def test_shell_env_has_metadata_header(self, project_dir):
        """apply_template generates shell.env with metadata header."""
        template = _make_template(template_name="my-template", template_path="/templates/test.json")
        apply_template(template, project_dir)

        shell_env_path = os.path.join(project_dir, "shell.env")
        with open(shell_env_path, "r") as f:
            content = f.read()

        assert "# Template: my-template" in content
        assert "# Template Path: /templates/test.json" in content
        assert f"# CLI Version: {__version__}" in content

    def test_aws_profile_map_when_enabled(self, project_dir):
        """apply_template writes aws-profile-map.json when AWS enabled."""
        container_env = {
            "AWS_CONFIG_ENABLED": "true",
        }
        aws_map = {"default": {"region": "us-west-2", "account_id": "123456789012"}}
        template = _make_template(containerEnv=container_env, aws_profile_map=aws_map)
        apply_template(template, project_dir)

        aws_path = os.path.join(project_dir, ".devcontainer", "aws-profile-map.json")
        assert os.path.isfile(aws_path)

        with open(aws_path, "r") as f:
            data = json.load(f)
        assert data["default"]["region"] == "us-west-2"

    def test_ssh_key_content_when_ssh_auth(self, project_dir):
        """apply_template writes actual key content to ssh-private-key when GIT_AUTH_METHOD=ssh."""
        container_env = {
            "GIT_AUTH_METHOD": "ssh",
            "AWS_CONFIG_ENABLED": "false",
        }
        key_content = "-----BEGIN OPENSSH PRIVATE KEY-----\nkeydata\n-----END OPENSSH PRIVATE KEY-----\n"
        template = _make_template(containerEnv=container_env, ssh_private_key=key_content)
        apply_template(template, project_dir)

        ssh_path = os.path.join(project_dir, ".devcontainer", "ssh-private-key")
        assert os.path.isfile(ssh_path)
        with open(ssh_path) as f:
            content = f.read()
        assert content == key_content
        stat = os.stat(ssh_path)
        assert oct(stat.st_mode & 0o777) == "0o600"

    def test_two_arg_signature(self, project_dir):
        """apply_template takes exactly 2 arguments (template_data, target_path)."""
        template = _make_template()
        # Should work with exactly 2 positional args
        apply_template(template, project_dir)

        # Verify it raises TypeError with 3 args (old signature)
        with pytest.raises(TypeError, match="takes 2 positional arguments but 3 were given"):
            apply_template(template, project_dir, "/source")

    def test_idempotent(self, project_dir):
        """Running apply_template twice produces consistent output."""
        template = _make_template()

        apply_template(template, project_dir)
        env_json_path = os.path.join(project_dir, "devcontainer-environment-variables.json")
        with open(env_json_path, "r") as f:
            first_json = json.load(f)

        apply_template(template, project_dir)
        with open(env_json_path, "r") as f:
            second_json = json.load(f)

        assert first_json == second_json
