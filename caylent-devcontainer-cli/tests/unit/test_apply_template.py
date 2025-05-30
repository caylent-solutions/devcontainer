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

    with patch("os.path.exists", return_value=False), patch("shutil.copytree"), patch("shutil.rmtree"), patch(
        "builtins.open"
    ), patch("json.dump"), patch("os.remove"):
        apply_template(template_data, "/target/path", "/source/path")


def test_apply_template_with_env_values():
    """Test applying a template with env_values format (old format)."""
    template_data = {
        "env_values": {
            "AWS_CONFIG_ENABLED": "true",
            "DEFAULT_GIT_BRANCH": "main",
        },
        "aws_profile_map": {"default": {"region": "us-west-2"}},
    }

    with patch("os.path.exists", return_value=False), patch("shutil.copytree"), patch("shutil.rmtree"), patch(
        "builtins.open"
    ), patch("json.dump"), patch("os.remove"):
        apply_template(template_data, "/target/path", "/source/path")


def test_apply_template_with_existing_target():
    """Test applying a template when target directory already exists."""
    template_data = {
        "containerEnv": {
            "AWS_CONFIG_ENABLED": "false",
        },
    }

    with patch("os.path.exists", return_value=True), patch("shutil.copytree"), patch(
        "shutil.rmtree"
    ) as mock_rmtree, patch("builtins.open"), patch("json.dump"), patch("os.remove"):
        apply_template(template_data, "/target/path", "/source/path")
        mock_rmtree.assert_called_once()


def test_apply_template_with_example_files():
    """Test applying a template with example files that need to be removed."""
    template_data = {
        "containerEnv": {
            "AWS_CONFIG_ENABLED": "false",
        },
    }

    with patch("os.path.exists", side_effect=[False, True, True]), patch("shutil.copytree"), patch(
        "shutil.rmtree"
    ), patch("builtins.open"), patch("json.dump"), patch("os.remove") as mock_remove:
        apply_template(template_data, "/target/path", "/source/path")
        assert mock_remove.call_count == 2
