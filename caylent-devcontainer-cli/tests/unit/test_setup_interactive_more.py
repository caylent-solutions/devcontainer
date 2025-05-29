#!/usr/bin/env python3
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.setup_interactive import upgrade_template


def test_upgrade_template_real():
    """Test the actual upgrade_template function."""
    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
        "cli_version": "1.0.0",
    }

    # Need to patch __version__ at the module level where upgrade_template is defined
    with patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["containerEnv"] == mock_template_data["containerEnv"]
    assert result["aws_profile_map"] == mock_template_data["aws_profile_map"]


def test_upgrade_template_with_env_values_real():
    """Test upgrading a template with env_values format."""
    mock_template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
        "cli_version": "1.0.0",
    }

    # Need to patch __version__ at the module level where upgrade_template is defined
    with patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["containerEnv"] == mock_template_data["env_values"]
    assert result["aws_profile_map"] == mock_template_data["aws_profile_map"]


def test_upgrade_template_without_env_values_real():
    """Test upgrading a template with no env values."""
    mock_template_data = {
        "cli_version": "1.0.0",
    }

    # Need to patch __version__ at the module level where upgrade_template is defined
    with patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"), patch(
        "caylent_devcontainer_cli.commands.setup_interactive.prompt_env_values",
        return_value={"AWS_CONFIG_ENABLED": "false"},
    ):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["containerEnv"] == {"AWS_CONFIG_ENABLED": "false"}
    assert result["aws_profile_map"] == {}


def test_upgrade_template_with_aws_enabled_no_profile_real():
    """Test upgrading a template with AWS enabled but no profile map."""
    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "cli_version": "1.0.0",
    }

    # Need to patch __version__ at the module level where upgrade_template is defined
    with patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"), patch(
        "caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map",
        return_value={"default": {"region": "us-west-2"}},
    ):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["containerEnv"] == mock_template_data["containerEnv"]
    assert result["aws_profile_map"] == {"default": {"region": "us-west-2"}}
