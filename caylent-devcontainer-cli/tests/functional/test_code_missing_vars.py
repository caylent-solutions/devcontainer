"""Functional tests for missing variable detection in code command."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from caylent_devcontainer_cli.commands.code import handle_code


def test_code_command_missing_vars_exit():
    """Test code command exits when user chooses to upgrade missing variables."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create environment file missing required variables
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump({"containerEnv": {"EXISTING_VAR": "value"}}, f)

        # Mock user choosing to exit and upgrade
        with patch("questionary.select") as mock_select, pytest.raises(SystemExit) as exc_info:
            mock_select.return_value.ask.return_value = "Exit and upgrade the profile first (recommended)"

            args = type("Args", (), {"project_root": temp_dir, "ide": "vscode"})()

            handle_code(args)

        assert exc_info.value.code == 0


def test_code_command_missing_vars_continue():
    """Test code command continues when user chooses to ignore missing variables."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create environment file missing required variables
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump({"containerEnv": {"EXISTING_VAR": "value"}}, f)

        # Create shell.env to skip generation
        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export EXISTING_VAR=value\n")

        # Mock user choosing to continue and mock IDE launch
        with (
            patch("questionary.select") as mock_select,
            patch("shutil.which", return_value="/usr/bin/code"),
            patch("subprocess.Popen") as mock_popen,
            patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries"),
        ):
            mock_select.return_value.ask.return_value = "Continue without the upgrade (may cause issues)"
            mock_process = MagicMock()
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            args = type("Args", (), {"project_root": temp_dir, "ide": "vscode"})()

            handle_code(args)

            # Verify IDE was launched despite missing variables
            mock_popen.assert_called_once()


def test_code_command_no_missing_vars():
    """Test code command works normally when no variables are missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create environment file with all required variables
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump(
                {
                    "containerEnv": {
                        "AWS_CONFIG_ENABLED": "true",
                        "AWS_DEFAULT_OUTPUT": "json",
                        "CICD": "false",
                        "DEFAULT_GIT_BRANCH": "main",
                        "DEFAULT_PYTHON_VERSION": "3.12.9",
                        "DEVELOPER_NAME": "test",
                        "EXTRA_APT_PACKAGES": "",
                        "GIT_PROVIDER_URL": "github.com",
                        "GIT_TOKEN": "test",
                        "GIT_USER": "test",
                        "GIT_USER_EMAIL": "test@example.com",
                        "PAGER": "cat",
                    }
                },
                f,
            )

        # Create shell.env to skip generation
        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export TEST=value\n")

        # Mock IDE launch - no missing variable prompts should appear
        with (
            patch("shutil.which", return_value="/usr/bin/code"),
            patch("subprocess.Popen") as mock_popen,
            patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries"),
            patch("questionary.select") as mock_select,
        ):
            mock_process = MagicMock()
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            args = type("Args", (), {"project_root": temp_dir, "ide": "vscode"})()

            handle_code(args)

            # Verify no missing variable prompts appeared
            mock_select.assert_not_called()
            # Verify IDE was launched normally
            mock_popen.assert_called_once()
