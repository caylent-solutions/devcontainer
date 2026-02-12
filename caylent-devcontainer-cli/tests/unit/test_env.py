#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.commands.env import handle_env_export, handle_env_load, load_environment


def test_handle_env_export():
    with patch("caylent_devcontainer_cli.commands.env.generate_shell_env") as mock_generate:
        args = MagicMock()
        args.json_file = "test.json"
        args.output = "output.sh"
        args.no_export = False

        handle_env_export(args)

        mock_generate.assert_called_once_with("test.json", "output.sh", False)


def test_handle_env_load():
    with patch("caylent_devcontainer_cli.commands.env.load_environment") as mock_load, patch(
        "caylent_devcontainer_cli.commands.env.resolve_project_root", return_value="/test/path"
    ):
        args = MagicMock()
        args.project_root = "/test/path"

        handle_env_load(args)

        mock_load.assert_called_once_with("/test/path")


@patch("os.path.exists", side_effect=[True])
@patch("os.path.join", return_value="shell.env")
def test_load_environment_existing(mock_join, mock_exists, capsys):
    with patch("caylent_devcontainer_cli.commands.env.generate_shell_env") as mock_generate:
        load_environment("/test/path")

        mock_exists.assert_called_once()
        mock_generate.assert_not_called()

        captured = capsys.readouterr()
        assert "To load the environment variables" in captured.out
        assert "shell.env" in captured.out


@patch("os.path.exists", side_effect=[False, True])
@patch("caylent_devcontainer_cli.commands.env.generate_shell_env")
def test_load_environment_generate(mock_generate, mock_exists, capsys):
    load_environment("/test/path")

    assert mock_exists.call_count == 2
    mock_generate.assert_called_once()

    captured = capsys.readouterr()
    assert "To load the environment variables" in captured.out
    assert "Generating shell.env" in captured.err


@patch("os.path.exists", side_effect=[False, False])
def test_load_environment_missing_config(mock_exists, capsys):
    with pytest.raises(SystemExit):
        load_environment("/test/path")

    assert mock_exists.call_count == 2

    captured = capsys.readouterr()
    assert "Configuration file not found" in captured.err
