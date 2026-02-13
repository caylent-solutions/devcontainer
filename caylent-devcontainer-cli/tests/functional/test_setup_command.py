"""Functional tests for the setup-devcontainer command."""

import subprocess
import tempfile


def run_command(cmd, cwd=None, input_text=None):
    """Run a command and return the output."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result


def test_help_command():
    """Test the help command."""
    result = run_command(["cdevcontainer", "--help"])

    assert result.returncode == 0
    assert "setup-devcontainer" in result.stdout
    assert "code" in result.stdout
    assert "template" in result.stdout


def test_version_command():
    """Test the version command."""
    result = run_command(["cdevcontainer", "--version"])

    assert result.returncode == 0
    assert "Caylent Devcontainer CLI" in result.stdout


def test_setup_help_shows_path_arg():
    """Test that setup-devcontainer help shows the path argument."""
    result = run_command(["cdevcontainer", "setup-devcontainer", "--help"])

    assert result.returncode == 0
    assert "path" in result.stdout

    # --manual and --ref should NOT appear in help (removed)
    assert "--manual" not in result.stdout
    assert "--ref" not in result.stdout


def test_setup_invalid_path():
    """Test setup-devcontainer with an invalid path."""
    result = run_command(["cdevcontainer", "setup-devcontainer", "/path/that/does/not/exist"])

    assert result.returncode != 0
    assert "not exist" in result.stderr or "not a directory" in result.stderr


def test_setup_rejects_removed_flags():
    """Test that --manual and --ref flags are rejected."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command(["cdevcontainer", "setup-devcontainer", "--manual", temp_dir])
        assert result.returncode == 2
        assert "unrecognized arguments" in result.stderr

        result = run_command(["cdevcontainer", "setup-devcontainer", "--ref", "main", temp_dir])
        assert result.returncode == 2
        assert "unrecognized arguments" in result.stderr
