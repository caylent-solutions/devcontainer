#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.commands.setup_interactive import (
    JsonValidator,
    apply_template,
    create_template_interactive,
    list_templates,
    load_template_from_file,
    prompt_aws_profile_map,
    prompt_env_values,
    prompt_save_template,
    prompt_template_name,
    prompt_use_template,
    save_template_to_file,
    select_template,
)


def test_json_validator_valid():
    validator = JsonValidator()
    document = MagicMock()
    document.text = '{"key": "value"}'
    # Should not raise an exception
    validator.validate(document)


def test_json_validator_invalid():
    validator = JsonValidator()
    document = MagicMock()
    document.text = '{"key": value}'  # Missing quotes

    with pytest.raises(Exception):
        validator.validate(document)


@patch("os.path.exists", return_value=True)
@patch("os.listdir", return_value=["template1.json", "template2.json", "not-a-template.txt"])
def test_list_templates(mock_listdir, mock_exists):
    templates = list_templates()
    assert "template1" in templates
    assert "template2" in templates
    assert "not-a-template" not in templates


@patch("os.path.exists", return_value=False)
@patch("os.makedirs")
def test_list_templates_no_dir(mock_makedirs, mock_exists):
    templates = list_templates()
    assert templates == []
    mock_makedirs.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.list_templates", return_value=["template1"])
@patch("questionary.confirm")
def test_prompt_use_template_with_templates(mock_confirm, mock_list):
    mock_confirm.return_value.ask.return_value = True
    result = prompt_use_template()
    assert result is True
    mock_confirm.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.list_templates", return_value=[])
def test_prompt_use_template_no_templates(mock_list):
    result = prompt_use_template()
    assert result is False


@patch("caylent_devcontainer_cli.commands.setup_interactive.list_templates", return_value=["template1", "template2"])
@patch("questionary.select")
def test_select_template(mock_select, mock_list):
    mock_select.return_value.ask.return_value = "template1"
    result = select_template()
    assert result == "template1"
    mock_select.assert_called_once()


@patch("questionary.confirm")
def test_prompt_save_template(mock_confirm):
    mock_confirm.return_value.ask.return_value = True
    result = prompt_save_template()
    assert result is True
    mock_confirm.assert_called_once()


@patch("questionary.text")
def test_prompt_template_name(mock_text):
    mock_text.return_value.ask.return_value = "my-template"
    result = prompt_template_name()
    assert result == "my-template"
    mock_text.assert_called_once()


@patch("questionary.text")
@patch("questionary.select")
@patch("questionary.password")
def test_prompt_env_values(mock_password, mock_select, mock_text):
    # Setup mock returns
    mock_select.return_value.ask.return_value = "true"
    mock_text.return_value.ask.side_effect = [
        "main",
        "3.12.9",
        "Test User",
        "github.com",
        "testuser",
        "test@example.com",
        "",
    ]
    mock_password.return_value.ask.return_value = "token123"

    result = prompt_env_values()

    assert result["AWS_CONFIG_ENABLED"] == "true"
    assert result["DEFAULT_GIT_BRANCH"] == "main"
    assert result["DEFAULT_PYTHON_VERSION"] == "3.12.9"
    assert result["DEVELOPER_NAME"] == "Test User"
    assert result["GIT_PROVIDER_URL"] == "github.com"
    assert result["GIT_USER"] == "testuser"
    assert result["GIT_USER_EMAIL"] == "test@example.com"
    assert result["GIT_TOKEN"] == "token123"
    assert result["EXTRA_APT_PACKAGES"] == ""


@patch("questionary.confirm")
def test_prompt_aws_profile_map_skip(mock_confirm):
    mock_confirm.return_value.ask.return_value = False
    result = prompt_aws_profile_map()
    assert result == {}
    mock_confirm.assert_called_once()


@patch("questionary.confirm")
@patch("questionary.text")
def test_prompt_aws_profile_map(mock_text, mock_confirm):
    mock_confirm.return_value.ask.return_value = True
    mock_text.return_value.ask.return_value = '{"default": {"region": "us-west-2"}}'

    result = prompt_aws_profile_map()

    assert result == {"default": {"region": "us-west-2"}}
    mock_confirm.assert_called_once()
    mock_text.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_env_values")
@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map")
def test_create_template_interactive_with_aws(mock_aws, mock_env):
    mock_env.return_value = {"AWS_CONFIG_ENABLED": "true"}
    mock_aws.return_value = {"default": {"region": "us-west-2"}}

    result = create_template_interactive()

    assert result["env_values"] == {"AWS_CONFIG_ENABLED": "true"}
    assert result["aws_profile_map"] == {"default": {"region": "us-west-2"}}
    mock_env.assert_called_once()
    mock_aws.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_env_values")
def test_create_template_interactive_without_aws(mock_env):
    mock_env.return_value = {"AWS_CONFIG_ENABLED": "false"}

    result = create_template_interactive()

    assert result["env_values"] == {"AWS_CONFIG_ENABLED": "false"}
    assert result["aws_profile_map"] == {}
    mock_env.assert_called_once()


@patch("os.path.exists", return_value=False)
@patch("os.makedirs")
@patch("builtins.open", new_callable=mock_open)
def test_save_template_to_file(mock_file, mock_makedirs, mock_exists):
    template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "true"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
    }

    save_template_to_file(template_data, "test-template")

    mock_makedirs.assert_called_once()
    mock_file.assert_called_once()
    # json.dump() makes multiple write calls, so we just check that write was called
    assert mock_file().write.call_count > 0


@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data='{"env_values": {}}')
def test_load_template_from_file(mock_file, mock_exists):
    result = load_template_from_file("test-template")

    assert result == {"env_values": {}}
    mock_file.assert_called_once()


@patch("os.path.exists", return_value=False)
def test_load_template_from_file_not_found(mock_exists):
    with pytest.raises(SystemExit):
        load_template_from_file("non-existent")


@patch("os.path.exists", return_value=False)
@patch("shutil.copytree")
@patch("builtins.open", new_callable=mock_open)
def test_apply_template_without_aws(mock_file, mock_copytree, mock_exists):
    template_data = {"env_values": {"AWS_CONFIG_ENABLED": "false"}, "aws_profile_map": {}}

    apply_template(template_data, "/target", "/source")

    mock_copytree.assert_called_once()
    assert mock_file.call_count == 1  # Only env file, no AWS file


@patch("os.path.exists", return_value=False)
@patch("shutil.copytree")
@patch("builtins.open", new_callable=mock_open)
def test_apply_template_with_aws(mock_file, mock_copytree, mock_exists):
    template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "true"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
    }

    apply_template(template_data, "/target", "/source")

    mock_copytree.assert_called_once()
    assert mock_file.call_count == 2  # Both env file and AWS file
