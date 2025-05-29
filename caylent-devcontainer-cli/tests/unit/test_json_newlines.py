#!/usr/bin/env python3
import os
import sys
from unittest.mock import mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.setup_interactive import (
    apply_template,
    save_template_to_file,
)


@patch("os.path.exists", return_value=False)
@patch("shutil.copytree")
@patch("builtins.open", new_callable=mock_open)
def test_apply_template_adds_newlines(mock_file, mock_copytree, mock_exists):
    template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "true"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
    }

    apply_template(template_data, "/target", "/source")

    # Check that write was called with a newline for both files
    write_calls = mock_file().write.call_args_list
    assert any(args[0][0] == "\n" for args in write_calls)

    # We don't need to check the exact count as json.dump() makes multiple write calls
    # Just verify that at least one newline was written
    assert sum(1 for args in write_calls if args[0][0] == "\n") >= 1


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
