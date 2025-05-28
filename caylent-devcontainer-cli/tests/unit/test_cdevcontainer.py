#!/usr/bin/env python3
import os
import sys
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock, call

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the CLI module
CLI_PATH = os.path.join(os.path.dirname(__file__), '../../.devcontainer/cdevcontainer')

# Mock the CLI module
class MockCLI:
    def __init__(self):
        self.AUTO_YES = False
        self.TEMPLATES_DIR = os.path.expanduser("~/.devcontainer-templates")
        self.INSTALL_DIR = os.path.expanduser("~/.local/bin")
        self.CLI_NAME = "Caylent Devcontainer CLI"
        self.VERSION = "1.0.0"
        self.COLORS = {
            "CYAN": "\033[1;36m",
            "GREEN": "\033[1;32m",
            "YELLOW": "\033[1;33m",
            "RED": "\033[1;31m",
            "BLUE": "\033[1;34m",
            "PURPLE": "\033[1;35m",
            "RESET": "\033[0m",
            "BOLD": "\033[1m"
        }

# Load the CLI module
with open(CLI_PATH, 'r') as f:
    cli_code = f.read()
    
# Create a namespace for the CLI module
cli = MockCLI()

# Execute the CLI code in the namespace
exec(cli_code, globals(), vars(cli))

# Test the log function
def test_log(capsys):
    cli.log("INFO", "Test message")
    captured = capsys.readouterr()
    assert "Test message" in captured.err
    assert "[INFO]" in captured.err

# Test the confirm_action function with yes response
@patch('builtins.input', return_value='y')
def test_confirm_action_yes(mock_input, capsys):
    result = cli.confirm_action("Test confirmation")
    captured = capsys.readouterr()
    assert result is True
    assert "Test confirmation" in captured.err
    mock_input.assert_called_once()

# Test the confirm_action function with no response
@patch('builtins.input', return_value='n')
def test_confirm_action_no(mock_input, capsys):
    with pytest.raises(SystemExit):
        cli.confirm_action("Test confirmation")
    captured = capsys.readouterr()
    assert "Test confirmation" in captured.err
    assert "Operation cancelled by user" in captured.err
    mock_input.assert_called_once()

# Test the confirm_action function with AUTO_YES=True
def test_confirm_action_auto_yes(capsys):
    cli.AUTO_YES = True
    result = cli.confirm_action("Test confirmation")
    captured = capsys.readouterr()
    assert result is True
    assert "Test confirmation" in captured.err
    assert "Automatically confirmed" in captured.err
    cli.AUTO_YES = False

# Test the generate_exports function
def test_generate_exports():
    env_dict = {
        "TEST_VAR": "test_value",
        "TEST_JSON": {"key": "value"},
        "TEST_LIST": [1, 2, 3]
    }
    
    # Test with export_prefix=True
    lines = cli.generate_exports(env_dict, export_prefix=True)
    assert len(lines) == 3
    assert lines[0] == "export TEST_VAR='test_value'"
    assert "export TEST_JSON=" in lines[1]
    assert "export TEST_LIST=" in lines[2]
    
    # Test with export_prefix=False
    lines = cli.generate_exports(env_dict, export_prefix=False)
    assert len(lines) == 3
    assert lines[0] == "TEST_VAR='test_value'"
    assert "TEST_JSON=" in lines[1]
    assert "TEST_LIST=" in lines[2]

# Test the load_json_config function
@patch('builtins.open', mock_open(read_data='{"containerEnv": {"TEST_VAR": "test_value"}}'))
def test_load_json_config():
    data = cli.load_json_config("test_file.json")
    assert data == {"containerEnv": {"TEST_VAR": "test_value"}}

# Test the load_json_config function with invalid JSON
@patch('builtins.open', mock_open(read_data='invalid json'))
def test_load_json_config_invalid():
    with pytest.raises(SystemExit):
        cli.load_json_config("test_file.json")

# Test the generate_shell_env function
@patch('builtins.open', mock_open(read_data='{"containerEnv": {"TEST_VAR": "test_value"}}'))
@patch('os.path.exists', return_value=False)
@patch('cli.confirm_action', return_value=True)
def test_generate_shell_env(mock_confirm, mock_exists, capsys):
    with patch('builtins.open', mock_open()) as mock_file:
        cli.generate_shell_env("test_file.json", "output_file.sh")
        mock_file().write.assert_called_with("export TEST_VAR='test_value'\n")
    
    captured = capsys.readouterr()
    assert "Reading configuration" in captured.err
    assert "Wrote" in captured.err

# Test the find_project_root function
@patch('os.path.isdir', return_value=True)
def test_find_project_root(mock_isdir):
    result = cli.find_project_root("/test/path")
    assert result == "/test/path"
    mock_isdir.assert_called_with("/test/path/.devcontainer")

# Test the find_project_root function with invalid path
@patch('os.path.isdir', return_value=False)
def test_find_project_root_invalid(mock_isdir, capsys):
    with pytest.raises(SystemExit):
        cli.find_project_root("/test/path")
    
    captured = capsys.readouterr()
    assert "Could not find a valid project root" in captured.err

# Test the install_cli function
@patch('os.path.exists', return_value=False)
@patch('os.makedirs')
@patch('shutil.copy2')
@patch('os.chmod')
@patch('os.environ.get', return_value="/usr/local/bin:/usr/bin")
def test_install_cli(mock_env, mock_chmod, mock_copy, mock_makedirs, mock_exists, capsys):
    with patch('cli.confirm_action', return_value=True):
        cli.install_cli()
    
    mock_makedirs.assert_called_once()
    mock_copy.assert_called_once()
    mock_chmod.assert_called_once()
    
    captured = capsys.readouterr()
    assert "installed successfully" in captured.err

# Test the uninstall_cli function
@patch('os.path.exists', return_value=True)
@patch('os.remove')
def test_uninstall_cli(mock_remove, mock_exists, capsys):
    with patch('cli.confirm_action', return_value=True):
        cli.uninstall_cli()
    
    mock_remove.assert_called_once()
    
    captured = capsys.readouterr()
    assert "uninstalled successfully" in captured.err

# Test the main function with no arguments
@patch('sys.argv', ['cdevcontainer'])
@patch('argparse.ArgumentParser.parse_args')
@patch('cli.show_banner')
def test_main_no_args(mock_banner, mock_parse_args, capsys):
    mock_args = MagicMock()
    mock_args.command = None
    mock_parse_args.return_value = mock_args
    
    with pytest.raises(SystemExit):
        cli.main()
    
    mock_banner.assert_called_once()

# Test the main function with code command
@patch('sys.argv', ['cdevcontainer', 'code'])
@patch('argparse.ArgumentParser.parse_args')
@patch('cli.show_banner')
@patch('cli.handle_code')
def test_main_code(mock_handle_code, mock_banner, mock_parse_args):
    mock_args = MagicMock()
    mock_args.command = 'code'
    mock_args.func = cli.handle_code
    mock_parse_args.return_value = mock_args
    
    cli.main()
    
    mock_banner.assert_called_once()
    mock_handle_code.assert_called_once_with(mock_args)

# Test the handle_code function
@patch('cli.find_project_root', return_value="/test/path")
@patch('os.path.isfile', side_effect=[True, True])
@patch('os.path.getmtime', side_effect=[100, 200])
@patch('cli.generate_shell_env')
@patch('subprocess.Popen')
def test_handle_code(mock_popen, mock_generate, mock_getmtime, mock_isfile, mock_find_project_root, capsys):
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process
    
    args = MagicMock()
    args.project_root = "/test/path"
    
    cli.handle_code(args)
    
    mock_find_project_root.assert_called_once_with("/test/path")
    mock_generate.assert_called_once()
    mock_popen.assert_called_once()
    
    captured = capsys.readouterr()
    assert "Launching VS Code" in captured.err