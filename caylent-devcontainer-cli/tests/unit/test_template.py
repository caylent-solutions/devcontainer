#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.template import (
    ensure_templates_dir,
    handle_template_list,
    handle_template_load,
    handle_template_save,
    list_templates,
    load_template,
    save_template,
)
from caylent_devcontainer_cli.utils.constants import TEMPLATES_DIR


def test_ensure_templates_dir():
    with patch("os.makedirs") as mock_makedirs:
        ensure_templates_dir()
        mock_makedirs.assert_called_once_with(TEMPLATES_DIR, exist_ok=True)


def test_handle_template_save():
    with patch("caylent_devcontainer_cli.commands.template.save_template") as mock_save:
        args = MagicMock()
        args.project_root = "/test/path"
        args.name = "test-template"

        handle_template_save(args)

        mock_save.assert_called_once_with("/test/path", "test-template")


def test_handle_template_load():
    with patch("caylent_devcontainer_cli.commands.template.load_template") as mock_load:
        args = MagicMock()
        args.project_root = "/test/path"
        args.name = "test-template"

        handle_template_load(args)

        mock_load.assert_called_once_with("/test/path", "test-template")


def test_handle_template_list():
    with patch("caylent_devcontainer_cli.commands.template.list_templates") as mock_list:
        args = MagicMock()

        handle_template_list(args)

        mock_list.assert_called_once()


def test_save_template():
    mock_env_data = {"key": "value"}
    mock_file = MagicMock()

    with patch("builtins.open", mock_file), patch("os.path.exists", return_value=True), patch(
        "json.load", return_value=mock_env_data
    ), patch("json.dump") as mock_dump, patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "caylent_devcontainer_cli.commands.template.ensure_templates_dir"
    ):

        save_template("/test/path", "test-template")

        # Verify json.dump was called with the env_data that includes cli_version
        mock_dump.assert_called_once()
        # First arg is the data dict, second arg is the file object
        saved_data = mock_dump.call_args[0][0]
        assert "cli_version" in saved_data


def test_load_template():
    mock_template_data = {"key": "value"}
    mock_file = MagicMock()

    with patch("builtins.open", mock_file), patch("os.path.exists", return_value=True), patch(
        "json.load", return_value=mock_template_data
    ), patch("json.dump") as mock_dump, patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ):

        load_template("/test/path", "test-template")

        # Verify json.dump was called with the template data
        mock_dump.assert_called_once()
        # First arg is the data dict, second arg is the file object
        loaded_data = mock_dump.call_args[0][0]
        assert loaded_data == mock_template_data


@patch("os.listdir", return_value=["template1.json", "template2.json", "not-a-template.txt"])
@patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir")
def test_list_templates(mock_ensure, mock_listdir, capsys):
    with patch("builtins.open", MagicMock()), patch("json.load", return_value={"cli_version": "1.0.0"}):
        list_templates()

    mock_ensure.assert_called_once()
    captured = capsys.readouterr()
    assert "Available templates" in captured.out
    assert "template1" in captured.out
    assert "template2" in captured.out
    assert "not-a-template" not in captured.out


@patch("os.listdir", return_value=[])
@patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir")
def test_list_templates_empty(mock_ensure, mock_listdir, capsys):
    list_templates()

    mock_ensure.assert_called_once()
    captured = capsys.readouterr()
    assert "No templates found" in captured.out
