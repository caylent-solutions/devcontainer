#!/usr/bin/env python3
"""Functional tests for write_project_files() end-to-end behavior."""

import json
import os

import pytest

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.constants import DEFAULT_NO_PROXY
from caylent_devcontainer_cli.utils.fs import write_project_files


@pytest.fixture
def project_dir(tmp_path):
    """Create a minimal project directory with .devcontainer."""
    devcontainer_dir = tmp_path / ".devcontainer"
    devcontainer_dir.mkdir()
    return str(tmp_path)


class TestWriteProjectFilesEndToEnd:
    """End-to-end tests for write_project_files()."""

    def _make_template(self, **overrides):
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

    def test_generates_both_files_together(self, project_dir):
        """Both env JSON and shell.env are always created together."""
        template = self._make_template()
        write_project_files(project_dir, template, "test-template", "/templates/test.json")

        env_json = os.path.join(project_dir, "devcontainer-environment-variables.json")
        shell_env = os.path.join(project_dir, "shell.env")
        assert os.path.isfile(env_json), "devcontainer-environment-variables.json not created"
        assert os.path.isfile(shell_env), "shell.env not created"

    def test_env_json_structure_and_metadata(self, project_dir):
        """devcontainer-environment-variables.json has correct metadata and sorted keys."""
        template = self._make_template()
        write_project_files(project_dir, template, "my-template", "/path/to/template.json")

        env_json_path = os.path.join(project_dir, "devcontainer-environment-variables.json")
        with open(env_json_path, "r") as f:
            data = json.load(f)

        assert data["template_name"] == "my-template"
        assert data["template_path"] == "/path/to/template.json"
        assert data["cli_version"] == __version__
        assert "containerEnv" in data

        # Verify keys are sorted
        keys = list(data["containerEnv"].keys())
        assert keys == sorted(keys), f"containerEnv keys not sorted: {keys}"

    def test_shell_env_metadata_header(self, project_dir):
        """shell.env starts with metadata comment lines."""
        template = self._make_template()
        write_project_files(project_dir, template, "my-template", "/path/to/template.json")

        shell_env_path = os.path.join(project_dir, "shell.env")
        with open(shell_env_path, "r") as f:
            content = f.read()

        assert "# Template: my-template" in content
        assert "# Template Path: /path/to/template.json" in content
        assert f"# CLI Version: {__version__}" in content
        assert "# Generated:" in content

    def test_shell_env_exports_sorted(self, project_dir):
        """All export lines in shell.env are sorted alphabetically."""
        template = self._make_template()
        write_project_files(project_dir, template, "test", "")

        shell_env_path = os.path.join(project_dir, "shell.env")
        with open(shell_env_path, "r") as f:
            lines = f.readlines()

        export_lines = [line.strip() for line in lines if line.startswith("export ") and "PATH=" not in line]
        export_keys = [line.split("=")[0].replace("export ", "") for line in export_lines]
        assert export_keys == sorted(export_keys), f"Exports not sorted: {export_keys}"

    def test_shell_env_static_values(self, project_dir):
        """shell.env contains required static container values."""
        template = self._make_template()
        write_project_files(project_dir, template, "test", "")

        shell_env_path = os.path.join(project_dir, "shell.env")
        with open(shell_env_path, "r") as f:
            content = f.read()

        assert "export DEVCONTAINER='true'" in content
        assert "NO_PROXY" not in content
        assert "no_proxy" not in content
        assert "BASH_ENV=" in content
        assert "unset GIT_EDITOR" in content

    def test_proxy_vars_when_host_proxy_true(self, project_dir):
        """Proxy variables are generated when HOST_PROXY=true."""
        container_env = {
            "HOST_PROXY": "true",
            "HOST_PROXY_URL": "http://proxy.example.com:8080",
            "AWS_CONFIG_ENABLED": "false",
        }
        template = self._make_template(containerEnv=container_env)
        write_project_files(project_dir, template, "test", "")

        shell_env_path = os.path.join(project_dir, "shell.env")
        with open(shell_env_path, "r") as f:
            content = f.read()

        assert "export HTTP_PROXY='http://proxy.example.com:8080'" in content
        assert "export HTTPS_PROXY='http://proxy.example.com:8080'" in content
        assert "export http_proxy='http://proxy.example.com:8080'" in content
        assert "export https_proxy='http://proxy.example.com:8080'" in content
        assert f"export NO_PROXY='{DEFAULT_NO_PROXY}'" in content
        assert f"export no_proxy='{DEFAULT_NO_PROXY}'" in content

    def test_no_proxy_vars_when_host_proxy_false(self, project_dir):
        """No proxy variables when HOST_PROXY is not true."""
        template = self._make_template()
        write_project_files(project_dir, template, "test", "")

        shell_env_path = os.path.join(project_dir, "shell.env")
        with open(shell_env_path, "r") as f:
            content = f.read()

        assert "HTTP_PROXY=" not in content
        assert "HTTPS_PROXY=" not in content

    def test_aws_profile_map_created_when_enabled(self, project_dir):
        """aws-profile-map.json is written when AWS_CONFIG_ENABLED=true."""
        container_env = {"AWS_CONFIG_ENABLED": "true"}
        aws_map = {"default": {"region": "us-west-2", "account_id": "123456789012"}}
        template = self._make_template(containerEnv=container_env, aws_profile_map=aws_map)
        write_project_files(project_dir, template, "test", "")

        aws_path = os.path.join(project_dir, ".devcontainer", "aws-profile-map.json")
        assert os.path.isfile(aws_path)

        with open(aws_path, "r") as f:
            data = json.load(f)
        assert data["default"]["region"] == "us-west-2"

    def test_no_aws_profile_map_when_disabled(self, project_dir):
        """aws-profile-map.json is NOT written when AWS_CONFIG_ENABLED=false."""
        template = self._make_template()
        write_project_files(project_dir, template, "test", "")

        aws_path = os.path.join(project_dir, ".devcontainer", "aws-profile-map.json")
        assert not os.path.isfile(aws_path)

    def test_ssh_key_placeholder_when_ssh_auth(self, project_dir):
        """ssh-private-key placeholder is created when GIT_AUTH_METHOD=ssh."""
        container_env = {"GIT_AUTH_METHOD": "ssh", "AWS_CONFIG_ENABLED": "false"}
        template = self._make_template(containerEnv=container_env)
        write_project_files(project_dir, template, "test", "")

        ssh_path = os.path.join(project_dir, ".devcontainer", "ssh-private-key")
        assert os.path.isfile(ssh_path)
        # Verify permissions
        stat = os.stat(ssh_path)
        assert oct(stat.st_mode & 0o777) == "0o600"

    def test_no_ssh_key_when_token_auth(self, project_dir):
        """ssh-private-key is NOT created when GIT_AUTH_METHOD is not ssh."""
        template = self._make_template()
        write_project_files(project_dir, template, "test", "")

        ssh_path = os.path.join(project_dir, ".devcontainer", "ssh-private-key")
        assert not os.path.isfile(ssh_path)

    def test_gitignore_entries_created(self, project_dir):
        """All 4 sensitive file entries are added to .gitignore."""
        template = self._make_template()
        write_project_files(project_dir, template, "test", "")

        gitignore_path = os.path.join(project_dir, ".gitignore")
        assert os.path.isfile(gitignore_path)

        with open(gitignore_path, "r") as f:
            content = f.read()

        assert "shell.env" in content
        assert "devcontainer-environment-variables.json" in content
        assert ".devcontainer/aws-profile-map.json" in content
        assert ".devcontainer/ssh-private-key" in content

    def test_gitignore_entries_not_duplicated(self, project_dir):
        """Running write_project_files twice does not duplicate .gitignore entries."""
        template = self._make_template()
        write_project_files(project_dir, template, "test", "")
        write_project_files(project_dir, template, "test", "")

        gitignore_path = os.path.join(project_dir, ".gitignore")
        with open(gitignore_path, "r") as f:
            content = f.read()

        # Each entry should appear exactly once
        assert content.count("shell.env") == 1
        assert content.count("devcontainer-environment-variables.json") == 1

    def test_idempotent_regeneration(self, project_dir):
        """Running write_project_files twice produces valid, consistent output."""
        template = self._make_template()

        write_project_files(project_dir, template, "test", "")
        env_json_path = os.path.join(project_dir, "devcontainer-environment-variables.json")
        with open(env_json_path, "r") as f:
            first_json = json.load(f)

        write_project_files(project_dir, template, "test", "")
        with open(env_json_path, "r") as f:
            second_json = json.load(f)

        # JSON content should be identical (except possibly timestamp in shell.env)
        assert first_json == second_json
