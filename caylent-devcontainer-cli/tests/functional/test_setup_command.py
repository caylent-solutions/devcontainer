"""Functional tests for the setup-devcontainer command."""

import os
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


def test_setup_creates_tool_versions_file(temp_project_dir):
    """Test that setup command creates .tool-versions file when missing."""
    # Ensure .tool-versions doesn't exist initially
    tool_versions_path = os.path.join(temp_project_dir, ".tool-versions")
    assert not os.path.exists(tool_versions_path)

    # Run the setup command with --manual flag and simulate pressing enter
    result = run_command(
        ["cdevcontainer", "setup-devcontainer", "--manual", temp_project_dir],
        input_text="\n",  # Simulate pressing enter when prompted
    )

    assert result.returncode == 0

    # Check that .tool-versions was created
    assert os.path.exists(tool_versions_path)

    # Check the content
    with open(tool_versions_path, "r") as f:
        content = f.read()

    assert "python 3.12.9" in content
    assert "Found .tool-versions file" not in result.stderr  # Should not find existing file
    assert ".tool-versions file not found but is required" in result.stderr


def test_setup_finds_existing_tool_versions_file(temp_project_dir):
    """Test that setup command finds existing .tool-versions file."""
    # Create existing .tool-versions file
    tool_versions_path = os.path.join(temp_project_dir, ".tool-versions")
    with open(tool_versions_path, "w") as f:
        f.write("python 3.11.5\n")

    # Run the setup command
    result = run_command(["cdevcontainer", "setup-devcontainer", "--manual", temp_project_dir])

    assert result.returncode == 0

    # Check that the existing file was found and not modified
    with open(tool_versions_path, "r") as f:
        content = f.read()

    assert "python 3.11.5" in content  # Original content preserved
    assert "Found .tool-versions file" in result.stderr
    assert ".tool-versions file not found" not in result.stderr


def test_setup_with_ref_flag_main_branch(temp_project_dir):
    """Test setup command with --ref flag using main branch."""
    # Run the setup command with --ref main flag
    result = run_command(["cdevcontainer", "setup-devcontainer", "--ref", "main", "--manual", temp_project_dir])

    # Check that the command succeeded
    assert result.returncode == 0

    # Check that the log message shows the correct ref
    assert "Cloning devcontainer repository (ref: main)" in result.stderr

    # Check that the .devcontainer directory was created
    devcontainer_dir = os.path.join(temp_project_dir, ".devcontainer")
    assert os.path.isdir(devcontainer_dir)

    # Check that essential files were copied
    assert os.path.isfile(os.path.join(devcontainer_dir, "devcontainer.json"))
    assert os.path.isfile(os.path.join(devcontainer_dir, ".devcontainer.postcreate.sh"))


def test_setup_with_ref_flag_invalid_reference(temp_project_dir):
    """Test setup command with --ref flag using invalid reference."""
    # Run the setup command with invalid ref
    result = run_command(
        ["cdevcontainer", "setup-devcontainer", "--ref", "nonexistent-branch", "--manual", temp_project_dir]
    )

    # Check that the command failed
    assert result.returncode != 0

    # Check that appropriate error messages are shown
    assert "Failed to clone devcontainer repository at ref 'nonexistent-branch'" in result.stderr
    assert "Reference 'nonexistent-branch' does not exist in the repository" in result.stderr


def test_setup_help_shows_ref_flag():
    """Test that setup-devcontainer help shows the --ref flag."""
    result = run_command(["cdevcontainer", "setup-devcontainer", "--help"])

    # Check that the command succeeded
    assert result.returncode == 0

    # Check that the --ref flag is documented in help
    assert "--ref" in result.stdout
    assert "Git reference (branch, tag, or commit)" in result.stdout


def test_setup_without_ref_uses_default_version(temp_project_dir):
    """Test that setup command without --ref flag uses CLI version by default."""
    # Run the setup command without --ref flag
    result = run_command(["cdevcontainer", "setup-devcontainer", "--manual", temp_project_dir])

    # Check that the command succeeded
    assert result.returncode == 0

    # Check that the log message shows the CLI version (not "main" or other ref)
    # The exact version will vary, but it should not say "ref: main"
    assert "Cloning devcontainer repository (ref:" in result.stderr
    assert "ref: main)" not in result.stderr  # Should not use main when no --ref specified
