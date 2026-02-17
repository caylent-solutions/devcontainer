#!/usr/bin/env python3
import json
import os
import sys
from unittest.mock import mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ENTRY_FILENAME,
    DEFAULT_NO_PROXY,
    ENV_VARS_FILENAME,
    SHELL_ENV_FILENAME,
    SSH_KEY_FILENAME,
)
from caylent_devcontainer_cli.utils.fs import (
    load_json_config,
    resolve_project_root,
    write_json_file,
)


@patch("builtins.open", mock_open(read_data='{"containerEnv": {"TEST_VAR": "test_value"}}'))
def test_load_json_config():
    data = load_json_config("test_file.json")
    assert data == {"containerEnv": {"TEST_VAR": "test_value"}}


@patch("builtins.open", mock_open(read_data="invalid json"))
def test_load_json_config_invalid():
    with pytest.raises(SystemExit):
        load_json_config("test_file.json")


def test_load_json_config_file_not_found():
    """Test loading JSON config when file doesn't exist."""
    with (
        patch("builtins.open", side_effect=FileNotFoundError()),
        patch("caylent_devcontainer_cli.utils.fs.log"),
        patch("sys.exit", side_effect=SystemExit(1)) as mock_exit,
    ):
        with pytest.raises(SystemExit):
            load_json_config("/test/path/nonexistent.json")
        mock_exit.assert_called_once_with(1)


# =============================================================================
# write_json_file tests
# =============================================================================


class TestWriteJsonFile:
    """Tests for write_json_file utility."""

    def test_writes_json_with_indent_2(self, tmp_path):
        """Test that write_json_file writes JSON with indent=2."""
        file_path = str(tmp_path / "output.json")
        data = {"key": "value", "nested": {"a": 1}}

        write_json_file(file_path, data)

        with open(file_path, "r") as f:
            content = f.read()

        expected = json.dumps(data, indent=2) + "\n"
        assert content == expected

    def test_writes_trailing_newline(self, tmp_path):
        """Test that write_json_file appends a trailing newline."""
        file_path = str(tmp_path / "output.json")
        data = {"key": "value"}

        write_json_file(file_path, data)

        with open(file_path, "r") as f:
            content = f.read()

        assert content.endswith("\n")
        # Ensure it's exactly one trailing newline (not two)
        assert not content.endswith("\n\n")

    def test_writes_empty_dict(self, tmp_path):
        """Test that write_json_file handles an empty dictionary."""
        file_path = str(tmp_path / "empty.json")
        data = {}

        write_json_file(file_path, data)

        with open(file_path, "r") as f:
            content = f.read()

        assert content == "{}\n"

    def test_writes_complex_nested_data(self, tmp_path):
        """Test that write_json_file handles complex nested structures."""
        file_path = str(tmp_path / "complex.json")
        data = {
            "containerEnv": {
                "AWS_CONFIG_ENABLED": "true",
            },
            "cli_version": "2.0.0",
        }

        write_json_file(file_path, data)

        with open(file_path, "r") as f:
            loaded = json.load(f)

        assert loaded == data

    def test_overwrites_existing_file(self, tmp_path):
        """Test that write_json_file overwrites an existing file."""
        file_path = str(tmp_path / "existing.json")

        # Write initial content
        write_json_file(file_path, {"old": "data"})

        # Overwrite with new content
        write_json_file(file_path, {"new": "data"})

        with open(file_path, "r") as f:
            loaded = json.load(f)

        assert loaded == {"new": "data"}

    def test_write_failure_exits(self, tmp_path):
        """Test that write_json_file exits on write failure."""
        # Use a path that doesn't exist (no parent directory)
        file_path = str(tmp_path / "nonexistent_dir" / "output.json")

        with pytest.raises(SystemExit):
            write_json_file(file_path, {"key": "value"})

    def test_writes_list_data(self, tmp_path):
        """Test that write_json_file handles list data."""
        file_path = str(tmp_path / "list.json")
        data = [{"name": "item1"}, {"name": "item2"}]

        write_json_file(file_path, data)

        with open(file_path, "r") as f:
            loaded = json.load(f)

        assert loaded == data


# =============================================================================
# File path constants tests
# =============================================================================


class TestFilePathConstants:
    """Tests for file path constants in utils/constants.py."""

    def test_env_vars_filename(self):
        """Test ENV_VARS_FILENAME constant value."""
        assert ENV_VARS_FILENAME == "devcontainer-environment-variables.json"

    def test_shell_env_filename(self):
        """Test SHELL_ENV_FILENAME constant value."""
        assert SHELL_ENV_FILENAME == "shell.env"

    def test_catalog_entry_filename(self):
        """Test CATALOG_ENTRY_FILENAME constant value."""
        assert CATALOG_ENTRY_FILENAME == "catalog-entry.json"

    def test_ssh_key_filename(self):
        """Test SSH_KEY_FILENAME constant value."""
        assert SSH_KEY_FILENAME == "ssh-private-key"


# =============================================================================
# resolve_project_root tests
# =============================================================================


class TestResolveProjectRoot:
    """Tests for resolve_project_root utility."""

    def test_defaults_to_cwd_when_path_is_none(self):
        """Test that resolve_project_root defaults to os.getcwd() when path is None."""
        with patch("os.getcwd", return_value="/current/dir"), patch("os.path.isdir", return_value=True):
            result = resolve_project_root()
            assert result == "/current/dir"

    def test_uses_provided_path(self):
        """Test that resolve_project_root uses the provided path."""
        with patch("os.path.isdir", return_value=True):
            result = resolve_project_root("/my/project")
            assert result == "/my/project"

    def test_validates_devcontainer_dir_exists(self):
        """Test that resolve_project_root validates .devcontainer/ exists."""
        with patch("os.path.isdir", return_value=False):
            with pytest.raises(SystemExit):
                resolve_project_root("/no/devcontainer")

    def test_handles_file_path_by_using_dirname(self):
        """Test that resolve_project_root handles file paths correctly."""
        with (
            patch("os.path.isfile", return_value=True),
            patch("os.path.dirname", return_value="/my/project"),
            patch("os.path.isdir", return_value=True),
        ):
            result = resolve_project_root("/my/project/file.json")
            assert result == "/my/project"

    def test_exits_with_clear_error_on_invalid_path(self):
        """Test that resolve_project_root exits with a clear error message."""
        with (
            patch("os.path.isdir", return_value=False),
            patch("os.path.isfile", return_value=False),
            patch("caylent_devcontainer_cli.utils.fs.log") as mock_log,
            patch("caylent_devcontainer_cli.utils.fs.exit_with_error", side_effect=SystemExit(1)) as mock_exit_error,
        ):
            with pytest.raises(SystemExit):
                resolve_project_root("/bad/path")
            mock_log.assert_any_call("INFO", "A valid project root must contain a .devcontainer directory")
            mock_exit_error.assert_called_once_with("Could not find a valid project root at /bad/path")

    def test_empty_string_defaults_to_cwd(self):
        """Test that empty string path defaults to cwd."""
        with patch("os.getcwd", return_value="/cwd/path"), patch("os.path.isdir", return_value=True):
            result = resolve_project_root("")
            assert result == "/cwd/path"


# =============================================================================
# write_project_files tests
# =============================================================================


class TestWriteProjectFiles:
    """Tests for write_project_files utility."""

    def _make_template_data(self, **overrides):
        """Build minimal template data for testing."""
        data = {
            "containerEnv": {
                "DEVELOPER_NAME": "Test User",
                "GIT_USER": "testuser",
                "GIT_USER_EMAIL": "test@example.com",
                "GIT_TOKEN": "test-token",
                "GIT_PROVIDER_URL": "github.com",
                "DEFAULT_GIT_BRANCH": "main",
                "CICD": "false",
                "AWS_CONFIG_ENABLED": "false",
                "EXTRA_APT_PACKAGES": "",
                "PAGER": "cat",
                "AWS_DEFAULT_OUTPUT": "json",
            },
            "cli_version": "2.0.0",
        }
        data.update(overrides)
        return data

    def _setup_project(self, tmp_path):
        """Create a minimal project structure."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        devcontainer_dir = project_root / ".devcontainer"
        devcontainer_dir.mkdir()
        return str(project_root)

    def test_generates_env_vars_json(self, tmp_path):
        """Test that write_project_files creates devcontainer-environment-variables.json."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "test-template", "/path/to/template")

        env_file = os.path.join(project_root, "devcontainer-environment-variables.json")
        assert os.path.isfile(env_file)

        with open(env_file, "r") as f:
            data = json.load(f)

        assert "containerEnv" in data
        assert data["containerEnv"]["DEVELOPER_NAME"] == "Test User"

    def test_env_vars_json_has_metadata(self, tmp_path):
        """Test that env vars JSON includes template_name, template_path, cli_version."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "my-template", "/home/user/.templates/my-template.json")

        env_file = os.path.join(project_root, "devcontainer-environment-variables.json")
        with open(env_file, "r") as f:
            data = json.load(f)

        assert data["template_name"] == "my-template"
        assert data["template_path"] == "/home/user/.templates/my-template.json"
        assert data["cli_version"] == "2.0.0"

    def test_env_vars_json_sorted_keys(self, tmp_path):
        """Test that containerEnv keys are sorted alphabetically."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "test", "/path")

        env_file = os.path.join(project_root, "devcontainer-environment-variables.json")
        with open(env_file, "r") as f:
            content = f.read()

        # Parse and check keys are sorted
        data = json.loads(content)
        keys = list(data["containerEnv"].keys())
        assert keys == sorted(keys)

    def test_generates_shell_env(self, tmp_path):
        """Test that write_project_files creates shell.env."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "test", "/path")

        shell_env = os.path.join(project_root, "shell.env")
        assert os.path.isfile(shell_env)

    def test_shell_env_has_metadata_header(self, tmp_path):
        """Test that shell.env has metadata comment header."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "my-template", "/path/to/tmpl")

        shell_env = os.path.join(project_root, "shell.env")
        with open(shell_env, "r") as f:
            content = f.read()

        assert "# Template: my-template" in content
        assert "# Template Path: /path/to/tmpl" in content
        assert "# CLI Version: 2.0.0" in content
        assert "# Generated:" in content

    def test_shell_env_exports_sorted(self, tmp_path):
        """Test that shell.env export lines are sorted alphabetically."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "test", "/path")

        shell_env = os.path.join(project_root, "shell.env")
        with open(shell_env, "r") as f:
            lines = f.readlines()

        # Extract export lines (skip comments, blank lines, unset, PATH)
        export_lines = [line.strip() for line in lines if line.startswith("export ") and "PATH=" not in line]
        export_keys = [line.split("=")[0].replace("export ", "") for line in export_lines]
        assert export_keys == sorted(export_keys)

    def test_shell_env_static_container_values(self, tmp_path):
        """Test that shell.env includes static container values."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "test", "/path")

        shell_env = os.path.join(project_root, "shell.env")
        with open(shell_env, "r") as f:
            content = f.read()

        assert "export DEVCONTAINER='true'" in content
        assert "BASH_ENV=" in content and "shell.env" in content
        assert "NO_PROXY" not in content
        assert "no_proxy" not in content
        assert "unset GIT_EDITOR" in content
        assert ".asdf/shims" in content
        assert ".localscripts" in content

    def test_shell_env_proxy_vars_when_host_proxy_true(self, tmp_path):
        """Test that proxy vars are generated when HOST_PROXY=true."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()
        template_data["containerEnv"]["HOST_PROXY"] = "true"
        template_data["containerEnv"]["HOST_PROXY_URL"] = "http://proxy.corp:8080"

        write_project_files(project_root, template_data, "test", "/path")

        shell_env = os.path.join(project_root, "shell.env")
        with open(shell_env, "r") as f:
            content = f.read()

        assert "export HTTP_PROXY='http://proxy.corp:8080'" in content
        assert "export HTTPS_PROXY='http://proxy.corp:8080'" in content
        assert "export http_proxy='http://proxy.corp:8080'" in content
        assert "export https_proxy='http://proxy.corp:8080'" in content
        assert f"export NO_PROXY='{DEFAULT_NO_PROXY}'" in content
        assert f"export no_proxy='{DEFAULT_NO_PROXY}'" in content

    def test_shell_env_no_proxy_vars_when_host_proxy_false(self, tmp_path):
        """Test that proxy vars are NOT generated when HOST_PROXY is not true."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "test", "/path")

        shell_env = os.path.join(project_root, "shell.env")
        with open(shell_env, "r") as f:
            content = f.read()

        assert "HTTP_PROXY=" not in content
        assert "HTTPS_PROXY=" not in content
        assert "http_proxy=" not in content
        assert "https_proxy=" not in content

    def test_writes_aws_profile_map_when_enabled(self, tmp_path):
        """Test that aws-profile-map.json is written when AWS_CONFIG_ENABLED=true."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()
        template_data["containerEnv"]["AWS_CONFIG_ENABLED"] = "true"
        template_data["aws_profile_map"] = {"default": {"region": "us-east-1"}}

        write_project_files(project_root, template_data, "test", "/path")

        aws_file = os.path.join(project_root, ".devcontainer", "aws-profile-map.json")
        assert os.path.isfile(aws_file)

        with open(aws_file, "r") as f:
            data = json.load(f)
        assert data == {"default": {"region": "us-east-1"}}

    def test_no_aws_profile_map_when_disabled(self, tmp_path):
        """Test that aws-profile-map.json is NOT written when AWS_CONFIG_ENABLED=false."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "test", "/path")

        aws_file = os.path.join(project_root, ".devcontainer", "aws-profile-map.json")
        assert not os.path.exists(aws_file)

    def test_writes_ssh_key_content_when_ssh_auth(self, tmp_path):
        """Test that ssh-private-key is written with actual key content when GIT_AUTH_METHOD=ssh."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()
        template_data["containerEnv"]["GIT_AUTH_METHOD"] = "ssh"
        template_data["ssh_private_key"] = (
            "-----BEGIN OPENSSH PRIVATE KEY-----\nkeydata\n-----END OPENSSH PRIVATE KEY-----\n"
        )

        write_project_files(project_root, template_data, "test", "/path")

        ssh_key = os.path.join(project_root, ".devcontainer", "ssh-private-key")
        assert os.path.isfile(ssh_key)
        with open(ssh_key) as f:
            content = f.read()
        assert "-----BEGIN OPENSSH PRIVATE KEY-----" in content
        assert "keydata" in content

    def test_no_ssh_key_when_token_auth(self, tmp_path):
        """Test that ssh-private-key is NOT written when GIT_AUTH_METHOD is not ssh."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "test", "/path")

        ssh_key = os.path.join(project_root, ".devcontainer", "ssh-private-key")
        assert not os.path.exists(ssh_key)

    def test_ensures_gitignore_entries(self, tmp_path):
        """Test that .gitignore is updated with all 4 sensitive file entries."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "test", "/path")

        gitignore = os.path.join(project_root, ".gitignore")
        assert os.path.isfile(gitignore)

        with open(gitignore, "r") as f:
            content = f.read()

        assert "shell.env" in content
        assert "devcontainer-environment-variables.json" in content
        assert ".devcontainer/aws-profile-map.json" in content
        assert ".devcontainer/ssh-private-key" in content

    def test_both_files_always_generated_together(self, tmp_path):
        """Test that both env vars JSON and shell.env are always generated."""
        from caylent_devcontainer_cli.utils.fs import write_project_files

        project_root = self._setup_project(tmp_path)
        template_data = self._make_template_data()

        write_project_files(project_root, template_data, "test", "/path")

        env_file = os.path.join(project_root, "devcontainer-environment-variables.json")
        shell_env = os.path.join(project_root, "shell.env")
        assert os.path.isfile(env_file)
        assert os.path.isfile(shell_env)


# =============================================================================
# CLI_NAME import test
# =============================================================================


class TestCLINameConstant:
    """Tests to verify CLI_NAME is imported from constants, not defined in cli.py."""

    def test_cli_name_exists_in_constants(self):
        """Test that CLI_NAME is defined in utils/constants.py."""
        from caylent_devcontainer_cli.utils.constants import CLI_NAME

        assert CLI_NAME == "Caylent Devcontainer CLI"

    def test_cli_module_uses_constants_cli_name(self):
        """Test that cli.py uses CLI_NAME from constants, not a local definition."""
        import caylent_devcontainer_cli.cli as cli_module
        from caylent_devcontainer_cli.utils.constants import CLI_NAME

        # The cli module should reference the same CLI_NAME from constants
        # After refactoring, cli.py should import CLI_NAME from constants
        assert hasattr(cli_module, "CLI_NAME") is False or cli_module.CLI_NAME == CLI_NAME
