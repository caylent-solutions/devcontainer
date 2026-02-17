"""Functional tests for code command file detection and source inspection (S1.3.2).

The missing variable validation is handled by S1.3.3 (Code Command Validation).
These tests verify the code command's file existence checks, IDE launch behavior,
source inspection (no-source pattern), and --regenerate-shell-env end-to-end.
"""

import inspect
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from caylent_devcontainer_cli.commands.code import handle_code
from caylent_devcontainer_cli.utils.validation import ValidationResult

# Helper: a no-issues validation result for tests that don't care about validation
_NO_ISSUES = ValidationResult(
    missing_base_keys={},
    metadata_present=True,
    template_name="test",
    template_path="/path/test.json",
    cli_version="2.0.0",
    template_found=True,
    validated_template={"containerEnv": {}},
    missing_template_keys={},
)

# =============================================================================
# File detection tests
# =============================================================================


def test_code_command_fails_when_shell_env_missing():
    """Test code command exits when shell.env is missing but JSON exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create environment file but NOT shell.env
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump({"containerEnv": {"EXISTING_VAR": "value"}}, f)

        with pytest.raises(SystemExit) as exc_info:
            args = type(
                "Args",
                (),
                {
                    "project_root": temp_dir,
                    "ide": "vscode",
                    "regenerate_shell_env": False,
                },
            )()
            handle_code(args)

        assert exc_info.value.code == 1


def test_code_command_launches_with_both_files():
    """Test code command launches IDE when both files exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create both required files
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump({"containerEnv": {"EXISTING_VAR": "value"}}, f)

        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export EXISTING_VAR=value\n")

        with (
            patch(
                "caylent_devcontainer_cli.commands.code.detect_validation_issues",
                return_value=_NO_ISSUES,
            ),
            patch("shutil.which", return_value="/usr/bin/code"),
            patch("subprocess.Popen") as mock_popen,
        ):
            mock_process = MagicMock()
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            args = type(
                "Args",
                (),
                {
                    "project_root": temp_dir,
                    "ide": "vscode",
                    "regenerate_shell_env": False,
                },
            )()
            handle_code(args)

            mock_popen.assert_called_once()


def test_code_command_launches_without_sourcing():
    """Test code command launches IDE without sourcing shell.env."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create both required files
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump({"containerEnv": {"TEST": "value"}}, f)

        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export TEST=value\n")

        with (
            patch(
                "caylent_devcontainer_cli.commands.code.detect_validation_issues",
                return_value=_NO_ISSUES,
            ),
            patch("shutil.which", return_value="/usr/bin/code"),
            patch("subprocess.Popen") as mock_popen,
        ):
            mock_process = MagicMock()
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            args = type(
                "Args",
                (),
                {
                    "project_root": temp_dir,
                    "ide": "vscode",
                    "regenerate_shell_env": False,
                },
            )()
            handle_code(args)

            # Verify the launch command is a list [ide_command, project_root]
            # — not a string with "source" in it
            cmd = mock_popen.call_args[0][0]
            assert isinstance(cmd, list)
            assert cmd == ["code", temp_dir]


# =============================================================================
# Source inspection tests — verify removed patterns stay removed
# =============================================================================


def test_handle_code_source_does_not_contain_source_keyword():
    """Verify handle_code() source does not contain 'source shell.env' pattern."""
    source = inspect.getsource(handle_code)
    assert "source " not in source, "handle_code must not source shell.env before launch"


def test_handle_code_source_does_not_call_write_project_files():
    """Verify handle_code() does not call write_project_files()."""
    source = inspect.getsource(handle_code)
    assert "write_project_files" not in source, "handle_code must not call write_project_files"


def test_handle_code_source_does_not_call_generate_shell_env():
    """Verify handle_code() does not call the old generate_shell_env() function."""
    source = inspect.getsource(handle_code)
    # The attribute regenerate_shell_env is expected; the old function call is not
    assert "generate_shell_env(" not in source, "handle_code must not call generate_shell_env()"


def test_handle_code_source_does_not_call_ensure_gitignore():
    """Verify handle_code() does not call ensure_gitignore_entries()."""
    source = inspect.getsource(handle_code)
    assert "ensure_gitignore" not in source, "handle_code must not call ensure_gitignore_entries"


def test_handle_code_source_does_not_call_getmtime():
    """Verify handle_code() does not use os.path.getmtime (staleness check removed)."""
    source = inspect.getsource(handle_code)
    assert "getmtime" not in source, "handle_code must not use getmtime for staleness checks"


def test_code_module_imports_write_project_files_for_validation():
    """Verify code.py imports write_project_files for validation Step 5."""
    import caylent_devcontainer_cli.commands.code as code_module

    # Check module namespace — handles both single-line and multi-line import formats
    assert hasattr(code_module, "write_project_files"), "code.py must import write_project_files for validation Step 5"


def test_code_module_imports_write_shell_env():
    """Verify code.py imports write_shell_env for --regenerate-shell-env."""
    import caylent_devcontainer_cli.commands.code as code_module

    # Check module namespace — handles both single-line and multi-line import formats
    assert hasattr(code_module, "write_shell_env"), "code.py must import write_shell_env"


# =============================================================================
# --regenerate-shell-env end-to-end test
# =============================================================================


def test_regenerate_shell_env_creates_shell_env_from_json():
    """End-to-end: --regenerate-shell-env reads JSON and writes shell.env."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create environment JSON with metadata
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump(
                {
                    "template_name": "test-template",
                    "template_path": "/templates/test-template.json",
                    "cli_version": "2.0.0",
                    "containerEnv": {
                        "DEVELOPER_NAME": "tester",
                        "GIT_USER": "testuser",
                        "HOST_PROXY": "false",
                    },
                },
                f,
            )

        # shell.env does NOT exist yet
        shell_env_path = os.path.join(temp_dir, "shell.env")
        assert not os.path.exists(shell_env_path)

        with (
            patch(
                "caylent_devcontainer_cli.commands.code.detect_validation_issues",
                return_value=_NO_ISSUES,
            ),
            patch("shutil.which", return_value="/usr/bin/code"),
            patch("subprocess.Popen") as mock_popen,
        ):
            mock_process = MagicMock()
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            args = type(
                "Args",
                (),
                {
                    "project_root": temp_dir,
                    "ide": "vscode",
                    "regenerate_shell_env": True,
                },
            )()
            handle_code(args)

        # Verify shell.env was created
        assert os.path.exists(shell_env_path), "shell.env should have been created"

        with open(shell_env_path, "r") as f:
            content = f.read()

        # Verify metadata header
        assert "# Template: test-template" in content
        assert "# CLI Version: 2.0.0" in content

        # Verify sorted exports
        assert "export DEVELOPER_NAME='tester'" in content
        assert "export GIT_USER='testuser'" in content

        # Verify static container values
        assert "export DEVCONTAINER='true'" in content
        assert "export BASH_ENV=" in content

        # Verify JSON was NOT modified
        with open(env_file, "r") as f:
            json_after = json.load(f)
        assert json_after["containerEnv"]["DEVELOPER_NAME"] == "tester"
        assert json_after["cli_version"] == "2.0.0"


def test_regenerate_shell_env_with_proxy_vars():
    """End-to-end: --regenerate-shell-env includes proxy vars when HOST_PROXY=true."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump(
                {
                    "template_name": "proxy-template",
                    "template_path": "/templates/proxy.json",
                    "cli_version": "2.0.0",
                    "containerEnv": {
                        "HOST_PROXY": "true",
                        "HOST_PROXY_URL": "http://proxy.example.com:8080",
                        "DEVELOPER_NAME": "tester",
                    },
                },
                f,
            )

        with (
            patch(
                "caylent_devcontainer_cli.commands.code.detect_validation_issues",
                return_value=_NO_ISSUES,
            ),
            patch("shutil.which", return_value="/usr/bin/code"),
            patch("subprocess.Popen") as mock_popen,
        ):
            mock_process = MagicMock()
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            args = type(
                "Args",
                (),
                {
                    "project_root": temp_dir,
                    "ide": "vscode",
                    "regenerate_shell_env": True,
                },
            )()
            handle_code(args)

        shell_env_path = os.path.join(temp_dir, "shell.env")
        with open(shell_env_path, "r") as f:
            content = f.read()

        # Verify proxy variables are present
        assert "export HTTP_PROXY='http://proxy.example.com:8080'" in content
        assert "export HTTPS_PROXY='http://proxy.example.com:8080'" in content
        assert "export http_proxy='http://proxy.example.com:8080'" in content
        assert "export https_proxy='http://proxy.example.com:8080'" in content
