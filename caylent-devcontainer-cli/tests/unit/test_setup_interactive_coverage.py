#!/usr/bin/env python3
import os
import sys
from unittest.mock import mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


# Tests for KeyboardInterrupt and None response handling
@patch("questionary.confirm")
def test_prompt_use_template_keyboard_interrupt(mock_confirm):
    """Test prompt_use_template with KeyboardInterrupt."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_use_template

    mock_confirm.return_value.ask.side_effect = KeyboardInterrupt()

    with pytest.raises(SystemExit):
        prompt_use_template()


@patch("questionary.confirm")
def test_prompt_use_template_none_response(mock_confirm):
    """Test prompt_use_template with None response."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_use_template

    mock_confirm.return_value.ask.return_value = None

    with pytest.raises(SystemExit):
        prompt_use_template()


@patch("questionary.select")
def test_select_template_keyboard_interrupt(mock_select):
    """Test select_template with KeyboardInterrupt."""
    from caylent_devcontainer_cli.commands.setup_interactive import select_template

    mock_select.return_value.ask.side_effect = KeyboardInterrupt()

    with pytest.raises(SystemExit):
        select_template()


@patch("questionary.select")
def test_select_template_none_response(mock_select):
    """Test select_template with None response."""
    from caylent_devcontainer_cli.commands.setup_interactive import select_template

    mock_select.return_value.ask.return_value = None

    with pytest.raises(SystemExit):
        select_template()


@patch("questionary.select")
def test_select_template_go_back(mock_select):
    """Test select_template with go back option."""
    from caylent_devcontainer_cli.commands.setup_interactive import select_template

    mock_select.return_value.ask.return_value = "< Go back"

    result = select_template()
    assert result is None


@patch("questionary.confirm")
def test_prompt_save_template_keyboard_interrupt(mock_confirm):
    """Test prompt_save_template with KeyboardInterrupt."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_save_template

    mock_confirm.return_value.ask.side_effect = KeyboardInterrupt()

    with pytest.raises(SystemExit):
        prompt_save_template()


@patch("questionary.confirm")
def test_prompt_save_template_none_response(mock_confirm):
    """Test prompt_save_template with None response."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_save_template

    mock_confirm.return_value.ask.return_value = None

    with pytest.raises(SystemExit):
        prompt_save_template()


@patch("questionary.text")
def test_prompt_template_name_keyboard_interrupt(mock_text):
    """Test prompt_template_name with KeyboardInterrupt."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_template_name

    mock_text.return_value.ask.side_effect = KeyboardInterrupt()

    with pytest.raises(SystemExit):
        prompt_template_name()


@patch("questionary.text")
def test_prompt_template_name_none_response(mock_text):
    """Test prompt_template_name with None response."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_template_name

    mock_text.return_value.ask.return_value = None

    with pytest.raises(SystemExit):
        prompt_template_name()


@patch("questionary.select")
def test_prompt_env_values_keyboard_interrupt(mock_select):
    """Test prompt_env_values with KeyboardInterrupt."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.side_effect = KeyboardInterrupt()

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.select")
def test_prompt_env_values_none_aws_config(mock_select):
    """Test prompt_env_values with None response for AWS config."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.return_value = None

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.text")
@patch("questionary.select")
def test_prompt_env_values_none_git_branch(mock_select, mock_text):
    """Test prompt_env_values with None response for git branch."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.return_value = "true"
    mock_text.return_value.ask.return_value = None

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.text")
@patch("questionary.select")
def test_prompt_env_values_none_python_version(mock_select, mock_text):
    """Test prompt_env_values with None response for Python version."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.return_value = "true"
    mock_text.return_value.ask.side_effect = ["main", None]

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.text")
@patch("questionary.select")
def test_prompt_env_values_none_developer_name(mock_select, mock_text):
    """Test prompt_env_values with None response for developer name."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.return_value = "true"
    mock_text.return_value.ask.side_effect = ["main", "3.12.9", None]

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.text")
@patch("questionary.select")
def test_prompt_env_values_none_git_provider(mock_select, mock_text):
    """Test prompt_env_values with None response for git provider."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.return_value = "true"
    mock_text.return_value.ask.side_effect = ["main", "3.12.9", "Developer", None]

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.text")
@patch("questionary.select")
def test_prompt_env_values_none_git_user(mock_select, mock_text):
    """Test prompt_env_values with None response for git user."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.return_value = "true"
    mock_text.return_value.ask.side_effect = ["main", "3.12.9", "Developer", "github.com", None]

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.text")
@patch("questionary.select")
def test_prompt_env_values_none_git_email(mock_select, mock_text):
    """Test prompt_env_values with None response for git email."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.return_value = "true"
    mock_text.return_value.ask.side_effect = ["main", "3.12.9", "Developer", "github.com", "user", None]

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.password")
@patch("questionary.text")
@patch("questionary.select")
def test_prompt_env_values_none_git_token(mock_select, mock_text, mock_password):
    """Test prompt_env_values with None response for git token."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.return_value = "true"
    mock_text.return_value.ask.side_effect = ["main", "3.12.9", "Developer", "github.com", "user", "user@example.com"]
    mock_password.return_value.ask.return_value = None

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.password")
@patch("questionary.text")
@patch("questionary.select")
def test_prompt_env_values_none_extra_packages(mock_select, mock_text, mock_password):
    """Test prompt_env_values with None response for extra packages."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_env_values

    mock_select.return_value.ask.return_value = "true"
    mock_text.return_value.ask.side_effect = [
        "main",
        "3.12.9",
        "Developer",
        "github.com",
        "user",
        "user@example.com",
        None,
    ]
    mock_password.return_value.ask.return_value = "token123"

    with pytest.raises(SystemExit):
        prompt_env_values()


@patch("questionary.select")
def test_load_template_version_mismatch_upgrade(mock_select):
    """Test load_template_from_file with version mismatch - upgrade choice."""
    from caylent_devcontainer_cli.commands.setup_interactive import load_template_from_file

    mock_select.return_value.ask.return_value = "Upgrade the template to the current format"

    with patch("builtins.open", mock_open(read_data='{"containerEnv": {"TEST": "value"}, "cli_version": "0.1.0"}')):
        with patch("os.path.exists", return_value=True):
            result = load_template_from_file("test-template")

            assert "cli_version" in result
            assert result["containerEnv"]["TEST"] == "value"


@patch("questionary.select")
@patch("caylent_devcontainer_cli.commands.setup_interactive.create_template_interactive")
def test_load_template_version_mismatch_create_new(mock_create, mock_select):
    """Test load_template_from_file with version mismatch - create new choice."""
    from caylent_devcontainer_cli.commands.setup_interactive import load_template_from_file

    mock_select.return_value.ask.return_value = "Create a new template from scratch"
    mock_create.return_value = {"containerEnv": {"NEW": "value"}}

    with patch("builtins.open", mock_open(read_data='{"containerEnv": {"TEST": "value"}, "cli_version": "0.1.0"}')):
        with patch("os.path.exists", return_value=True):
            result = load_template_from_file("test-template")

            assert result["containerEnv"]["NEW"] == "value"
            mock_create.assert_called_once()


@patch("questionary.select")
def test_load_template_version_mismatch_exit(mock_select):
    """Test load_template_from_file with version mismatch - exit choice."""
    from caylent_devcontainer_cli.commands.setup_interactive import load_template_from_file

    mock_select.return_value.ask.return_value = "Exit without making changes"

    with patch("builtins.open", mock_open(read_data='{"containerEnv": {"TEST": "value"}, "cli_version": "0.1.0"}')):
        with patch("os.path.exists", return_value=True):
            with pytest.raises(SystemExit):
                load_template_from_file("test-template")


@patch("questionary.select")
def test_load_template_version_mismatch_use_anyway(mock_select):
    """Test load_template_from_file with version mismatch - use anyway choice."""
    from caylent_devcontainer_cli.commands.setup_interactive import load_template_from_file

    mock_select.return_value.ask.return_value = "Use the template anyway (may cause issues)"

    with patch("builtins.open", mock_open(read_data='{"containerEnv": {"TEST": "value"}, "cli_version": "0.1.0"}')):
        with patch("os.path.exists", return_value=True):
            result = load_template_from_file("test-template")

            assert result["containerEnv"]["TEST"] == "value"
