#!/usr/bin/env python3
import json
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ENTRY_FILENAME,
    ENV_VARS_FILENAME,
    EXAMPLE_AWS_FILE,
    EXAMPLE_ENV_FILE,
    SHELL_ENV_FILENAME,
    SSH_KEY_FILENAME,
)
from caylent_devcontainer_cli.utils.fs import (
    find_project_root,
    generate_exports,
    generate_shell_env,
    load_json_config,
    remove_example_files,
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
    with patch("builtins.open", side_effect=FileNotFoundError()), patch("caylent_devcontainer_cli.utils.fs.log"), patch(
        "sys.exit", side_effect=SystemExit(1)
    ) as mock_exit:
        with pytest.raises(SystemExit):
            load_json_config("/test/path/nonexistent.json")
        mock_exit.assert_called_once_with(1)


def test_generate_exports():
    env_dict = {"TEST_VAR": "test_value", "TEST_JSON": {"key": "value"}, "TEST_LIST": [1, 2, 3]}

    # Test with export_prefix=True
    lines = generate_exports(env_dict, export_prefix=True)
    assert len(lines) == 3
    assert "export TEST_VAR='test_value'" in lines
    assert "export TEST_JSON='" in lines[1]
    assert "export TEST_LIST='" in lines[2]

    # Test with export_prefix=False
    lines = generate_exports(env_dict, export_prefix=False)
    assert len(lines) == 3
    assert "TEST_VAR='test_value'" in lines
    assert "TEST_JSON='" in lines[1]
    assert "TEST_LIST='" in lines[2]


def test_generate_exports_with_special_chars():
    """Test generating exports with values containing special characters."""
    env_values = {
        "NORMAL_VALUE": "simple",
        "QUOTED_VALUE": "value with spaces",
        "SPECIAL_CHARS": 'value with $pecial & "chars"',
    }

    exports = generate_exports(env_values)

    assert len(exports) == 3
    assert any("NORMAL_VALUE='simple'" in e for e in exports)
    assert any("QUOTED_VALUE='value with spaces'" in e for e in exports)
    assert any("SPECIAL_CHARS='value with $pecial & \"chars\"'" in e for e in exports)


@patch(
    "caylent_devcontainer_cli.utils.fs.load_json_config",
    return_value={"containerEnv": {"TEST_VAR": "test_value"}, "cli_version": "1.0.0"},
)
@patch("os.path.exists", return_value=False)
@patch("caylent_devcontainer_cli.utils.fs.confirm_action", return_value=True)
@patch("caylent_devcontainer_cli.utils.fs.find_project_root", return_value="/test/project")
def test_generate_shell_env(mock_find_root, mock_confirm, mock_exists, mock_load_json):
    with patch("builtins.open", mock_open()) as mock_file:
        generate_shell_env("test_file.json", "output_file.sh")
        mock_file().write.assert_called()


@patch("os.path.exists", return_value=False)
@patch("caylent_devcontainer_cli.utils.fs.load_json_config", return_value={"invalid": []})
@patch("caylent_devcontainer_cli.utils.fs.confirm_action", return_value=True)
def test_generate_shell_env_invalid_json(mock_confirm, mock_load_json, mock_exists):
    with pytest.raises(SystemExit):
        generate_shell_env("test_file.json", "output_file.sh")


def test_generate_shell_env_confirmation_cancel():
    """Test generate_shell_env when user cancels confirmation."""
    with patch(
        "caylent_devcontainer_cli.utils.fs.load_json_config",
        return_value={"containerEnv": {"TEST": "value"}, "cli_version": "1.0.0"},
    ):
        with patch("os.path.exists", return_value=True):
            with patch("caylent_devcontainer_cli.utils.fs.confirm_action", return_value=False):
                with pytest.raises(SystemExit):
                    generate_shell_env("/test/input.json", "/test/output.env")


def test_generate_shell_env_new_file():
    """Test generate_shell_env when creating a new file."""
    with patch(
        "caylent_devcontainer_cli.utils.fs.load_json_config",
        return_value={"containerEnv": {"TEST": "value"}, "cli_version": "1.0.0"},
    ):
        with patch("os.path.exists", return_value=False):
            with patch("caylent_devcontainer_cli.utils.fs.confirm_action", return_value=True):
                with patch("caylent_devcontainer_cli.utils.fs.find_project_root", return_value="/test/project"):
                    with patch("builtins.open", MagicMock()):
                        generate_shell_env("/test/input.json", "/test/output.env")


def test_generate_shell_env_includes_cli_version():
    """Test that generate_shell_env includes CLI_VERSION from cli_version field."""
    test_data = {"containerEnv": {"TEST_VAR": "test_value"}, "cli_version": "1.5.0"}

    with patch("caylent_devcontainer_cli.utils.fs.load_json_config", return_value=test_data):
        with patch("os.path.exists", return_value=False):
            with patch("caylent_devcontainer_cli.utils.fs.confirm_action", return_value=True):
                with patch("caylent_devcontainer_cli.utils.fs.find_project_root", return_value="/test/project"):
                    with patch("builtins.open", mock_open()) as mock_file:
                        generate_shell_env("/test/input.json", "/test/output.env")

                        # Get the written content
                        written_content = mock_file().write.call_args[0][0]

                        # Verify both TEST_VAR and CLI_VERSION are included
                        assert "export TEST_VAR='test_value'" in written_content
                        assert "export CLI_VERSION='1.5.0'" in written_content


def test_generate_shell_env_without_cli_version():
    """Test that generate_shell_env works when cli_version is not present."""
    test_data = {"containerEnv": {"TEST_VAR": "test_value"}}

    with patch("caylent_devcontainer_cli.utils.fs.load_json_config", return_value=test_data):
        with patch("os.path.exists", return_value=False):
            with patch("caylent_devcontainer_cli.utils.fs.confirm_action", return_value=True):
                with patch("caylent_devcontainer_cli.utils.fs.find_project_root", return_value="/test/project"):
                    with patch("builtins.open", mock_open()) as mock_file:
                        generate_shell_env("/test/input.json", "/test/output.env")

                        # Get the written content
                        written_content = mock_file().write.call_args[0][0]

                        # Verify TEST_VAR is included but CLI_VERSION is not
                        assert "export TEST_VAR='test_value'" in written_content
                        assert "CLI_VERSION" not in written_content


@patch("os.path.isdir", return_value=True)
def test_find_project_root(mock_isdir):
    result = find_project_root("/test/path")
    assert result == "/test/path"
    mock_isdir.assert_called_with("/test/path/.devcontainer")


@patch("os.path.isdir", return_value=False)
def test_find_project_root_invalid(mock_isdir):
    with pytest.raises(SystemExit):
        find_project_root("/test/path")


@patch("os.path.isfile", return_value=True)
@patch("os.path.isdir", return_value=True)
@patch("os.path.dirname", return_value="/test")
def test_find_project_root_file(mock_dirname, mock_isdir, mock_isfile):
    result = find_project_root("/test/file.txt")
    assert result == "/test"
    mock_isfile.assert_called_with("/test/file.txt")
    mock_dirname.assert_called_with("/test/file.txt")
    mock_isdir.assert_called_with("/test/.devcontainer")


def test_find_project_root_with_git_dir():
    """Test finding project root with .devcontainer directory."""
    with patch("os.path.isdir", return_value=True):
        result = find_project_root("/test/path/subdir")
        assert result == "/test/path/subdir"


def test_find_project_root_with_path():
    """Test find_project_root with a provided path."""
    with patch("os.path.isdir", return_value=True):
        result = find_project_root("/test/path")
        assert result == "/test/path"


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
                "DEFAULT_PYTHON_VERSION": "3.12.9",
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
# remove_example_files tests
# =============================================================================


class TestRemoveExampleFiles:
    """Tests for remove_example_files utility."""

    def test_removes_both_example_files(self, tmp_path):
        """Test that both example files are removed."""
        devcontainer_dir = tmp_path / ".devcontainer"
        devcontainer_dir.mkdir()

        example_env = devcontainer_dir / "example-container-env-values.json"
        example_aws = devcontainer_dir / "example-aws-profile-map.json"
        example_env.write_text("{}")
        example_aws.write_text("{}")

        remove_example_files(str(devcontainer_dir))

        assert not example_env.exists()
        assert not example_aws.exists()

    def test_handles_missing_files_gracefully(self, tmp_path):
        """Test that no error occurs when example files don't exist."""
        devcontainer_dir = tmp_path / ".devcontainer"
        devcontainer_dir.mkdir()

        # Should not raise any exception
        remove_example_files(str(devcontainer_dir))

    def test_handles_partial_files(self, tmp_path):
        """Test removal when only one example file exists."""
        devcontainer_dir = tmp_path / ".devcontainer"
        devcontainer_dir.mkdir()

        example_env = devcontainer_dir / "example-container-env-values.json"
        example_env.write_text("{}")

        remove_example_files(str(devcontainer_dir))

        assert not example_env.exists()

    def test_does_not_remove_other_files(self, tmp_path):
        """Test that non-example files are not removed."""
        devcontainer_dir = tmp_path / ".devcontainer"
        devcontainer_dir.mkdir()

        other_file = devcontainer_dir / "devcontainer.json"
        other_file.write_text("{}")

        example_env = devcontainer_dir / "example-container-env-values.json"
        example_env.write_text("{}")

        remove_example_files(str(devcontainer_dir))

        assert other_file.exists()
        assert not example_env.exists()


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

    def test_example_env_file(self):
        """Test EXAMPLE_ENV_FILE constant value."""
        assert EXAMPLE_ENV_FILE == "example-container-env-values.json"

    def test_example_aws_file(self):
        """Test EXAMPLE_AWS_FILE constant value."""
        assert EXAMPLE_AWS_FILE == "example-aws-profile-map.json"

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
        with patch("os.path.isfile", return_value=True), patch("os.path.dirname", return_value="/my/project"), patch(
            "os.path.isdir", return_value=True
        ):
            result = resolve_project_root("/my/project/file.json")
            assert result == "/my/project"

    def test_exits_with_clear_error_on_invalid_path(self):
        """Test that resolve_project_root exits with a clear error message."""
        with patch("os.path.isdir", return_value=False), patch("os.path.isfile", return_value=False), patch(
            "caylent_devcontainer_cli.utils.fs.log"
        ) as mock_log, patch(
            "caylent_devcontainer_cli.utils.fs.exit_with_error", side_effect=SystemExit(1)
        ) as mock_exit_error:
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
