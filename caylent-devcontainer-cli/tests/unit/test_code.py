"""Unit tests for the code command (S1.3.2)."""

from unittest.mock import MagicMock, patch

import pytest

from caylent_devcontainer_cli.commands.code import IDE_CONFIG, handle_code, register_command

# =============================================================================
# register_command tests
# =============================================================================


def test_register_command():
    """Test register_command creates the code parser with expected args."""
    mock_subparsers = MagicMock()
    mock_parser = MagicMock()
    mock_subparsers.add_parser.return_value = mock_parser

    register_command(mock_subparsers)

    mock_subparsers.add_parser.assert_called_once_with(
        "code", help="Launch IDE (VS Code, Cursor) with the devcontainer environment"
    )
    mock_parser.set_defaults.assert_called_once_with(func=handle_code)


def test_register_command_ide_choices():
    """Test register_command adds IDE choices correctly."""
    mock_subparsers = MagicMock()
    mock_parser = MagicMock()
    mock_subparsers.add_parser.return_value = mock_parser

    register_command(mock_subparsers)

    ide_call = None
    for call in mock_parser.add_argument.call_args_list:
        if call[0][0] == "--ide":
            ide_call = call
            break

    assert ide_call is not None
    assert ide_call[1]["choices"] == ["vscode", "cursor"]
    assert ide_call[1]["default"] == "vscode"


def test_register_command_has_regenerate_shell_env_flag():
    """Test register_command adds --regenerate-shell-env flag."""
    mock_subparsers = MagicMock()
    mock_parser = MagicMock()
    mock_subparsers.add_parser.return_value = mock_parser

    register_command(mock_subparsers)

    regen_call = None
    for call in mock_parser.add_argument.call_args_list:
        args = call[0]
        if "--regenerate-shell-env" in args:
            regen_call = call
            break

    assert regen_call is not None
    assert regen_call[1]["action"] == "store_true"


# =============================================================================
# IDE_CONFIG tests
# =============================================================================


def test_ide_config_structure():
    """Test that IDE_CONFIG has the expected structure."""
    assert "vscode" in IDE_CONFIG
    assert "cursor" in IDE_CONFIG

    for ide_key, config in IDE_CONFIG.items():
        assert "command" in config
        assert "name" in config
        assert "install_instructions" in config

    assert IDE_CONFIG["vscode"]["command"] == "code"
    assert IDE_CONFIG["vscode"]["name"] == "VS Code"
    assert IDE_CONFIG["cursor"]["command"] == "cursor"
    assert IDE_CONFIG["cursor"]["name"] == "Cursor"


# =============================================================================
# Missing file detection tests
# =============================================================================


@patch("caylent_devcontainer_cli.commands.code.resolve_project_root", return_value="/test/path")
@patch("os.path.isfile", return_value=False)
def test_missing_env_json_error(mock_isfile, mock_resolve, capsys):
    """Test error when devcontainer-environment-variables.json is missing."""
    args = MagicMock()
    args.project_root = "/test/path"
    args.regenerate_shell_env = False

    with pytest.raises(SystemExit):
        handle_code(args)

    captured = capsys.readouterr()
    assert "devcontainer-environment-variables.json" in captured.err
    assert "setup-devcontainer" in captured.err or "template load" in captured.err


@patch("caylent_devcontainer_cli.commands.code.resolve_project_root", return_value="/test/path")
@patch("os.path.isfile", side_effect=lambda p: "environment-variables" in p)
def test_missing_shell_env_error(mock_isfile, mock_resolve, capsys):
    """Test error when shell.env is missing."""
    args = MagicMock()
    args.project_root = "/test/path"
    args.regenerate_shell_env = False

    with pytest.raises(SystemExit):
        handle_code(args)

    captured = capsys.readouterr()
    assert "shell.env" in captured.err
    assert "setup-devcontainer" in captured.err or "template load" in captured.err


# =============================================================================
# Launch command tests — no sourcing shell.env
# =============================================================================


@patch("caylent_devcontainer_cli.commands.code.resolve_project_root", return_value="/test/path")
@patch("os.path.isfile", return_value=True)
@patch("shutil.which", return_value="/usr/bin/code")
@patch("subprocess.Popen")
def test_launch_command_no_source(mock_popen, mock_which, mock_isfile, mock_resolve, capsys):
    """Test that IDE launch does NOT source shell.env."""
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "vscode"
    args.regenerate_shell_env = False

    handle_code(args)

    cmd_args = mock_popen.call_args[0][0]
    assert "source" not in cmd_args
    assert "shell.env" not in cmd_args


@patch("caylent_devcontainer_cli.commands.code.resolve_project_root", return_value="/test/path")
@patch("os.path.isfile", return_value=True)
@patch("shutil.which", return_value="/usr/bin/code")
@patch("subprocess.Popen")
def test_launch_command_simple(mock_popen, mock_which, mock_isfile, mock_resolve, capsys):
    """Test that launch command is simply '<ide_command> <project_root>'."""
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "vscode"
    args.regenerate_shell_env = False

    handle_code(args)

    mock_popen.assert_called_once()
    call_args = mock_popen.call_args
    cmd = call_args[0][0]
    assert cmd == ["code", "/test/path"]


@patch("caylent_devcontainer_cli.commands.code.resolve_project_root", return_value="/test/path")
@patch("os.path.isfile", return_value=True)
@patch("shutil.which", return_value="/usr/bin/cursor")
@patch("subprocess.Popen")
def test_launch_cursor(mock_popen, mock_which, mock_isfile, mock_resolve, capsys):
    """Test that cursor IDE is launched correctly."""
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "cursor"
    args.regenerate_shell_env = False

    handle_code(args)

    call_args = mock_popen.call_args
    cmd = call_args[0][0]
    assert cmd == ["cursor", "/test/path"]

    captured = capsys.readouterr()
    assert "Cursor" in captured.err


# =============================================================================
# IDE not found tests
# =============================================================================


@patch("caylent_devcontainer_cli.commands.code.resolve_project_root", return_value="/test/path")
@patch("os.path.isfile", return_value=True)
@patch("shutil.which", return_value=None)
def test_ide_not_found(mock_which, mock_isfile, mock_resolve, capsys):
    """Test error when IDE command not in PATH."""
    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "vscode"
    args.regenerate_shell_env = False

    with pytest.raises(SystemExit):
        handle_code(args)

    captured = capsys.readouterr()
    assert "not found in PATH" in captured.err


# =============================================================================
# --regenerate-shell-env flag tests
# =============================================================================


@patch("caylent_devcontainer_cli.commands.code.resolve_project_root", return_value="/test/path")
@patch("os.path.isfile", side_effect=lambda p: "environment-variables" in p)
@patch("caylent_devcontainer_cli.commands.code.load_json_config")
@patch("caylent_devcontainer_cli.commands.code.write_shell_env")
@patch("shutil.which", return_value="/usr/bin/code")
@patch("subprocess.Popen")
def test_regenerate_shell_env_calls_write(
    mock_popen, mock_which, mock_write_shell, mock_load, mock_isfile, mock_resolve, capsys
):
    """Test --regenerate-shell-env reads JSON and calls write_shell_env."""
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process
    mock_load.return_value = {
        "containerEnv": {"KEY": "val"},
        "cli_version": "2.0.0",
        "template_name": "test",
        "template_path": "/some/path",
    }

    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "vscode"
    args.regenerate_shell_env = True

    handle_code(args)

    mock_write_shell.assert_called_once()
    mock_load.assert_called_once()


@patch("caylent_devcontainer_cli.commands.code.resolve_project_root", return_value="/test/path")
@patch("os.path.isfile", return_value=False)
def test_regenerate_shell_env_requires_json(mock_isfile, mock_resolve, capsys):
    """Test --regenerate-shell-env fails if JSON file is missing."""
    args = MagicMock()
    args.project_root = "/test/path"
    args.regenerate_shell_env = True

    with pytest.raises(SystemExit):
        handle_code(args)

    captured = capsys.readouterr()
    assert "devcontainer-environment-variables.json" in captured.err


@patch("caylent_devcontainer_cli.commands.code.resolve_project_root", return_value="/test/path")
@patch("os.path.isfile", side_effect=lambda p: "environment-variables" in p)
@patch("caylent_devcontainer_cli.commands.code.load_json_config")
@patch("caylent_devcontainer_cli.commands.code.write_shell_env")
@patch("shutil.which", return_value="/usr/bin/code")
@patch("subprocess.Popen")
def test_regenerate_does_not_modify_json(
    mock_popen, mock_which, mock_write_shell, mock_load, mock_isfile, mock_resolve, capsys
):
    """Test --regenerate-shell-env does not write to JSON file."""
    mock_process = MagicMock()
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process
    mock_load.return_value = {
        "containerEnv": {"KEY": "val"},
        "cli_version": "2.0.0",
        "template_name": "test",
        "template_path": "/some/path",
    }

    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "vscode"
    args.regenerate_shell_env = True

    with patch("caylent_devcontainer_cli.utils.fs.write_json_file") as mock_write_json:
        handle_code(args)
        mock_write_json.assert_not_called()


# =============================================================================
# Launch failure test
# =============================================================================


@patch("caylent_devcontainer_cli.commands.code.resolve_project_root", return_value="/test/path")
@patch("os.path.isfile", return_value=True)
@patch("shutil.which", return_value="/usr/bin/code")
@patch("subprocess.Popen", side_effect=Exception("Launch failed"))
def test_launch_failure(mock_popen, mock_which, mock_isfile, mock_resolve, capsys):
    """Test error when IDE launch fails."""
    args = MagicMock()
    args.project_root = "/test/path"
    args.ide = "vscode"
    args.regenerate_shell_env = False

    with pytest.raises(SystemExit):
        handle_code(args)

    captured = capsys.readouterr()
    assert "Failed to launch" in captured.err


# =============================================================================
# Missing vars check tests (kept for backward compat — S1.3.3 will rewrite)
# =============================================================================


@patch(
    "caylent_devcontainer_cli.utils.env.EXAMPLE_ENV_VALUES",
    {"EXISTING_VAR": "default1", "MISSING_VAR": "default2", "COMPLEX_VAR": {"key": "value"}},
)
def test_get_missing_env_vars():
    """Test checking for missing environment variables."""
    from caylent_devcontainer_cli.utils.env import get_missing_env_vars

    container_env = {"EXISTING_VAR": "value"}
    missing = get_missing_env_vars(container_env)

    assert missing == {"MISSING_VAR": "default2"}


@patch("questionary.select")
@patch("sys.exit")
def test_prompt_upgrade_or_continue_exit(mock_exit, mock_select):
    """Test prompting user to exit and upgrade."""
    from caylent_devcontainer_cli.commands.code import prompt_upgrade_or_continue

    mock_select.return_value.ask.return_value = "Exit and upgrade the profile first (recommended)"

    prompt_upgrade_or_continue(["VAR1", "VAR2"], "test-template")

    mock_exit.assert_called_once_with(0)


@patch("questionary.select")
def test_prompt_upgrade_or_continue_continue(mock_select):
    """Test prompting user to continue without upgrade."""
    from caylent_devcontainer_cli.commands.code import prompt_upgrade_or_continue

    mock_select.return_value.ask.return_value = "Continue without the upgrade (may cause issues)"

    prompt_upgrade_or_continue(["VAR1", "VAR2"])

    mock_select.assert_called_once()
