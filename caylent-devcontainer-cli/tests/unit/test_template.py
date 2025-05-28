#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

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


@patch("os.path.exists", side_effect=[True, True])
@patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=True)
@patch("shutil.copy2")
@patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir")
def test_save_template(mock_ensure, mock_copy, mock_confirm, mock_exists, capsys):
    save_template("/test/path", "test-template")

    mock_ensure.assert_called_once()
    assert mock_exists.call_count >= 1
    mock_confirm.assert_called_once()
    mock_copy.assert_called_once()

    captured = capsys.readouterr()
    assert "Saving template" in captured.err or "Template saved" in captured.err


@patch("os.path.exists", side_effect=[True, True])
@patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=True)
@patch("shutil.copy2")
def test_load_template(mock_copy, mock_confirm, mock_exists, capsys):
    load_template("/test/path", "test-template")

    mock_exists.assert_called()
    mock_confirm.assert_called_once()
    mock_copy.assert_called_once()

    captured = capsys.readouterr()
    assert "Loading template" in captured.err or "Template" in captured.err


@patch("os.listdir", return_value=["template1.json", "template2.json", "not-a-template.txt"])
@patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir")
def test_list_templates(mock_ensure, mock_listdir, capsys):
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
