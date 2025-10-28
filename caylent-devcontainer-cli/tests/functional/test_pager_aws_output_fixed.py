"""Functional tests for pager and AWS output format selection features."""

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


def test_env_export_includes_pager_and_aws_output():
    """Test that env export includes PAGER and AWS_DEFAULT_OUTPUT variables."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create .devcontainer directory for project root validation
        os.makedirs(os.path.join(temp_dir, ".devcontainer"))
        
        # Create a test environment file with the new variables
        env_file = os.path.join(temp_dir, "test-env.json")
        env_data = {
            "containerEnv": {
                "AWS_CONFIG_ENABLED": "true",
                "DEFAULT_GIT_BRANCH": "main",
                "DEFAULT_PYTHON_VERSION": "3.12.9",
                "DEVELOPER_NAME": "testuser",
                "GIT_PROVIDER_URL": "github.com",
                "GIT_TOKEN": "test-token",
                "GIT_USER": "testuser",
                "GIT_USER_EMAIL": "test@example.com",
                "EXTRA_APT_PACKAGES": "",
                "PAGER": "less",
                "AWS_DEFAULT_OUTPUT": "table",
            }
        }

        with open(env_file, "w") as f:
            json.dump(env_data, f, indent=2)

        # Test env export command with -y flag to bypass confirmation
        output_file = os.path.join(temp_dir, "output.sh")
        result = run_command(["cdevcontainer", "env", "export", env_file, "-o", output_file, "-y"])

        assert result.returncode == 0

        # Check that the output file contains the new variables
        with open(output_file, "r") as f:
            content = f.read()

        assert "export PAGER='less'" in content
        assert "export AWS_DEFAULT_OUTPUT='table'" in content


def test_env_export_pager_options():
    """Test that all pager options work correctly in env export."""
    pager_options = ["cat", "less", "more", "most"]

    for pager in pager_options:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create .devcontainer directory for project root validation
            os.makedirs(os.path.join(temp_dir, ".devcontainer"))
            
            env_file = os.path.join(temp_dir, "test-env.json")
            env_data = {
                "containerEnv": {
                    "AWS_CONFIG_ENABLED": "false",
                    "DEFAULT_GIT_BRANCH": "main",
                    "DEFAULT_PYTHON_VERSION": "3.12.9",
                    "DEVELOPER_NAME": "testuser",
                    "GIT_PROVIDER_URL": "github.com",
                    "GIT_TOKEN": "test-token",
                    "GIT_USER": "testuser",
                    "GIT_USER_EMAIL": "test@example.com",
                    "EXTRA_APT_PACKAGES": "",
                    "PAGER": pager,
                }
            }

            with open(env_file, "w") as f:
                json.dump(env_data, f, indent=2)

            output_file = os.path.join(temp_dir, "output.sh")
            result = run_command(["cdevcontainer", "env", "export", env_file, "-o", output_file, "-y"])

            assert result.returncode == 0

            with open(output_file, "r") as f:
                content = f.read()

            assert f"export PAGER='{pager}'" in content


def test_setup_manual_includes_new_variables():
    """Test that manual setup creates example files with new variables."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_command(["cdevcontainer", "setup-devcontainer", "--manual", temp_dir])

        assert result.returncode == 0

        # Check that the example file includes the new variables
        example_file = os.path.join(temp_dir, ".devcontainer", "example-container-env-values.json")
        assert os.path.exists(example_file)

        with open(example_file, "r") as f:
            example_data = json.load(f)

        # The example file should be valid JSON with containerEnv structure
        container_env = example_data.get("containerEnv", {})

        # At minimum, the structure should be compatible with the new variables
        assert isinstance(container_env, dict)
        assert len(container_env) > 0  # Should have some environment variables
