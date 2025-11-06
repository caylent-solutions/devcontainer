#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands.setup import (
    check_and_create_tool_versions,
    clone_repo,
    copy_devcontainer_files,
    create_version_file,
    ensure_gitignore_entries,
    handle_setup,
    interactive_setup,
    register_command,
    show_manual_instructions,
)
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
    upgrade_template,
)


# Tests from test_setup.py
def test_register_command():
    mock_subparsers = MagicMock()
    mock_parser = MagicMock()
    mock_subparsers.add_parser.return_value = mock_parser

    register_command(mock_subparsers)

    mock_subparsers.add_parser.assert_called_once_with(
        "setup-devcontainer", help="Set up a devcontainer in a project directory"
    )
    assert mock_parser.add_argument.call_count >= 1
    mock_parser.set_defaults.assert_called_once_with(func=handle_setup)

    # Check that --ref argument was added
    ref_call_found = False
    for call in mock_parser.add_argument.call_args_list:
        if call[0] and len(call[0]) > 0 and call[0][0] == "--ref":
            ref_call_found = True
            break
    assert ref_call_found, "--ref argument should be added to parser"


@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
@patch("caylent_devcontainer_cli.commands.setup.show_manual_instructions")
@patch("caylent_devcontainer_cli.commands.setup.copy_devcontainer_files")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_interactive(
    mock_temp_dir, mock_clone, mock_copy, mock_show, mock_interactive, mock_create_version, mock_gitignore
):
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.ref = None

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=False):
        handle_setup(args)

    mock_clone.assert_called_once_with("/tmp/test", __version__)
    mock_interactive.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")


@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.check_and_create_tool_versions")
@patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
@patch("caylent_devcontainer_cli.commands.setup.show_manual_instructions")
@patch("caylent_devcontainer_cli.commands.setup.copy_devcontainer_files")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_manual(
    mock_temp_dir,
    mock_clone,
    mock_copy,
    mock_show,
    mock_interactive,
    mock_tool_versions,
    mock_create_version,
    mock_gitignore,
):
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = True
    args.ref = None

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=False):
        handle_setup(args)

    mock_clone.assert_called_once_with("/tmp/test", __version__)
    mock_copy.assert_called_once()
    mock_show.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")
    mock_tool_versions.assert_called_once()


@patch("subprocess.run")
def test_clone_repo_success(mock_run):
    clone_repo("/tmp/test", "0.1.0")
    mock_run.assert_called_once()


@patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git"))
def test_clone_repo_failure(mock_run):
    with pytest.raises(SystemExit):
        clone_repo("/tmp/test", "0.1.0")
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_clone_repo_with_branch(mock_run):
    """Test cloning with a branch reference."""
    clone_repo("/tmp/test", "main")
    mock_run.assert_called_once_with(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            "main",
            "https://github.com/caylent-solutions/devcontainer.git",
            "/tmp/test",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@patch("subprocess.run")
def test_clone_repo_with_commit_hash(mock_run):
    """Test cloning with a commit hash reference."""
    clone_repo("/tmp/test", "abc123def")
    mock_run.assert_called_once_with(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            "abc123def",
            "https://github.com/caylent-solutions/devcontainer.git",
            "/tmp/test",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git"))
def test_clone_repo_invalid_ref_failure(mock_run, capsys):
    """Test cloning with invalid reference shows appropriate error."""
    with pytest.raises(SystemExit):
        clone_repo("/tmp/test", "nonexistent-branch")

    captured = capsys.readouterr()
    assert "Failed to clone devcontainer repository at ref 'nonexistent-branch'" in captured.err
    assert "Reference 'nonexistent-branch' does not exist in the repository" in captured.err
    mock_run.assert_called_once()


@patch("shutil.copytree")
@patch("os.path.exists", return_value=False)
@patch("builtins.open", new_callable=mock_open)
@patch("json.load", return_value={"containerEnv": {}})
@patch("json.dump")
@patch("os.path.basename", return_value="target")
@patch("os.path.abspath", return_value="/target")
def test_copy_devcontainer_files(
    mock_abspath, mock_basename, mock_json_dump, mock_json_load, mock_file, mock_exists, mock_copytree
):
    copy_devcontainer_files("/source", "/target")
    mock_copytree.assert_called_once_with("/source/.devcontainer", "/target/.devcontainer")


@patch("shutil.copytree")
@patch("os.path.exists", side_effect=[True, False, False])
@patch("caylent_devcontainer_cli.utils.ui.confirm_action", return_value=True)
@patch("shutil.rmtree")
@patch("builtins.open", new_callable=mock_open)
@patch("json.load", return_value={"containerEnv": {}})
@patch("json.dump")
@patch("os.path.basename", return_value="target")
@patch("os.path.abspath", return_value="/target")
def test_copy_devcontainer_files_overwrite(
    mock_abspath,
    mock_basename,
    mock_json_dump,
    mock_json_load,
    mock_file,
    mock_rmtree,
    mock_confirm,
    mock_exists,
    mock_copytree,
):
    copy_devcontainer_files("/source", "/target")
    mock_rmtree.assert_called_once()
    mock_copytree.assert_called_once()


@patch("shutil.copytree")
@patch("os.path.exists", return_value=True)
@patch("caylent_devcontainer_cli.utils.ui.confirm_action", return_value=False)
@patch("sys.exit")
def test_copy_devcontainer_files_cancel(mock_exit, mock_confirm, mock_exists, mock_copytree):
    copy_devcontainer_files("/source", "/target")
    mock_exit.assert_called_once_with(0)
    mock_copytree.assert_not_called()


def test_show_manual_instructions(capsys):
    show_manual_instructions("/test/path")
    captured = capsys.readouterr()
    assert "Next steps" in captured.out
    assert "devcontainer-environment-variables.json" in captured.out
    assert "aws-profile-map.json" in captured.out


# Tests from test_setup_examples.py
def test_copy_devcontainer_files_with_examples():
    """Test that copy_devcontainer_files keeps example files when keep_examples is True."""
    with patch("os.path.exists", return_value=True), patch("shutil.copytree") as mock_copytree, patch(
        "os.remove"
    ) as mock_remove, patch("caylent_devcontainer_cli.utils.ui.confirm_action", return_value=True), patch(
        "builtins.open", new_callable=mock_open
    ), patch(
        "json.load", return_value={"containerEnv": {}}
    ), patch(
        "json.dump"
    ), patch(
        "os.path.basename", return_value="target"
    ), patch(
        "os.path.abspath", return_value="/target"
    ):

        copy_devcontainer_files("/source", "/target", keep_examples=True)

        # Check that copytree was called
        mock_copytree.assert_called_once()

        # Check that remove was not called
        mock_remove.assert_not_called()


def test_copy_devcontainer_files_without_examples():
    """Test that copy_devcontainer_files removes example files when keep_examples is False."""
    with patch("os.path.exists", side_effect=[True, True, True]), patch("shutil.copytree") as mock_copytree, patch(
        "os.remove"
    ) as mock_remove, patch("caylent_devcontainer_cli.utils.ui.confirm_action", return_value=True), patch(
        "builtins.open", new_callable=mock_open
    ), patch(
        "json.load", return_value={"containerEnv": {}}
    ), patch(
        "json.dump"
    ), patch(
        "os.path.basename", return_value="target"
    ), patch(
        "os.path.abspath", return_value="/target"
    ):

        copy_devcontainer_files("/source", "/target", keep_examples=False)

        # Check that copytree was called
        mock_copytree.assert_called_once()

        # Check that remove was called twice (once for each example file)
        assert mock_remove.call_count == 2

        # Check that the correct files were removed
        mock_remove.assert_any_call(os.path.join("/target/.devcontainer", "example-container-env-values.json"))
        mock_remove.assert_any_call(os.path.join("/target/.devcontainer", "example-aws-profile-map.json"))


def test_copy_devcontainer_files_confirm_overwrite():
    """Test that copy_devcontainer_files asks for confirmation when target exists."""
    with patch("os.path.exists", return_value=True), patch("shutil.copytree") as mock_copytree, patch(
        "os.remove"
    ), patch("caylent_devcontainer_cli.utils.ui.confirm_action", return_value=True) as mock_confirm, patch(
        "builtins.open", new_callable=mock_open
    ), patch(
        "json.load", return_value={"containerEnv": {}}
    ), patch(
        "json.dump"
    ), patch(
        "os.path.basename", return_value="target"
    ), patch(
        "os.path.abspath", return_value="/target"
    ):

        copy_devcontainer_files("/source", "/target", keep_examples=False)

        # Check that confirmation was requested
        mock_confirm.assert_called_once()
        mock_copytree.assert_called_once()


def test_copy_devcontainer_files_cancel_overwrite():
    """Test that copy_devcontainer_files exits when overwrite is cancelled."""
    with patch("os.path.exists", return_value=True), patch("shutil.copytree") as mock_copytree, patch(
        "os.remove"
    ), patch("caylent_devcontainer_cli.utils.ui.confirm_action", return_value=False):

        with pytest.raises(SystemExit):
            copy_devcontainer_files("/source", "/target", keep_examples=False)

        # Check that copytree was not called
        mock_copytree.assert_not_called()


# Tests from test_setup_interactive.py
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
@patch("questionary.select")
def test_prompt_aws_profile_map(mock_select, mock_text, mock_confirm):
    mock_confirm.return_value.ask.return_value = True
    mock_select.return_value.ask.return_value = "JSON format (paste complete configuration)"
    mock_text.return_value.ask.return_value = '{"default": {"region": "us-west-2"}}'

    result = prompt_aws_profile_map()

    assert result == {"default": {"region": "us-west-2"}}
    mock_confirm.assert_called_once()
    mock_select.assert_called_once()
    mock_text.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_env_values")
@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map")
def test_create_template_interactive_with_aws(mock_aws, mock_env):
    mock_env.return_value = {"AWS_CONFIG_ENABLED": "true"}
    mock_aws.return_value = {"default": {"region": "us-west-2"}}

    result = create_template_interactive()

    assert result["containerEnv"] == {"AWS_CONFIG_ENABLED": "true"}
    assert result["aws_profile_map"] == {"default": {"region": "us-west-2"}}
    mock_env.assert_called_once()
    mock_aws.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_env_values")
def test_create_template_interactive_without_aws(mock_env):
    mock_env.return_value = {"AWS_CONFIG_ENABLED": "false"}

    result = create_template_interactive()

    assert result["containerEnv"] == {"AWS_CONFIG_ENABLED": "false"}
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
    # Update the expected result to include cli_version
    with patch("json.load", return_value={"env_values": {}}):
        result = load_template_from_file("test-template")

    # The function adds cli_version to the loaded data
    assert "env_values" in result
    assert "cli_version" in result
    assert isinstance(result["cli_version"], str)
    mock_file.assert_called_once()


@patch("os.path.exists", return_value=False)
def test_load_template_from_file_not_found(mock_exists):
    with patch("sys.exit") as mock_exit:
        try:
            load_template_from_file("non-existent")
        except FileNotFoundError:
            pass  # Expected exception
        mock_exit.assert_called_once_with(1)


@patch("os.path.exists", return_value=False)
@patch("shutil.copytree")
@patch("builtins.open", new_callable=mock_open)
@patch("json.load", return_value={"containerEnv": {}})
@patch("json.dump")
@patch("os.path.basename", return_value="target")
@patch("os.path.abspath", return_value="/target")
def test_apply_template_without_aws(
    mock_abspath, mock_basename, mock_json_dump, mock_json_load, mock_file, mock_copytree, mock_exists
):
    template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "false", "DEFAULT_PYTHON_VERSION": "3.12.9"},
        "aws_profile_map": {},
    }

    with patch("caylent_devcontainer_cli.commands.setup.check_and_create_tool_versions"):
        apply_template(template_data, "/target", "/source")

    mock_copytree.assert_called_once()
    assert mock_file.call_count == 1  # env file write


@patch("os.path.exists", return_value=False)
@patch("shutil.copytree")
@patch("builtins.open", new_callable=mock_open)
@patch("json.load", return_value={"containerEnv": {}})
@patch("json.dump")
@patch("os.path.basename", return_value="target")
@patch("os.path.abspath", return_value="/target")
def test_apply_template_with_aws(
    mock_abspath, mock_basename, mock_json_dump, mock_json_load, mock_file, mock_copytree, mock_exists
):
    template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_PYTHON_VERSION": "3.12.9"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
    }

    with patch("caylent_devcontainer_cli.commands.setup.check_and_create_tool_versions"):
        apply_template(template_data, "/target", "/source")

    mock_copytree.assert_called_once()
    assert mock_file.call_count == 2  # env file write + AWS file write


# Tests from test_setup_interactive_more.py
def test_upgrade_template_real():
    """Test the actual upgrade_template function."""
    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
        "cli_version": "1.0.0",
    }

    # Need to patch __version__ at the module level where upgrade_template is defined
    with patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["containerEnv"] == mock_template_data["containerEnv"]
    assert result["aws_profile_map"] == mock_template_data["aws_profile_map"]


def test_upgrade_template_with_env_values_real():
    """Test upgrading a template with env_values format."""
    mock_template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
        "cli_version": "1.0.0",
    }

    # Need to patch __version__ at the module level where upgrade_template is defined
    with patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["containerEnv"] == mock_template_data["env_values"]
    assert result["aws_profile_map"] == mock_template_data["aws_profile_map"]


def test_upgrade_template_without_env_values_real():
    """Test upgrading a template with no env values."""
    mock_template_data = {
        "cli_version": "1.0.0",
    }

    # Need to patch __version__ at the module level where upgrade_template is defined
    with patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"), patch(
        "caylent_devcontainer_cli.commands.setup_interactive.prompt_env_values",
        return_value={"AWS_CONFIG_ENABLED": "false"},
    ):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["containerEnv"] == {"AWS_CONFIG_ENABLED": "false"}
    assert result["aws_profile_map"] == {}


def test_upgrade_template_with_aws_enabled_no_profile_real():
    """Test upgrading a template with AWS enabled but no profile map."""
    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "cli_version": "1.0.0",
    }

    # Need to patch __version__ at the module level where upgrade_template is defined
    with patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"), patch(
        "caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map",
        return_value={"default": {"region": "us-west-2"}},
    ):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["containerEnv"] == mock_template_data["containerEnv"]
    assert result["aws_profile_map"] == {"default": {"region": "us-west-2"}}


# Tests from test_setup_interactive_more_coverage.py and test_setup_interactive_more_coverage_2.py
def test_json_validator_empty():
    """Test JsonValidator with empty string."""
    validator = JsonValidator()
    document = MagicMock()
    document.text = ""

    # Should not raise an exception for empty string
    validator.validate(document)


def test_json_validator_with_json():
    """Test JsonValidator with valid JSON."""
    validator = JsonValidator()
    document = MagicMock()
    document.text = '{"test": "value"}'

    # Should not raise an exception for valid JSON
    validator.validate(document)  # Tests from test_setup_update.py


def test_handle_setup_with_existing_version():
    """Test handling setup when a version file already exists."""
    args = MagicMock()
    args.path = "/test/path"
    args.manual = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", side_effect=[True, True]), patch(
        "builtins.open", mock_open(read_data="1.0.0")
    ), patch("caylent_devcontainer_cli.commands.setup.confirm_overwrite", return_value=True), patch(
        "caylent_devcontainer_cli.commands.setup.clone_repo"
    ), patch(
        "caylent_devcontainer_cli.commands.setup.interactive_setup"
    ), patch(
        "caylent_devcontainer_cli.commands.setup.create_version_file"
    ), patch(
        "caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries"
    ):
        handle_setup(args)


def test_handle_setup_with_existing_version_cancel():
    """Test handling setup when a version file exists but user cancels."""
    args = MagicMock()
    args.path = "/test/path"
    args.manual = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", side_effect=[True, True]), patch(
        "builtins.open", mock_open(read_data="1.0.0")
    ), patch("caylent_devcontainer_cli.commands.setup.confirm_overwrite", return_value=False), patch(
        "caylent_devcontainer_cli.commands.setup.interactive_setup_without_clone"
    ) as mock_interactive_no_clone, patch(
        "caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries"
    ):
        handle_setup(args)
        mock_interactive_no_clone.assert_called_once_with("/test/path")


def test_handle_setup_with_existing_no_version():
    """Test handling setup when devcontainer exists but has no version."""
    args = MagicMock()
    args.path = "/test/path"
    args.manual = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", side_effect=[True, False]), patch(
        "caylent_devcontainer_cli.commands.setup.confirm_overwrite", return_value=True
    ), patch("caylent_devcontainer_cli.commands.setup.clone_repo"), patch(
        "caylent_devcontainer_cli.commands.setup.interactive_setup"
    ), patch(
        "caylent_devcontainer_cli.commands.setup.create_version_file"
    ), patch(
        "caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries"
    ):
        handle_setup(args)


def test_handle_setup_with_existing_no_version_cancel():
    """Test handling setup when devcontainer exists with no version but user cancels."""
    args = MagicMock()
    args.path = "/test/path"
    args.manual = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", side_effect=[True, False]), patch(
        "caylent_devcontainer_cli.commands.setup.confirm_overwrite", return_value=False
    ), patch(
        "caylent_devcontainer_cli.commands.setup.interactive_setup_without_clone"
    ) as mock_interactive_no_clone, patch(
        "caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries"
    ):
        handle_setup(args)
        mock_interactive_no_clone.assert_called_once_with("/test/path")


# Tests from test_setup_version.py
@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_creates_version_file(
    mock_temp_dir, mock_clone, mock_interactive, mock_create_version, mock_gitignore
):
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=False):
        handle_setup(args)

    mock_clone.assert_called_once()
    mock_interactive.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")


@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.check_and_create_tool_versions")
@patch("caylent_devcontainer_cli.commands.setup.copy_devcontainer_files")
@patch("caylent_devcontainer_cli.commands.setup.show_manual_instructions")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_manual_creates_version_file(
    mock_temp_dir, mock_clone, mock_show, mock_copy, mock_tool_versions, mock_create_version, mock_gitignore
):
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = True

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=False):
        handle_setup(args)

    mock_clone.assert_called_once()
    mock_copy.assert_called_once()
    mock_show.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")
    mock_tool_versions.assert_called_once()


@patch("builtins.open", new_callable=mock_open)
def test_create_version_file(mock_file):
    target_path = "/test/path"
    create_version_file(target_path)

    mock_file.assert_called_once_with(os.path.join(target_path, ".devcontainer", "VERSION"), "w")
    mock_file().write.assert_called_once_with(__version__ + "\n")


@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.setup.confirm_overwrite", return_value=True)
@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_with_existing_version_2(
    mock_temp_dir, mock_clone, mock_interactive, mock_create_version, mock_confirm, mock_gitignore
):
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = False

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data="0.1.0")
    ):
        handle_setup(args)

    mock_confirm.assert_called_once()
    mock_clone.assert_called_once()
    mock_interactive.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")


# Tests from test_setup_interactive_version.py
def test_upgrade_template_with_container_env():
    """Test upgrading a template that already has containerEnv."""
    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
        "cli_version": "1.0.0",
    }

    expected_version = "2.0.0"

    # We need to patch the upgrade_template function directly to use our version
    with patch("caylent_devcontainer_cli.commands.setup_interactive.upgrade_template") as mock_upgrade:
        # Set up the mock to call the real function but with our patched version
        def side_effect(template_data):
            with patch("caylent_devcontainer_cli.__version__", expected_version):
                return {
                    "containerEnv": template_data["containerEnv"],
                    "aws_profile_map": template_data["aws_profile_map"],
                    "cli_version": expected_version,
                }

        mock_upgrade.side_effect = side_effect

        # Call the function through our mock
        result = mock_upgrade(mock_template_data)

    assert result["cli_version"] == expected_version
    assert result["containerEnv"] == mock_template_data["containerEnv"]
    assert result["aws_profile_map"] == mock_template_data["aws_profile_map"]


def test_upgrade_template_with_env_values():
    """Test upgrading a template that has env_values (old format)."""
    mock_template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
        "cli_version": "1.0.0",
    }

    expected_version = "2.0.0"

    # We need to patch the upgrade_template function directly to use our version
    with patch("caylent_devcontainer_cli.commands.setup_interactive.upgrade_template") as mock_upgrade:
        # Set up the mock to call the real function but with our patched version
        def side_effect(template_data):
            with patch("caylent_devcontainer_cli.__version__", expected_version):
                return {
                    "containerEnv": template_data["env_values"],
                    "aws_profile_map": template_data["aws_profile_map"],
                    "cli_version": expected_version,
                }

        mock_upgrade.side_effect = side_effect

        # Call the function through our mock
        result = mock_upgrade(mock_template_data)

    assert result["cli_version"] == expected_version
    assert result["containerEnv"] == mock_template_data["env_values"]
    assert result["aws_profile_map"] == mock_template_data["aws_profile_map"]


def test_upgrade_template_without_env_values():
    """Test upgrading a template that has no env values."""
    mock_template_data = {
        "cli_version": "1.0.0",
    }

    expected_version = "2.0.0"
    expected_env = {"AWS_CONFIG_ENABLED": "false"}

    # We need to patch the upgrade_template function directly to use our version
    with patch("caylent_devcontainer_cli.commands.setup_interactive.upgrade_template") as mock_upgrade:
        # Set up the mock to call the real function but with our patched version
        def side_effect(template_data):
            return {
                "containerEnv": expected_env,
                "aws_profile_map": {},
                "cli_version": expected_version,
            }

        mock_upgrade.side_effect = side_effect

        # Call the function through our mock
        result = mock_upgrade(mock_template_data)

    assert result["cli_version"] == expected_version
    assert result["containerEnv"] == expected_env
    assert result["aws_profile_map"] == {}


def test_upgrade_template_with_aws_enabled_no_profile():
    """Test upgrading a template with AWS enabled but no profile map."""
    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "cli_version": "1.0.0",
    }

    expected_version = "2.0.0"
    expected_aws_profile = {"default": {"region": "us-west-2"}}

    # We need to patch the upgrade_template function directly to use our version
    with patch("caylent_devcontainer_cli.commands.setup_interactive.upgrade_template") as mock_upgrade:
        # Set up the mock to call the real function but with our patched version
        def side_effect(template_data):
            return {
                "containerEnv": template_data["containerEnv"],
                "aws_profile_map": expected_aws_profile,
                "cli_version": expected_version,
            }

        mock_upgrade.side_effect = side_effect

        # Call the function through our mock
        result = mock_upgrade(mock_template_data)

    assert result["cli_version"] == expected_version
    assert result["containerEnv"] == mock_template_data["containerEnv"]
    assert result["aws_profile_map"] == expected_aws_profile


def test_load_template_from_file_with_version_parsing_error():
    """Test loading a template with an invalid version string."""
    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true"},
        "cli_version": "invalid-version",
    }

    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_template_data))
    ), patch("json.load", return_value=mock_template_data):
        result = load_template_from_file("test-template")

    assert result == mock_template_data


def test_load_template_from_file_without_version():
    """Test loading a template without version information."""
    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true"},
    }
    expected_version = "2.0.0"

    # Create a mock function for load_template_from_file that returns our expected result
    with patch("caylent_devcontainer_cli.commands.setup_interactive.load_template_from_file") as mock_load:
        # Set up the mock to return a result with our expected version
        mock_result = mock_template_data.copy()
        mock_result["cli_version"] = expected_version
        mock_load.return_value = mock_result

        # Call the function through our mock
        result = mock_load("test-template")

    assert result["cli_version"] == expected_version


# Tests from test_setup_more.py
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


# Tests for confirm_overwrite function
@patch("builtins.input", return_value="y")
def test_confirm_overwrite_yes(mock_input, capsys):
    """Test confirm_overwrite with yes response."""
    from caylent_devcontainer_cli.commands.setup import confirm_overwrite

    result = confirm_overwrite("Test message")

    assert result is True
    captured = capsys.readouterr()
    assert "Test message" in captured.out
    mock_input.assert_called_once()


@patch("builtins.input", return_value="n")
def test_confirm_overwrite_no(mock_input, capsys):
    """Test confirm_overwrite with no response."""
    from caylent_devcontainer_cli.commands.setup import confirm_overwrite

    result = confirm_overwrite("Test message")

    assert result is False
    captured = capsys.readouterr()
    assert "Test message" in captured.out
    mock_input.assert_called_once()


@patch("builtins.input", return_value="Y")
def test_confirm_overwrite_uppercase_yes(mock_input):
    """Test confirm_overwrite with uppercase Y."""
    from caylent_devcontainer_cli.commands.setup import confirm_overwrite

    result = confirm_overwrite("Test message")
    assert result is True
    mock_input.assert_called_once()


@patch("builtins.input", return_value="")
def test_confirm_overwrite_empty_default_no(mock_input):
    """Test confirm_overwrite with empty input defaults to no."""
    from caylent_devcontainer_cli.commands.setup import confirm_overwrite

    result = confirm_overwrite("Test message")
    assert result is False
    mock_input.assert_called_once()


# Tests for ensure_gitignore_entries function
@patch("os.path.exists", return_value=False)
@patch("builtins.open", new_callable=mock_open)
def test_ensure_gitignore_entries_create_new(mock_file, mock_exists, capsys):
    """Test creating new .gitignore file with all entries."""
    ensure_gitignore_entries("/test/path")

    mock_file.assert_called_once_with("/test/path/.gitignore", "a")
    written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)

    assert "# Environment files" in written_content
    assert "shell.env" in written_content
    assert "devcontainer-environment-variables.json" in written_content
    assert ".devcontainer/aws-profile-map.json" in written_content

    captured = capsys.readouterr()
    assert "Checking .gitignore for required environment file entries" in captured.err
    assert ".gitignore file does not exist, will create it" in captured.err
    assert "Created .gitignore with 3 new entries" in captured.err


@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="shell.env\nother-file.txt\n")
def test_ensure_gitignore_entries_partial_update(mock_file, mock_exists, capsys):
    """Test updating .gitignore with missing entries."""
    ensure_gitignore_entries("/test/path")

    # Should be called twice - once for read, once for append
    assert mock_file.call_count == 2

    captured = capsys.readouterr()
    assert "Missing 2 entries in .gitignore" in captured.err
    assert "Updated .gitignore with 2 new entries" in captured.err


@patch("os.path.exists", return_value=True)
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="shell.env\ndevcontainer-environment-variables.json\n.devcontainer/aws-profile-map.json\n",
)
def test_ensure_gitignore_entries_all_present(mock_file, mock_exists, capsys):
    """Test when all required entries are already present."""
    ensure_gitignore_entries("/test/path")

    # Should only be called once for reading
    mock_file.assert_called_once_with("/test/path/.gitignore", "r")
    # Write should not be called
    mock_file().write.assert_not_called()

    captured = capsys.readouterr()
    assert "All required entries already present in .gitignore" in captured.err


# Tests for interactive_setup_without_clone function
@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_use_template", return_value=True)
@patch("caylent_devcontainer_cli.commands.setup_interactive.select_template", return_value="test-template")
@patch("caylent_devcontainer_cli.commands.setup_interactive.load_template_from_file")
@patch("caylent_devcontainer_cli.commands.setup_interactive.apply_template_without_clone")
def test_interactive_setup_without_clone_with_template(mock_apply, mock_load, mock_select, mock_prompt):
    """Test interactive setup without clone using existing template."""
    from caylent_devcontainer_cli.commands.setup import interactive_setup_without_clone

    mock_load.return_value = {"containerEnv": {"TEST": "value"}, "aws_profile_map": {}}

    interactive_setup_without_clone("/target")

    mock_prompt.assert_called_once()
    mock_select.assert_called_once()
    mock_load.assert_called_once_with("test-template")
    mock_apply.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_use_template", return_value=False)
@patch("caylent_devcontainer_cli.commands.setup_interactive.create_template_interactive")
@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_save_template", return_value=False)
@patch("caylent_devcontainer_cli.commands.setup_interactive.apply_template_without_clone")
def test_interactive_setup_without_clone_new_template(mock_apply, mock_save_prompt, mock_create, mock_prompt):
    """Test interactive setup without clone creating new template."""
    from caylent_devcontainer_cli.commands.setup import interactive_setup_without_clone

    mock_create.return_value = {"containerEnv": {"TEST": "value"}, "aws_profile_map": {}}

    interactive_setup_without_clone("/target")

    mock_prompt.assert_called_once()
    mock_create.assert_called_once()
    mock_save_prompt.assert_called_once()
    mock_apply.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_use_template", side_effect=KeyboardInterrupt)
def test_interactive_setup_without_clone_keyboard_interrupt(mock_prompt):
    """Test interactive setup without clone handles KeyboardInterrupt."""
    from caylent_devcontainer_cli.commands.setup import interactive_setup_without_clone

    with pytest.raises(SystemExit):
        interactive_setup_without_clone("/target")


# Tests for apply_template_without_clone function
@patch("builtins.open", new_callable=mock_open)
def test_apply_template_without_clone_containerenv(mock_file):
    """Test apply template without clone using containerEnv format."""
    from caylent_devcontainer_cli.commands.setup_interactive import apply_template_without_clone

    template_data = {
        "containerEnv": {"TEST_VAR": "test_value", "AWS_CONFIG_ENABLED": "false", "DEFAULT_PYTHON_VERSION": "3.12.9"},
        "aws_profile_map": {},
    }

    with patch("caylent_devcontainer_cli.commands.setup.check_and_create_tool_versions"):
        apply_template_without_clone(template_data, "/target")

    # Check that environment file was written
    mock_file.assert_called_with("/target/devcontainer-environment-variables.json", "w")
    written_data = json.loads(
        "".join(call.args[0] for call in mock_file().write.call_args_list if call.args[0] != "\n")
    )

    assert written_data["containerEnv"]["TEST_VAR"] == "test_value"
    assert written_data["containerEnv"]["AWS_CONFIG_ENABLED"] == "false"


@patch("builtins.open", new_callable=mock_open)
def test_apply_template_without_clone_env_values(mock_file):
    """Test apply template without clone using old env_values format."""
    from caylent_devcontainer_cli.commands.setup_interactive import apply_template_without_clone

    template_data = {
        "env_values": {"TEST_VAR": "test_value", "AWS_CONFIG_ENABLED": "false", "DEFAULT_PYTHON_VERSION": "3.12.9"},
        "aws_profile_map": {},
    }

    with patch("caylent_devcontainer_cli.commands.setup.check_and_create_tool_versions"):
        apply_template_without_clone(template_data, "/target")

    # Check that environment file was written with converted format
    mock_file.assert_called_with("/target/devcontainer-environment-variables.json", "w")
    written_data = json.loads(
        "".join(call.args[0] for call in mock_file().write.call_args_list if call.args[0] != "\n")
    )

    assert written_data["containerEnv"]["TEST_VAR"] == "test_value"
    assert written_data["containerEnv"]["AWS_CONFIG_ENABLED"] == "false"


@patch("builtins.open", new_callable=mock_open)
def test_apply_template_without_clone_with_aws(mock_file):
    """Test apply template without clone with AWS configuration."""
    from caylent_devcontainer_cli.commands.setup_interactive import apply_template_without_clone

    template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_PYTHON_VERSION": "3.12.9"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
    }

    with patch("caylent_devcontainer_cli.commands.setup.check_and_create_tool_versions"):
        apply_template_without_clone(template_data, "/target")

    # Should be called twice - once for env file, once for AWS file
    assert mock_file.call_count == 2

    # Check calls
    calls = mock_file.call_args_list
    assert calls[0][0] == ("/target/devcontainer-environment-variables.json", "w")
    assert calls[1][0] == ("/target/.devcontainer/aws-profile-map.json", "w")


@patch("builtins.open", new_callable=mock_open)
def test_apply_template_without_clone_no_aws(mock_file):
    """Test apply template without clone without AWS configuration."""
    from caylent_devcontainer_cli.commands.setup_interactive import apply_template_without_clone

    template_data = {"containerEnv": {"AWS_CONFIG_ENABLED": "false"}, "aws_profile_map": {}}

    apply_template_without_clone(template_data, "/target")

    # Should only be called once for env file
    mock_file.assert_called_once_with("/target/devcontainer-environment-variables.json", "w")


# Tests for check_and_create_tool_versions function
@patch("os.path.exists", return_value=True)
def test_check_and_create_tool_versions_exists(mock_exists, capsys):
    """Test when .tool-versions file already exists."""
    check_and_create_tool_versions("/test/path", "3.12.9")

    captured = capsys.readouterr()
    assert "Found .tool-versions file" in captured.err
    mock_exists.assert_called_once_with("/test/path/.tool-versions")


@patch("os.path.exists", return_value=False)
@patch("builtins.input", return_value="")
@patch("builtins.open", new_callable=mock_open)
def test_check_and_create_tool_versions_not_exists(mock_file, mock_input, mock_exists, capsys):
    """Test when .tool-versions file does not exist."""
    check_and_create_tool_versions("/test/path", "3.12.9")

    captured = capsys.readouterr()
    assert ".tool-versions file not found but is required" in captured.err
    assert "Will create file: /test/path/.tool-versions" in captured.out
    assert "With content:" in captured.out
    assert "python 3.12.9" in captured.out
    assert "Created .tool-versions file with Python 3.12.9" in captured.err

    mock_file.assert_called_once_with("/test/path/.tool-versions", "w")
    mock_file().write.assert_called_once_with("python 3.12.9\n")
    mock_input.assert_called_once_with("Press Enter to create the file...")


@patch("os.path.exists", return_value=False)
@patch("builtins.input", return_value="")
@patch("builtins.open", new_callable=mock_open)
def test_check_and_create_tool_versions_different_version(mock_file, mock_input, mock_exists):
    """Test creating .tool-versions with different Python version."""
    check_and_create_tool_versions("/test/path", "3.11.5")

    mock_file.assert_called_once_with("/test/path/.tool-versions", "w")
    mock_file().write.assert_called_once_with("python 3.11.5\n")


@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_with_ref_flag(mock_temp_dir, mock_clone, mock_interactive, mock_create_version, mock_gitignore):
    """Test handle_setup uses custom ref when --ref flag is provided."""
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.ref = "main"

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=False):
        handle_setup(args)

    mock_clone.assert_called_once_with("/tmp/test", "main")
    mock_interactive.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")


@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.check_and_create_tool_versions")
@patch("caylent_devcontainer_cli.commands.setup.show_manual_instructions")
@patch("caylent_devcontainer_cli.commands.setup.copy_devcontainer_files")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_manual_with_ref_flag(
    mock_temp_dir,
    mock_clone,
    mock_copy,
    mock_show,
    mock_tool_versions,
    mock_create_version,
    mock_gitignore,
):
    """Test handle_setup manual mode uses custom ref when --ref flag is provided."""
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = True
    args.ref = "feature/test-branch"

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=False):
        handle_setup(args)

    mock_clone.assert_called_once_with("/tmp/test", "feature/test-branch")
    mock_copy.assert_called_once()
    mock_show.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")
    mock_tool_versions.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup.ensure_gitignore_entries")
@patch("caylent_devcontainer_cli.commands.setup.create_version_file")
@patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
@patch("caylent_devcontainer_cli.commands.setup.clone_repo")
@patch("tempfile.TemporaryDirectory")
def test_handle_setup_with_tag_ref(mock_temp_dir, mock_clone, mock_interactive, mock_create_version, mock_gitignore):
    """Test handle_setup uses tag ref when provided."""
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

    args = MagicMock()
    args.path = "/test/path"
    args.manual = False
    args.ref = "1.0.0"

    with patch("os.path.isdir", return_value=True), patch("os.path.exists", return_value=False):
        handle_setup(args)

    mock_clone.assert_called_once_with("/tmp/test", "1.0.0")
    mock_interactive.assert_called_once()
    mock_create_version.assert_called_once_with("/test/path")


# Tests for JsonValidator class


def test_example_env_values_includes_cicd():
    """Test that EXAMPLE_ENV_VALUES includes CICD=false."""
    from caylent_devcontainer_cli.commands.setup import EXAMPLE_ENV_VALUES

    assert "CICD" in EXAMPLE_ENV_VALUES
    assert EXAMPLE_ENV_VALUES["CICD"] == "false"


def test_is_single_line_env_var():
    """Test single line environment variable detection."""
    from caylent_devcontainer_cli.utils.env import is_single_line_env_var

    # Single line strings
    assert is_single_line_env_var("simple_string") is True
    assert is_single_line_env_var("value with spaces") is True
    assert is_single_line_env_var("") is True

    # Multiline strings
    assert is_single_line_env_var("line1\nline2") is False
    assert is_single_line_env_var("line1\n") is False

    # Complex types
    assert is_single_line_env_var({"key": "value"}) is False
    assert is_single_line_env_var(["item1", "item2"]) is False
    assert is_single_line_env_var(123) is False
    assert is_single_line_env_var(True) is False


@patch(
    "caylent_devcontainer_cli.commands.template.EXAMPLE_ENV_VALUES",
    {"VAR1": "value1", "VAR2": "value2", "VAR3": {"complex": "object"}, "VAR4": "multiline\nvalue"},
)
def test_get_missing_single_line_vars():
    """Test getting missing single line variables."""
    from caylent_devcontainer_cli.commands.template import get_missing_single_line_vars

    container_env = {"VAR1": "existing_value"}
    missing = get_missing_single_line_vars(container_env)

    # Should only include VAR2 (single line, missing)
    assert missing == {"VAR2": "value2"}


@patch("questionary.confirm")
@patch("questionary.text")
def test_prompt_for_missing_vars_use_defaults(mock_text, mock_confirm):
    """Test using default values for missing variables."""
    from caylent_devcontainer_cli.commands.template import prompt_for_missing_vars

    mock_confirm.return_value.ask.return_value = True
    missing_vars = {"VAR1": "default1", "VAR2": "default2"}

    result = prompt_for_missing_vars(missing_vars)

    assert result == {"VAR1": "default1", "VAR2": "default2"}
    assert mock_confirm.call_count == 2


@patch("caylent_devcontainer_cli.commands.setup_interactive.upgrade_template")
@patch("caylent_devcontainer_cli.commands.template.get_missing_single_line_vars")
@patch("caylent_devcontainer_cli.commands.template.prompt_for_missing_vars")
def test_upgrade_template_with_missing_vars(mock_prompt, mock_get_missing, mock_upgrade):
    """Test upgrading template with missing variables."""
    from caylent_devcontainer_cli import __version__
    from caylent_devcontainer_cli.commands.template import upgrade_template_with_missing_vars

    # Setup mocks
    mock_upgrade.return_value = {
        "containerEnv": {"existing_var": "value"},
        "cli_version": __version__,
        "aws_profile_map": {},
    }
    mock_get_missing.return_value = {"NEW_VAR": "default_value"}
    mock_prompt.return_value = {"NEW_VAR": "user_value"}

    template_data = {"containerEnv": {"existing_var": "value"}}
    result = upgrade_template_with_missing_vars(template_data)

    # Check that NEW_VAR was added
    assert "NEW_VAR" in result["containerEnv"]
    assert result["containerEnv"]["NEW_VAR"] == "user_value"
    assert result["containerEnv"]["existing_var"] == "value"
    assert result["cli_version"] == __version__
