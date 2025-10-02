"""Functional tests for the setup-devcontainer command with VERSION file."""

import os
import subprocess


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


def test_setup_creates_version_file(temp_project_dir):
    """Test that setup-devcontainer creates a VERSION file."""
    # Run the setup command in manual mode
    result = run_command(["cdevcontainer", "setup-devcontainer", "--manual", temp_project_dir])

    # Check that the command succeeded
    assert result.returncode == 0

    # Check that the VERSION file was created
    version_file = os.path.join(temp_project_dir, ".devcontainer", "VERSION")
    assert os.path.isfile(version_file)

    # Check that the VERSION file contains a version string
    with open(version_file, "r") as f:
        version = f.read().strip()

    assert version, "VERSION file should not be empty"
    assert "." in version, "VERSION should be in semver format"
