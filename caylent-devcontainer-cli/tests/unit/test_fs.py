#!/usr/bin/env python3
import os
import sys
from unittest.mock import mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.utils.fs import find_project_root, generate_exports, generate_shell_env, load_json_config


@patch("builtins.open", mock_open(read_data='{"containerEnv": {"TEST_VAR": "test_value"}}'))
def test_load_json_config():
    data = load_json_config("test_file.json")
    assert data == {"containerEnv": {"TEST_VAR": "test_value"}}


@patch("builtins.open", mock_open(read_data="invalid json"))
def test_load_json_config_invalid():
    with pytest.raises(SystemExit):
        load_json_config("test_file.json")


def test_generate_exports():
    env_dict = {"TEST_VAR": "test_value", "TEST_JSON": {"key": "value"}, "TEST_LIST": [1, 2, 3]}

    # Test with export_prefix=True
    lines = generate_exports(env_dict, export_prefix=True)
    assert len(lines) == 3
    assert "export TEST_VAR='test_value'" in lines
    assert "export TEST_JSON='" in lines[1]
    assert "export TEST_LIST='" in lines[2]

    # Test with export_prefix=False
    lines = generate_exports(env_dict, export_prefix=False)
    assert len(lines) == 3
    assert "TEST_VAR='test_value'" in lines
    assert "TEST_JSON='" in lines[1]
    assert "TEST_LIST='" in lines[2]


@patch("caylent_devcontainer_cli.utils.fs.load_json_config", return_value={"containerEnv": {"TEST_VAR": "test_value"}})
@patch("os.path.exists", return_value=False)
@patch("caylent_devcontainer_cli.utils.fs.confirm_action", return_value=True)
def test_generate_shell_env(mock_confirm, mock_exists, mock_load_json):
    with patch("builtins.open", mock_open()) as mock_file:
        generate_shell_env("test_file.json", "output_file.sh")
        mock_file().write.assert_called()


@patch("os.path.exists", return_value=False)
@patch("caylent_devcontainer_cli.utils.fs.load_json_config", return_value={"invalid": []})
@patch("caylent_devcontainer_cli.utils.fs.confirm_action", return_value=True)
def test_generate_shell_env_invalid_json(mock_confirm, mock_load_json, mock_exists):
    with pytest.raises(SystemExit):
        generate_shell_env("test_file.json", "output_file.sh")


@patch("os.path.isdir", return_value=True)
def test_find_project_root(mock_isdir):
    result = find_project_root("/test/path")
    assert result == "/test/path"
    mock_isdir.assert_called_with("/test/path/.devcontainer")


@patch("os.path.isdir", return_value=False)
def test_find_project_root_invalid(mock_isdir):
    with pytest.raises(SystemExit):
        find_project_root("/test/path")


@patch("os.path.isfile", return_value=True)
@patch("os.path.isdir", return_value=True)
@patch("os.path.dirname", return_value="/test")
def test_find_project_root_file(mock_dirname, mock_isdir, mock_isfile):
    result = find_project_root("/test/file.txt")
    assert result == "/test"
    mock_isfile.assert_called_with("/test/file.txt")
    mock_dirname.assert_called_with("/test/file.txt")
    mock_isdir.assert_called_with("/test/.devcontainer")
