#!/usr/bin/env python3
import os
import sys
from unittest.mock import mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.setup_interactive import apply_template, save_template_to_file


@patch("caylent_devcontainer_cli.commands.setup_interactive.write_project_files")
def test_apply_template_calls_write_project_files(mock_write_files):
    """Test that apply_template delegates to write_project_files."""
    template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_PYTHON_VERSION": "3.12.9"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
    }

    with patch("caylent_devcontainer_cli.commands.setup.check_and_create_tool_versions"):
        apply_template(template_data, "/target")

    mock_write_files.assert_called_once()
    call_args = mock_write_files.call_args
    assert call_args[0][0] == "/target"
    assert call_args[0][1] == template_data


@patch("os.path.exists", return_value=False)
@patch("os.makedirs")
@patch("builtins.open", new_callable=mock_open)
def test_save_template_adds_newline(mock_file, mock_makedirs, mock_exists):
    template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "true"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
    }

    save_template_to_file(template_data, "test-template")

    # Check that write was called with a newline
    write_calls = mock_file().write.call_args_list
    assert any(args[0][0] == "\n" for args in write_calls)
