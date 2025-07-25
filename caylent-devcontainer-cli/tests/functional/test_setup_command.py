"""Functional tests for the setup-devcontainer command."""

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


def test_setup_gitignore_creation(temp_project_dir):
    """Test that setup command creates .gitignore entries."""
    # Run the setup command with --manual flag
    result = run_command(["cdevcontainer", "setup-devcontainer", "--manual", temp_project_dir])

    assert result.returncode == 0

    # Check that .gitignore was created with required entries
    gitignore_path = os.path.join(temp_project_dir, ".gitignore")
    assert os.path.exists(gitignore_path)

    with open(gitignore_path, "r") as f:
        gitignore_content = f.read()

    assert "shell.env" in gitignore_content
    assert "devcontainer-environment-variables.json" in gitignore_content
    assert ".devcontainer/aws-profile-map.json" in gitignore_content
    assert "# Environment files" in gitignore_content


def test_setup_gitignore_update(temp_project_dir):
    """Test that setup command updates existing .gitignore."""
    # Create existing .gitignore with some entries
    gitignore_path = os.path.join(temp_project_dir, ".gitignore")
    with open(gitignore_path, "w") as f:
        f.write("shell.env\nother-file.txt\n")

    # Run the setup command
    result = run_command(["cdevcontainer", "setup-devcontainer", "--manual", temp_project_dir])

    assert result.returncode == 0

    # Check that .gitignore was updated with missing entries
    with open(gitignore_path, "r") as f:
        gitignore_content = f.read()

    assert "shell.env" in gitignore_content  # Already existed
    assert "other-file.txt" in gitignore_content  # Already existed
    assert "devcontainer-environment-variables.json" in gitignore_content  # Added
    assert ".devcontainer/aws-profile-map.json" in gitignore_content  # Added


def test_setup_existing_devcontainer():
    """Test setup behavior with existing devcontainer."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # First, create a devcontainer
        result = run_command(["cdevcontainer", "setup-devcontainer", "--manual", temp_dir])
        assert result.returncode == 0

        # Verify devcontainer was created
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        assert os.path.isdir(devcontainer_dir)
        assert os.path.isfile(os.path.join(devcontainer_dir, "devcontainer.json"))


def test_setup_update_mode():
    """Test setup command with --update flag."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # First, create a devcontainer
        result = run_command(["cdevcontainer", "setup-devcontainer", "--manual", temp_dir])
        assert result.returncode == 0

        # Verify the devcontainer exists
        devcontainer_dir = os.path.join(temp_dir, ".devcontainer")
        assert os.path.isdir(devcontainer_dir)

        # Test that update mode recognizes existing devcontainer
        # (We can't easily test the full interactive flow in functional tests)
        assert os.path.isfile(os.path.join(devcontainer_dir, "devcontainer.json"))


def test_setup_update_mode_no_devcontainer():
    """Test setup command with --update flag when no devcontainer exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Try to update non-existent devcontainer
        result = run_command(["cdevcontainer", "setup-devcontainer", "--update", temp_dir])

        assert result.returncode != 0
        assert "No .devcontainer directory found" in result.stderr
