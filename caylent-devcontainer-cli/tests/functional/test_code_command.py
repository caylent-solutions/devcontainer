"""Functional tests for the code command with IDE support."""

import json
import os
import subprocess
import tempfile


def run_command(cmd, cwd=None, input_text=None):
    """Run a command and return the output."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        input=input_text.encode() if input_text else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result


def test_code_command_help():
    """Test the code command help."""
    result = run_command(["cdevcontainer", "code", "--help"])

    assert result.returncode == 0
    assert "--ide" in result.stdout
    assert "vscode" in result.stdout
    assert "cursor" in result.stdout
    assert "IDE to launch" in result.stdout
    assert "--regenerate-shell-env" in result.stdout


def test_code_command_missing_config():
    """Test code command with missing configuration file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .devcontainer directory to make it a valid project
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Run code command without environment file
        result = run_command(["cdevcontainer", "code", temp_dir])

        assert result.returncode != 0
        assert "devcontainer-environment-variables.json" in result.stderr
        assert "setup-devcontainer" in result.stderr or "template load" in result.stderr


def test_code_command_ide_not_found():
    """Test code command when IDE is not installed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create environment file with required variables
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump(
                {
                    "containerEnv": {
                        "AWS_CONFIG_ENABLED": "true",
                        "AWS_DEFAULT_OUTPUT": "json",
                        "DEFAULT_GIT_BRANCH": "main",
                        "DEFAULT_PYTHON_VERSION": "3.12.9",
                        "DEVELOPER_NAME": "test",
                        "EXTRA_APT_PACKAGES": "",
                        "GIT_AUTH_METHOD": "token",
                        "GIT_PROVIDER_URL": "github.com",
                        "GIT_TOKEN": "test",
                        "GIT_USER": "test",
                        "GIT_USER_EMAIL": "test@example.com",
                        "HOST_PROXY": "false",
                        "HOST_PROXY_URL": "",
                        "PAGER": "cat",
                        "TEST": "value",
                    }
                },
                f,
            )

        # Create shell.env to skip generation step
        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export TEST=value\n")

        # Create a directory with only cdevcontainer and python3 — no IDE commands.
        # The cdevcontainer shebang is #!/usr/bin/env python3, so python3 must
        # be discoverable in PATH for the script to execute.
        import shutil
        import sys

        isolated_dir = os.path.join(temp_dir, "isolated_bin")
        os.makedirs(isolated_dir)

        cdevcontainer_path = shutil.which("cdevcontainer")
        if cdevcontainer_path:
            shutil.copy2(cdevcontainer_path, os.path.join(isolated_dir, "cdevcontainer"))

        python_dir = os.path.dirname(sys.executable)

        env = os.environ.copy()
        env["PATH"] = isolated_dir + ":" + python_dir

        result = subprocess.run(
            ["cdevcontainer", "code", "--ide", "vscode", temp_dir],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        assert result.returncode != 0
        assert "not found in PATH" in result.stderr


def test_code_command_default_ide():
    """Test that code command defaults to vscode."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create environment file with required variables
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump(
                {
                    "containerEnv": {
                        "AWS_CONFIG_ENABLED": "true",
                        "AWS_DEFAULT_OUTPUT": "json",
                        "DEFAULT_GIT_BRANCH": "main",
                        "DEFAULT_PYTHON_VERSION": "3.12.9",
                        "DEVELOPER_NAME": "test",
                        "EXTRA_APT_PACKAGES": "",
                        "GIT_AUTH_METHOD": "token",
                        "GIT_PROVIDER_URL": "github.com",
                        "GIT_TOKEN": "test",
                        "GIT_USER": "test",
                        "GIT_USER_EMAIL": "test@example.com",
                        "HOST_PROXY": "false",
                        "HOST_PROXY_URL": "",
                        "PAGER": "cat",
                        "TEST": "value",
                    }
                },
                f,
            )

        # Create shell.env to skip generation step
        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export TEST=value\n")

        # Create a directory with only cdevcontainer and python3 — no IDE commands.
        # The cdevcontainer shebang is #!/usr/bin/env python3, so python3 must
        # be discoverable in PATH for the script to execute.
        import shutil
        import sys

        isolated_dir = os.path.join(temp_dir, "isolated_bin")
        os.makedirs(isolated_dir)

        cdevcontainer_path = shutil.which("cdevcontainer")
        if cdevcontainer_path:
            shutil.copy2(cdevcontainer_path, os.path.join(isolated_dir, "cdevcontainer"))

        python_dir = os.path.dirname(sys.executable)

        env = os.environ.copy()
        env["PATH"] = isolated_dir + ":" + python_dir

        result = subprocess.run(
            ["cdevcontainer", "code", temp_dir],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        assert result.returncode != 0
        assert "VS Code command 'code' not found" in result.stderr


def test_code_command_cursor_ide():
    """Test code command with cursor IDE."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create environment file with required variables
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump(
                {
                    "containerEnv": {
                        "AWS_CONFIG_ENABLED": "true",
                        "AWS_DEFAULT_OUTPUT": "json",
                        "DEFAULT_GIT_BRANCH": "main",
                        "DEFAULT_PYTHON_VERSION": "3.12.9",
                        "DEVELOPER_NAME": "test",
                        "EXTRA_APT_PACKAGES": "",
                        "GIT_AUTH_METHOD": "token",
                        "GIT_PROVIDER_URL": "github.com",
                        "GIT_TOKEN": "test",
                        "GIT_USER": "test",
                        "GIT_USER_EMAIL": "test@example.com",
                        "HOST_PROXY": "false",
                        "HOST_PROXY_URL": "",
                        "PAGER": "cat",
                        "TEST": "value",
                    }
                },
                f,
            )

        # Create shell.env to skip generation step
        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export TEST=value\n")

        # Create empty directory and put it first in PATH
        empty_dir = os.path.join(temp_dir, "empty")
        os.makedirs(empty_dir)

        env = os.environ.copy()
        env["PATH"] = empty_dir + ":" + env.get("PATH", "")

        result = subprocess.run(
            ["cdevcontainer", "code", "--ide", "cursor", temp_dir],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        assert result.returncode != 0
        assert "Cursor command 'cursor' not found" in result.stderr


def test_code_command_launches_ide():
    """Test that code command launches the IDE when both files exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create environment file
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump({"containerEnv": {"TEST": "value"}}, f)

        # Create shell.env
        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export TEST=value\n")

        # Create a fake IDE command
        fake_ide_dir = os.path.join(temp_dir, "fake_bin")
        os.makedirs(fake_ide_dir)
        fake_code = os.path.join(fake_ide_dir, "code")
        with open(fake_code, "w") as f:
            f.write("#!/bin/bash\necho 'fake code launched'\n")
        os.chmod(fake_code, 0o755)

        env = os.environ.copy()
        env["PATH"] = fake_ide_dir + ":" + env.get("PATH", "")

        result = subprocess.run(
            ["cdevcontainer", "code", temp_dir],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        assert result.returncode == 0
        assert "launched" in result.stderr


def test_code_command_missing_shell_env():
    """Test code command fails when shell.env is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create only the JSON file — no shell.env
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump({"containerEnv": {"TEST": "value"}}, f)

        result = run_command(["cdevcontainer", "code", temp_dir])

        assert result.returncode != 0
        assert "shell.env" in result.stderr
        assert "setup-devcontainer" in result.stderr or "template load" in result.stderr


def test_code_command_regenerate_shell_env():
    """Test --regenerate-shell-env creates shell.env and launches IDE."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Create environment JSON
        env_file = os.path.join(temp_dir, "devcontainer-environment-variables.json")
        with open(env_file, "w") as f:
            json.dump(
                {
                    "template_name": "test",
                    "template_path": "/templates/test.json",
                    "cli_version": "2.0.0",
                    "containerEnv": {"DEVELOPER_NAME": "tester", "HOST_PROXY": "false"},
                },
                f,
            )

        # Create a fake IDE command
        fake_ide_dir = os.path.join(temp_dir, "fake_bin")
        os.makedirs(fake_ide_dir)
        fake_code = os.path.join(fake_ide_dir, "code")
        with open(fake_code, "w") as f:
            f.write("#!/bin/bash\necho 'fake code launched'\n")
        os.chmod(fake_code, 0o755)

        env = os.environ.copy()
        env["PATH"] = fake_ide_dir + ":" + env.get("PATH", "")

        result = subprocess.run(
            ["cdevcontainer", "code", "--regenerate-shell-env", temp_dir],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        assert result.returncode == 0
        assert "Regenerated shell.env" in result.stderr
        assert "launched" in result.stderr

        # Verify shell.env was created
        shell_env_path = os.path.join(temp_dir, "shell.env")
        assert os.path.exists(shell_env_path)

        with open(shell_env_path, "r") as f:
            content = f.read()
        assert "export DEVELOPER_NAME='tester'" in content


def test_code_command_regenerate_requires_json():
    """Test --regenerate-shell-env fails if JSON is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .devcontainer directory
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # No JSON file
        result = run_command(["cdevcontainer", "code", "--regenerate-shell-env", temp_dir])

        assert result.returncode != 0
        assert "devcontainer-environment-variables.json" in result.stderr
