"""Functional tests for the Caylent Devcontainer CLI."""

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


def test_help_command():
    """Test the help command."""
    result = run_command(["cdevcontainer", "--help"])

    # Check that the command succeeded
    assert result.returncode == 0

    # Check that the output contains expected commands
    assert "setup-devcontainer" in result.stdout
    assert "code" in result.stdout
    assert "template" in result.stdout


def test_version_command():
    """Test the version command."""
    result = run_command(["cdevcontainer", "--version"])

    # Check that the command succeeded
    assert result.returncode == 0

    # Check that the output contains a version number
    assert "Caylent Devcontainer CLI" in result.stdout


def test_setup_manual_mode(temp_project_dir):
    """Test the setup-devcontainer command in manual mode."""
    # Run the setup command with --manual flag
    result = run_command(["cdevcontainer", "setup-devcontainer", "--manual", temp_project_dir])

    # Check that the command succeeded
    assert result.returncode == 0

    # Check that the .devcontainer directory was created
    devcontainer_dir = os.path.join(temp_project_dir, ".devcontainer")
    assert os.path.isdir(devcontainer_dir)

    # Check that essential files were copied
    assert os.path.isfile(os.path.join(devcontainer_dir, "devcontainer.json"))
    assert os.path.isfile(os.path.join(devcontainer_dir, ".devcontainer.postcreate.sh"))
    assert os.path.isfile(os.path.join(devcontainer_dir, "example-container-env-values.json"))


def test_invalid_command():
    """Test an invalid command."""
    result = run_command(["cdevcontainer", "invalid-command"])

    # Check that the command failed
    assert result.returncode != 0

    # Check that the error message is helpful
    assert "usage:" in result.stderr


def test_template_load_nonexistent():
    """Test loading a nonexistent template."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Run the template load command with a nonexistent template
        result = run_command(["cdevcontainer", "template", "load", "nonexistent-template"], cwd=temp_dir)

        # Check that the command failed
        assert result.returncode != 0

        # Check that the error message is helpful
        assert "not found" in result.stderr


def test_setup_devcontainer_invalid_path():
    """Test setup-devcontainer with an invalid path."""
    # Run the setup-devcontainer command with a nonexistent path
    result = run_command(["cdevcontainer", "setup-devcontainer", "/path/that/does/not/exist"])

    # Check that the command failed
    assert result.returncode != 0

    # Check that the error message is helpful
    assert "not exist" in result.stderr or "not a directory" in result.stderr
