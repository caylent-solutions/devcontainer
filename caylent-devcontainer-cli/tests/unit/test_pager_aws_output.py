#!/usr/bin/env python3
"""Tests for pager and AWS output format selection features."""

import os
import sys
from unittest.mock import patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


@patch("questionary.password")
@patch("questionary.text")
@patch("questionary.select")
def test_prompt_env_values_none_pager(mock_select, mock_text, mock_password):
    """Test prompt_env_values with None response for pager selection."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.side_effect = ["true", None]
    mock_text.return_value.ask.side_effect = [
        "main",
        "3.12.9",
        "Developer",
        "github.com",
        "user",
        "user@example.com",
        "",
    ]
    mock_password.return_value.ask.return_value = "token123"

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.password")
@patch("questionary.text")
@patch("questionary.select")
def test_prompt_env_values_none_aws_output(mock_select, mock_text, mock_password):
    """Test prompt_env_values with None response for AWS output format."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.side_effect = ["true", "cat", None]
    mock_text.return_value.ask.side_effect = [
        "main",
        "3.12.9",
        "Developer",
        "github.com",
        "user",
        "user@example.com",
        "",
    ]
    mock_password.return_value.ask.return_value = "token123"

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.password")
@patch("questionary.text")
@patch("questionary.select")
def test_pager_selection_options(mock_select, mock_text, mock_password):
    """Test that all pager options are available and work correctly."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    pager_options = ["cat", "less", "more", "most"]

    for pager in pager_options:
        mock_select.return_value.ask.side_effect = ["false", pager]
        mock_text.return_value.ask.side_effect = [
            "main",
            "3.12.9",
            "Developer",
            "github.com",
            "user",
            "user@example.com",
            "",
        ]
        mock_password.return_value.ask.return_value = "token123"

        result = prompt_env_values()
        assert result["PAGER"] == pager


@patch("questionary.password")
@patch("questionary.text")
@patch("questionary.select")
def test_aws_output_selection_options(mock_select, mock_text, mock_password):
    """Test that all AWS output format options are available and work correctly."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    aws_output_options = ["json", "table", "text", "yaml"]

    for output_format in aws_output_options:
        mock_select.return_value.ask.side_effect = ["true", "cat", output_format]
        mock_text.return_value.ask.side_effect = [
            "main",
            "3.12.9",
            "Developer",
            "github.com",
            "user",
            "user@example.com",
            "",
        ]
        mock_password.return_value.ask.return_value = "token123"

        result = prompt_env_values()
        assert result["AWS_DEFAULT_OUTPUT"] == output_format


@patch("questionary.password")
@patch("questionary.text")
@patch("questionary.select")
def test_aws_output_not_prompted_when_aws_disabled(mock_select, mock_text, mock_password):
    """Test that AWS output format is not prompted when AWS is disabled."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    # Only two select calls: AWS config (false) and pager (cat)
    mock_select.return_value.ask.side_effect = ["false", "cat"]
    mock_text.return_value.ask.side_effect = [
        "main",
        "3.12.9",
        "Developer",
        "github.com",
        "user",
        "user@example.com",
        "",
    ]
    mock_password.return_value.ask.return_value = "token123"

    result = prompt_env_values()

    assert result["AWS_CONFIG_ENABLED"] == "false"
    assert result["PAGER"] == "cat"
    assert "AWS_DEFAULT_OUTPUT" not in result

    # Verify that select was only called twice (AWS config and pager)
    assert mock_select.return_value.ask.call_count == 2


@patch("questionary.password")
@patch("questionary.text")
@patch("questionary.select")
def test_default_values_selection(mock_select, mock_text, mock_password):
    """Test that default values are properly set for pager and AWS output."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    # Test with AWS enabled - should get both pager and AWS output prompts
    mock_select.return_value.ask.side_effect = ["true", "cat", "json"]
    mock_text.return_value.ask.side_effect = [
        "main",
        "3.12.9",
        "Developer",
        "github.com",
        "user",
        "user@example.com",
        "",
    ]
    mock_password.return_value.ask.return_value = "token123"

    result = prompt_env_values()

    assert result["PAGER"] == "cat"  # Default pager
    assert result["AWS_DEFAULT_OUTPUT"] == "json"  # Default AWS output
