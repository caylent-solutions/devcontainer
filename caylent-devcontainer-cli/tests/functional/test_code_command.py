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


def test_code_command_missing_config():
    """Test code command with missing configuration file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .devcontainer directory to make it a valid project
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        # Run code command without environment file
        result = run_command(["cdevcontainer", "code", temp_dir])

        assert result.returncode != 0
        assert "Configuration file not found" in result.stderr
        assert "devcontainer-environment-variables.json" in result.stderr


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
                        "CICD": "false",
                        "DEFAULT_GIT_BRANCH": "main",
                        "DEFAULT_PYTHON_VERSION": "3.12.9",
                        "DEVELOPER_NAME": "test",
                        "GIT_PROVIDER_URL": "github.com",
                        "GIT_USER": "test",
                        "GIT_USER_EMAIL": "test@example.com",
                        "GIT_TOKEN": "test",
                        "EXTRA_APT_PACKAGES": "",
                        "PAGER": "cat",
                        "AWS_DEFAULT_OUTPUT": "json",
                        "TEST": "value",
                    }
                },
                f,
            )

        # Create shell.env to skip generation step
        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export TEST=value\n")

        # Create empty directory and use only it in PATH
        empty_dir = os.path.join(temp_dir, "empty")
        os.makedirs(empty_dir)

        # Add cdevcontainer to the empty directory so the CLI can run
        import shutil

        cdevcontainer_path = shutil.which("cdevcontainer")
        if cdevcontainer_path:
            fake_cdevcontainer = os.path.join(empty_dir, "cdevcontainer")
            shutil.copy2(cdevcontainer_path, fake_cdevcontainer)

        env = os.environ.copy()
        env["PATH"] = empty_dir

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
                        "CICD": "false",
                        "DEFAULT_GIT_BRANCH": "main",
                        "DEFAULT_PYTHON_VERSION": "3.12.9",
                        "DEVELOPER_NAME": "test",
                        "GIT_PROVIDER_URL": "github.com",
                        "GIT_USER": "test",
                        "GIT_USER_EMAIL": "test@example.com",
                        "GIT_TOKEN": "test",
                        "EXTRA_APT_PACKAGES": "",
                        "PAGER": "cat",
                        "AWS_DEFAULT_OUTPUT": "json",
                        "TEST": "value",
                    }
                },
                f,
            )

        # Create shell.env to skip generation step
        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export TEST=value\n")

        # Create empty directory and use only it in PATH
        empty_dir = os.path.join(temp_dir, "empty")
        os.makedirs(empty_dir)

        # Add cdevcontainer to the empty directory so the CLI can run
        import shutil

        cdevcontainer_path = shutil.which("cdevcontainer")
        if cdevcontainer_path:
            fake_cdevcontainer = os.path.join(empty_dir, "cdevcontainer")
            shutil.copy2(cdevcontainer_path, fake_cdevcontainer)

        env = os.environ.copy()
        env["PATH"] = empty_dir

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
                        "CICD": "false",
                        "DEFAULT_GIT_BRANCH": "main",
                        "DEFAULT_PYTHON_VERSION": "3.12.9",
                        "DEVELOPER_NAME": "test",
                        "GIT_PROVIDER_URL": "github.com",
                        "GIT_USER": "test",
                        "GIT_USER_EMAIL": "test@example.com",
                        "GIT_TOKEN": "test",
                        "EXTRA_APT_PACKAGES": "",
                        "PAGER": "cat",
                        "AWS_DEFAULT_OUTPUT": "json",
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


def test_code_command_gitignore_creation():
    """Test that code command creates .gitignore entries."""
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
                        "CICD": "false",
                        "DEFAULT_GIT_BRANCH": "main",
                        "DEFAULT_PYTHON_VERSION": "3.12.9",
                        "DEVELOPER_NAME": "test",
                        "GIT_PROVIDER_URL": "github.com",
                        "GIT_USER": "test",
                        "GIT_USER_EMAIL": "test@example.com",
                        "GIT_TOKEN": "test",
                        "EXTRA_APT_PACKAGES": "",
                        "PAGER": "cat",
                        "AWS_DEFAULT_OUTPUT": "json",
                        "TEST": "value",
                    }
                },
                f,
            )

        # Create shell.env to skip generation step
        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export TEST=value\n")

        # Create a fake IDE command that will succeed
        fake_ide_dir = os.path.join(temp_dir, "fake_bin")
        os.makedirs(fake_ide_dir)
        fake_code = os.path.join(fake_ide_dir, "code")
        with open(fake_code, "w") as f:
            f.write("#!/bin/bash\necho 'fake code launched'\n")
        os.chmod(fake_code, 0o755)

        # Run code command with fake IDE in PATH
        env = os.environ.copy()
        env["PATH"] = fake_ide_dir + ":" + env.get("PATH", "")

        result = subprocess.run(
            ["cdevcontainer", "code", temp_dir],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Command should succeed
        assert result.returncode == 0

        # Check that .gitignore was created with required entries
        gitignore_path = os.path.join(temp_dir, ".gitignore")
        assert os.path.exists(gitignore_path)

        with open(gitignore_path, "r") as f:
            gitignore_content = f.read()

        assert "shell.env" in gitignore_content
        assert "devcontainer-environment-variables.json" in gitignore_content
        assert ".devcontainer/aws-profile-map.json" in gitignore_content
        assert "# Environment files" in gitignore_content


def test_code_command_gitignore_update():
    """Test that code command updates existing .gitignore."""
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
                        "CICD": "false",
                        "DEFAULT_GIT_BRANCH": "main",
                        "DEFAULT_PYTHON_VERSION": "3.12.9",
                        "DEVELOPER_NAME": "test",
                        "GIT_PROVIDER_URL": "github.com",
                        "GIT_USER": "test",
                        "GIT_USER_EMAIL": "test@example.com",
                        "GIT_TOKEN": "test",
                        "EXTRA_APT_PACKAGES": "",
                        "PAGER": "cat",
                        "AWS_DEFAULT_OUTPUT": "json",
                        "TEST": "value",
                    }
                },
                f,
            )

        # Create shell.env to skip generation step
        shell_env = os.path.join(temp_dir, "shell.env")
        with open(shell_env, "w") as f:
            f.write("export TEST=value\n")

        # Create existing .gitignore with some entries
        gitignore_path = os.path.join(temp_dir, ".gitignore")
        with open(gitignore_path, "w") as f:
            f.write("shell.env\nother-file.txt\n")

        # Create a fake IDE command
        fake_ide_dir = os.path.join(temp_dir, "fake_bin")
        os.makedirs(fake_ide_dir)
        fake_code = os.path.join(fake_ide_dir, "code")
        with open(fake_code, "w") as f:
            f.write("#!/bin/bash\necho 'fake code launched'\n")
        os.chmod(fake_code, 0o755)

        # Run code command
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

        # Check that .gitignore was updated with missing entries
        with open(gitignore_path, "r") as f:
            gitignore_content = f.read()

        assert "shell.env" in gitignore_content  # Already existed
        assert "other-file.txt" in gitignore_content  # Already existed
        assert "devcontainer-environment-variables.json" in gitignore_content  # Added
        assert ".devcontainer/aws-profile-map.json" in gitignore_content  # Added

        # Should show update message in stderr
        assert "Updated .gitignore with" in result.stderr
