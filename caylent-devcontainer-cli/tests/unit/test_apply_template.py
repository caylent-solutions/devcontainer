#!/usr/bin/env python3
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.setup_interactive import apply_template


def test_apply_template_with_container_env():
    """Test applying a template with containerEnv format."""
    template_data = {
        "containerEnv": {
            "AWS_CONFIG_ENABLED": "true",
            "DEFAULT_GIT_BRANCH": "main",
        },
        "aws_profile_map": {"default": {"region": "us-west-2"}},
    }

    with patch("caylent_devcontainer_cli.commands.setup_interactive.write_project_files") as mock_write:
        apply_template(template_data, "/target/path")

    mock_write.assert_called_once()
    call_args = mock_write.call_args
    assert call_args[0][0] == "/target/path"
    assert call_args[0][1] == template_data


def test_apply_template_with_env_values():
    """Test applying a template with env_values format (old format)."""
    template_data = {
        "env_values": {
            "AWS_CONFIG_ENABLED": "true",
            "DEFAULT_GIT_BRANCH": "main",
        },
        "aws_profile_map": {"default": {"region": "us-west-2"}},
    }

    with patch("caylent_devcontainer_cli.commands.setup_interactive.write_project_files") as mock_write:
        apply_template(template_data, "/target/path")

    mock_write.assert_called_once()
    call_args = mock_write.call_args
    assert call_args[0][0] == "/target/path"
    assert call_args[0][1] == template_data


def test_apply_template_does_not_copy_devcontainer():
    """Test that apply_template does NOT copy .devcontainer/ files."""
    template_data = {
        "containerEnv": {
            "AWS_CONFIG_ENABLED": "false",
        },
    }

    with (
        patch("caylent_devcontainer_cli.commands.setup_interactive.write_project_files"),
        patch("shutil.copytree") as mock_copytree,
        patch("shutil.rmtree") as mock_rmtree,
    ):
        apply_template(template_data, "/target/path")
        mock_copytree.assert_not_called()
        mock_rmtree.assert_not_called()


def test_apply_template_does_not_call_tool_versions():
    """Test that apply_template does not manage .tool-versions (handled by handle_setup)."""
    template_data = {
        "containerEnv": {
            "AWS_CONFIG_ENABLED": "false",
        },
    }

    with patch("caylent_devcontainer_cli.commands.setup_interactive.write_project_files"):
        # Should not raise AttributeError looking for check_and_create_tool_versions
        apply_template(template_data, "/target/path")
