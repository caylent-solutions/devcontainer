#!/usr/bin/env python3
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.setup import interactive_setup


@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_use_template", return_value=True)
@patch("caylent_devcontainer_cli.commands.setup_interactive.select_template", return_value="test-template")
@patch("caylent_devcontainer_cli.commands.setup_interactive.load_template_from_file")
@patch("caylent_devcontainer_cli.commands.setup_interactive.apply_template")
def test_interactive_setup_with_template(mock_apply, mock_load, mock_select, mock_prompt):
    mock_load.return_value = {"env_values": {}, "aws_profile_map": {}}

    interactive_setup("/source", "/target")

    mock_prompt.assert_called_once()
    mock_select.assert_called_once()
    mock_load.assert_called_once_with("test-template")
    mock_apply.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_use_template", return_value=False)
@patch("caylent_devcontainer_cli.commands.setup_interactive.create_template_interactive")
@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_save_template", return_value=False)
@patch("caylent_devcontainer_cli.commands.setup_interactive.apply_template")
def test_interactive_setup_without_template(mock_apply, mock_save_prompt, mock_create, mock_prompt):
    mock_create.return_value = {"env_values": {}, "aws_profile_map": {}}

    interactive_setup("/source", "/target")

    mock_prompt.assert_called_once()
    mock_create.assert_called_once()
    mock_save_prompt.assert_called_once()
    mock_apply.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_use_template", return_value=False)
@patch("caylent_devcontainer_cli.commands.setup_interactive.create_template_interactive")
@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_save_template", return_value=True)
@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_template_name", return_value="new-template")
@patch("caylent_devcontainer_cli.commands.setup_interactive.save_template_to_file")
@patch("caylent_devcontainer_cli.commands.setup_interactive.apply_template")
def test_interactive_setup_save_new_template(
    mock_apply, mock_save, mock_name, mock_save_prompt, mock_create, mock_prompt
):
    mock_create.return_value = {"env_values": {}, "aws_profile_map": {}}

    interactive_setup("/source", "/target")

    mock_prompt.assert_called_once()
    mock_create.assert_called_once()
    mock_save_prompt.assert_called_once()
    mock_name.assert_called_once()
    mock_save.assert_called_once_with({"env_values": {}, "aws_profile_map": {}}, "new-template")
    mock_apply.assert_called_once()
