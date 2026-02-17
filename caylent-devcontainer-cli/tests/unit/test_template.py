#!/usr/bin/env python3
import json
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands.template import (
    create_new_template,
    delete_template,
    handle_template_create,
    handle_template_delete,
    handle_template_list,
    handle_template_load,
    handle_template_save,
    handle_template_upgrade,
    handle_template_view,
    list_templates,
    load_template,
    save_template,
    upgrade_template_file,
    view_template,
)
from caylent_devcontainer_cli.utils.constants import TEMPLATES_DIR
from caylent_devcontainer_cli.utils.template import ensure_templates_dir


# Basic functionality tests
def test_ensure_templates_dir():
    with patch("caylent_devcontainer_cli.utils.template.os.makedirs") as mock_makedirs:
        ensure_templates_dir()
        mock_makedirs.assert_called_once_with(TEMPLATES_DIR, exist_ok=True)


def test_handle_template_save():
    with (
        patch("caylent_devcontainer_cli.commands.template.save_template") as mock_save,
        patch("caylent_devcontainer_cli.commands.template.resolve_project_root", return_value="/test/path"),
    ):
        args = MagicMock()
        args.project_root = "/test/path"
        args.name = "test-template"

        handle_template_save(args)

        mock_save.assert_called_once_with("/test/path", "test-template")


def test_handle_template_load():
    with (
        patch("caylent_devcontainer_cli.commands.template.load_template") as mock_load,
        patch("caylent_devcontainer_cli.commands.template.resolve_project_root", return_value="/test/path"),
    ):
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

    with (
        patch("builtins.open", mock_file),
        patch("os.path.exists", return_value=True),
        patch("json.load", return_value=mock_env_data),
        patch("json.dump") as mock_dump,
        patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=True),
        patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir"),
    ):

        save_template("/test/path", "test-template")

        # Verify json.dump was called with the env_data that includes cli_version
        mock_dump.assert_called_once()
        # First arg is the data dict, second arg is the file object
        saved_data = mock_dump.call_args[0][0]
        assert "cli_version" in saved_data


def test_load_template_no_existing_file():
    """Test load_template when no existing env file — no confirmation prompt."""
    mock_template_data = {"containerEnv": {"TEST": "val"}, "cli_version": "2.0.0"}

    with (
        patch("os.path.exists", side_effect=lambda p: "templates" in p),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_template_data))),
        patch("json.load", return_value=mock_template_data),
        patch("caylent_devcontainer_cli.commands.template.validate_template", side_effect=lambda d: d),
        patch("caylent_devcontainer_cli.commands.template.write_project_files") as mock_write_files,
    ):

        load_template("/test/path", "test-template")

        # Verify write_project_files was called with the template data
        mock_write_files.assert_called_once()
        call_args = mock_write_files.call_args
        assert call_args[0][0] == "/test/path"
        assert call_args[0][1] == mock_template_data


def test_load_template_overwrite_accepted():
    """Test load_template when existing env file and user accepts overwrite."""
    mock_template_data = {"containerEnv": {"TEST": "val"}, "cli_version": "2.0.0"}
    mock_confirm = MagicMock()
    mock_confirm.ask.return_value = True

    with (
        patch("os.path.exists", return_value=True),
        patch("questionary.confirm", return_value=mock_confirm),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_template_data))),
        patch("json.load", return_value=mock_template_data),
        patch("caylent_devcontainer_cli.commands.template.validate_template", side_effect=lambda d: d),
        patch("caylent_devcontainer_cli.commands.template.write_project_files") as mock_write_files,
    ):

        load_template("/test/path", "test-template")

        mock_write_files.assert_called_once()


def test_load_template_overwrite_declined():
    """Test load_template when existing env file and user declines overwrite."""
    mock_confirm = MagicMock()
    mock_confirm.ask.return_value = False

    with (
        patch("os.path.exists", return_value=True),
        patch("questionary.confirm", return_value=mock_confirm),
    ):
        with pytest.raises(SystemExit):
            load_template("/test/path", "test-template")


def test_load_template_calls_validate_template():
    """Test that load_template calls validate_template before write_project_files."""
    mock_template_data = {"containerEnv": {"K": "v"}, "cli_version": "2.0.0"}
    validated_data = {"containerEnv": {"K": "v", "ADDED": "by_validate"}, "cli_version": "2.0.0"}

    with (
        patch("os.path.exists", side_effect=lambda p: "templates" in p),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_template_data))),
        patch("json.load", return_value=mock_template_data),
        patch("caylent_devcontainer_cli.commands.template.validate_template", return_value=validated_data),
        patch("caylent_devcontainer_cli.commands.template.write_project_files") as mock_write_files,
    ):

        load_template("/test/path", "test-template")

        # write_project_files should receive the validated data, not the original
        mock_write_files.assert_called_once()
        assert mock_write_files.call_args[0][1] == validated_data


def test_load_template_passes_name_and_path_to_write():
    """Test that load_template passes template_name and template_path to write_project_files."""
    mock_template_data = {"containerEnv": {"K": "v"}, "cli_version": "2.0.0"}

    with (
        patch("os.path.exists", side_effect=lambda p: "templates" in p),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_template_data))),
        patch("json.load", return_value=mock_template_data),
        patch("caylent_devcontainer_cli.commands.template.validate_template", side_effect=lambda d: d),
        patch("caylent_devcontainer_cli.commands.template.write_project_files") as mock_write_files,
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/home/.devcontainer-templates"),
    ):

        load_template("/test/path", "my-template")

        call_args = mock_write_files.call_args[0]
        assert call_args[2] == "my-template"
        assert call_args[3] == "/home/.devcontainer-templates/my-template.json"


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


# Tests for template delete and upgrade
def test_handle_template_delete():
    """Test handling template delete command."""
    args = MagicMock()
    args.names = ["template1", "template2"]

    with patch("caylent_devcontainer_cli.commands.template.delete_template") as mock_delete:
        handle_template_delete(args)
        assert mock_delete.call_count == 2
        mock_delete.assert_any_call("template1")
        mock_delete.assert_any_call("template2")


def test_handle_template_create():
    """Test handling template create command."""
    args = MagicMock()
    args.name = "new-template"

    with patch("caylent_devcontainer_cli.commands.template.create_new_template") as mock_create:
        handle_template_create(args)
        mock_create.assert_called_once_with("new-template")


@patch("caylent_devcontainer_cli.commands.setup_interactive.save_template_to_file")
@patch("caylent_devcontainer_cli.commands.setup_interactive.create_template_interactive")
@patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir")
@patch("os.path.exists", return_value=False)
def test_create_new_template(mock_exists, mock_ensure_dir, mock_create_interactive, mock_save):
    """Test creating a new template."""
    mock_create_interactive.return_value = {"containerEnv": {"TEST": "value"}, "cli_version": "1.0.0"}

    create_new_template("test-template")

    mock_ensure_dir.assert_called_once()
    mock_create_interactive.assert_called_once()
    mock_save.assert_called_once_with({"containerEnv": {"TEST": "value"}, "cli_version": "1.0.0"}, "test-template")


@patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir")
@patch("os.path.exists", return_value=True)
def test_create_new_template_exists_cancel(mock_exists, mock_ensure_dir):
    """Test creating template when it exists and user cancels."""
    mock_confirm = MagicMock()
    mock_confirm.ask.return_value = False

    with patch("questionary.confirm", return_value=mock_confirm):
        with pytest.raises(SystemExit):
            create_new_template("existing-template")

    mock_ensure_dir.assert_called_once()


def test_handle_template_upgrade():
    """Test handling template upgrade command."""
    args = MagicMock()
    args.name = "template1"

    with patch("caylent_devcontainer_cli.commands.template.upgrade_template_file") as mock_upgrade:
        handle_template_upgrade(args)
        mock_upgrade.assert_called_once_with("template1")


def test_delete_template():
    """Test deleting a template."""
    template_name = "template1"

    with (
        patch("os.path.exists", return_value=True),
        patch("os.remove") as mock_remove,
        patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=True),
        patch("caylent_devcontainer_cli.utils.ui.log"),
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"),
    ):
        delete_template(template_name)

        # Check that os.remove was called
        mock_remove.assert_called_once_with("/templates/template1.json")


def test_delete_template_not_found():
    """Test deleting a template that doesn't exist."""
    template_name = "template1"

    with (
        patch("os.path.exists", return_value=False),
        patch("os.remove") as mock_remove,
        patch("caylent_devcontainer_cli.utils.ui.log"),
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"),
    ):
        delete_template(template_name)

        # Check that os.remove was not called
        mock_remove.assert_not_called()


def test_delete_template_cancel():
    """Test canceling template deletion."""
    template_name = "template1"

    with (
        patch("os.path.exists", return_value=True),
        patch("os.remove") as mock_remove,
        patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=False),
        patch("caylent_devcontainer_cli.utils.ui.log"),
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"),
    ):
        delete_template(template_name)

        # Check that os.remove was not called
        mock_remove.assert_not_called()


def test_upgrade_template_file_not_found():
    """Test upgrading a template file that doesn't exist."""
    with (
        patch("os.path.exists", return_value=False),
        patch("sys.exit", side_effect=SystemExit(1)),
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"),
    ):
        with pytest.raises(SystemExit):
            upgrade_template_file("template1")


def test_upgrade_already_current_version(capsys):
    """Test upgrade when template is already at current CLI version."""
    mock_data = {"containerEnv": {"K": "v"}, "cli_version": __version__}

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_data))),
        patch("json.load", return_value=mock_data),
        patch("caylent_devcontainer_cli.commands.template.write_json_file") as mock_write,
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"),
    ):
        upgrade_template_file("test-template")

        # Should NOT write the file — no changes needed
        mock_write.assert_not_called()

    captured = capsys.readouterr()
    assert "already at CLI" in captured.err
    assert "No changes needed" in captured.err


def test_upgrade_calls_validate_template():
    """Test that upgrade_template_file calls validate_template."""
    mock_data = {"containerEnv": {"K": "v"}, "cli_version": "2.0.0-alpha.1"}
    validated = {"containerEnv": {"K": "v", "ADDED": "by_validate"}, "cli_version": "2.0.0-alpha.1"}

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_data))),
        patch("json.load", return_value=mock_data),
        patch(
            "caylent_devcontainer_cli.commands.template.validate_template",
            return_value=validated,
        ) as mock_validate,
        patch("caylent_devcontainer_cli.commands.template.write_json_file"),
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"),
    ):
        upgrade_template_file("test-template")

        mock_validate.assert_called_once_with(mock_data)


def test_upgrade_updates_cli_version():
    """Test that upgrade updates cli_version to current version."""
    mock_data = {"containerEnv": {"K": "v"}, "cli_version": "2.0.0-alpha.1"}

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_data))),
        patch("json.load", return_value=mock_data),
        patch("caylent_devcontainer_cli.commands.template.validate_template", side_effect=lambda d: d),
        patch("caylent_devcontainer_cli.commands.template.write_json_file") as mock_write,
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"),
    ):
        upgrade_template_file("test-template")

        # Check cli_version was updated in the written data
        written_data = mock_write.call_args[0][1]
        assert written_data["cli_version"] == __version__


def test_upgrade_saves_template_file():
    """Test that upgrade saves to the correct template path."""
    mock_data = {"containerEnv": {"K": "v"}, "cli_version": "2.0.0-alpha.1"}

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_data))),
        patch("json.load", return_value=mock_data),
        patch("caylent_devcontainer_cli.commands.template.validate_template", side_effect=lambda d: d),
        patch("caylent_devcontainer_cli.commands.template.write_json_file") as mock_write,
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"),
    ):
        upgrade_template_file("test-template")

        mock_write.assert_called_once()
        assert mock_write.call_args[0][0] == "/templates/test-template.json"


def test_upgrade_success_message(capsys):
    """Test that upgrade outputs the correct success message."""
    mock_data = {"containerEnv": {"K": "v"}, "cli_version": "2.0.0-alpha.1"}

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_data))),
        patch("json.load", return_value=mock_data),
        patch("caylent_devcontainer_cli.commands.template.validate_template", side_effect=lambda d: d),
        patch("caylent_devcontainer_cli.commands.template.write_json_file"),
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"),
    ):
        upgrade_template_file("test-template")

    captured = capsys.readouterr()
    assert "test-template" in captured.err
    assert f"CLI v{__version__}" in captured.err
    assert "cdevcontainer code" in captured.err


def test_upgrade_v1x_rejected_by_validate():
    """Test that v1.x templates are rejected via validate_template()."""
    mock_data = {"containerEnv": {"K": "v"}, "cli_version": "1.0.0"}

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_data))),
        patch("json.load", return_value=mock_data),
        patch(
            "caylent_devcontainer_cli.commands.template.validate_template",
            side_effect=SystemExit(1),
        ),
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"),
    ):
        with pytest.raises(SystemExit):
            upgrade_template_file("test-template")


# Additional coverage tests
def test_handle_template_save_no_project_root():
    """Test handle_template_save function with no project_root."""
    args = MagicMock()
    args.project_root = None
    args.name = "test-template"

    with (
        patch("caylent_devcontainer_cli.commands.template.save_template") as mock_save,
        patch("caylent_devcontainer_cli.commands.template.resolve_project_root", return_value="/current/dir"),
    ):
        handle_template_save(args)
        mock_save.assert_called_once_with("/current/dir", "test-template")


def test_handle_template_load_no_project_root():
    """Test handle_template_load function with no project_root."""
    args = MagicMock()
    args.project_root = None
    args.name = "test-template"

    with (
        patch("caylent_devcontainer_cli.commands.template.load_template") as mock_load,
        patch("caylent_devcontainer_cli.commands.template.resolve_project_root", return_value="/current/dir"),
    ):
        handle_template_load(args)
        mock_load.assert_called_once_with("/current/dir", "test-template")


def test_ensure_templates_dir_creates_dir():
    """Test ensure_templates_dir creates directory if it doesn't exist."""
    with (
        patch("caylent_devcontainer_cli.utils.template.os.makedirs") as mock_makedirs,
        patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/test/templates"),
    ):
        ensure_templates_dir()
        mock_makedirs.assert_called_once_with("/test/templates", exist_ok=True)


def test_list_templates_with_no_templates():
    """Test list_templates when no templates are found."""
    with (
        patch("os.path.exists", return_value=True),
        patch("os.listdir", return_value=[]),
        patch("caylent_devcontainer_cli.commands.template.COLORS", {"YELLOW": "", "RESET": ""}),
        patch("builtins.print") as mock_print,
    ):
        list_templates()
        mock_print.assert_called_once_with("No templates found. Create one with 'template save <n>'")


def test_list_templates_with_templates():
    """Test list_templates with templates."""
    with (
        patch("os.path.exists", return_value=True),
        patch("os.listdir", return_value=["template1.json", "template2.json"]),
        patch("builtins.open", mock_open()),
        patch("json.load", side_effect=[{"cli_version": "1.0.0"}, {}]),
        patch("caylent_devcontainer_cli.commands.template.COLORS", {"CYAN": "", "GREEN": "", "RESET": ""}),
        patch("builtins.print") as mock_print,
    ):
        list_templates()
        mock_print.assert_any_call("Available templates:")
        mock_print.assert_any_call("  - template1 (created with CLI version 1.0.0)")
        mock_print.assert_any_call("  - template2 (created with CLI version unknown)")


# Tests for error handling
def test_save_template_error():
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", side_effect=Exception("Test error")),
        patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=True),
        patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir"),
        patch("sys.exit", side_effect=SystemExit(1)),
    ):
        with pytest.raises(SystemExit):
            save_template("/test/path", "test-template")


def test_load_template_not_found():
    """Test load_template when template is not found."""
    with (
        patch("os.path.exists", return_value=False),
        patch("caylent_devcontainer_cli.utils.ui.log"),
        patch("sys.exit", side_effect=SystemExit(1)),
    ):
        with pytest.raises(SystemExit):
            load_template("/test/path", "test-template")


def test_load_template_error():
    """Test load_template when file read raises an error."""
    mock_confirm = MagicMock()
    mock_confirm.ask.return_value = True

    with (
        patch("os.path.exists", return_value=True),
        patch("questionary.confirm", return_value=mock_confirm),
        patch("builtins.open", side_effect=Exception("Test error")),
        patch("sys.exit", side_effect=SystemExit(1)),
    ):
        with pytest.raises(SystemExit):
            load_template("/test/path", "test-template")


# Version-related tests
def test_save_template_adds_version():
    """Test that save_template adds the CLI version to the template data."""
    mock_env_data = {"key": "value"}

    with (
        patch("builtins.open", mock_open(read_data=json.dumps(mock_env_data))),
        patch("os.path.exists", return_value=True),
        patch("json.load", return_value=mock_env_data),
        patch("json.dump") as mock_dump,
        patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=True),
    ):

        save_template("/test/path", "test-template")

        # Verify json.dump was called with the env_data that includes cli_version
        mock_dump.assert_called_once()
        # First arg is the data dict, second arg is the file object
        saved_data = mock_dump.call_args[0][0]
        assert "cli_version" in saved_data
        assert saved_data["cli_version"] == __version__


def test_load_template_v1x_rejected_by_validate():
    """Test that v1.x templates are rejected via validate_template()."""
    mock_template_data = {"containerEnv": {"K": "v"}, "cli_version": "1.0.0"}

    with (
        patch("os.path.exists", side_effect=lambda p: "templates" in p),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_template_data))),
        patch("json.load", return_value=mock_template_data),
        patch(
            "caylent_devcontainer_cli.commands.template.validate_template",
            side_effect=SystemExit(1),
        ),
    ):
        with pytest.raises(SystemExit):
            load_template("/test/path", "test-template")


# Additional tests for missing coverage


def test_save_template_no_env_file():
    """Test save_template when environment file doesn't exist."""
    with (
        patch("os.path.exists", return_value=False),
        patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir"),
        patch("sys.exit", side_effect=SystemExit(1)),
    ):

        with pytest.raises(SystemExit):
            save_template("/test/path", "test-template")


def test_save_template_confirm_cancel():
    """Test save_template when user cancels confirmation."""
    with (
        patch("os.path.exists", side_effect=[True, False]),
        patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=False),
        patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir"),
        patch("sys.exit", side_effect=SystemExit(1)),
    ):

        with pytest.raises(SystemExit):
            save_template("/test/path", "test-template")


def test_load_template_success_message(capsys):
    """Test that load_template outputs success message."""
    mock_template_data = {"containerEnv": {"K": "v"}, "cli_version": "2.0.0"}

    with (
        patch("os.path.exists", side_effect=lambda p: "templates" in p),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_template_data))),
        patch("json.load", return_value=mock_template_data),
        patch("caylent_devcontainer_cli.commands.template.validate_template", side_effect=lambda d: d),
        patch("caylent_devcontainer_cli.commands.template.write_project_files"),
    ):

        load_template("/test/path", "test-template")

    captured = capsys.readouterr()
    assert "loaded successfully" in captured.err


def test_delete_template_exception():
    """Test delete_template with exception during deletion."""
    with (
        patch("os.path.exists", return_value=True),
        patch("os.remove", side_effect=Exception("Delete error")),
        patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=True),
    ):

        delete_template("test-template")


def test_list_templates_json_exception():
    """Test list_templates with JSON exception."""
    with (
        patch("os.listdir", return_value=["template1.json"]),
        patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir"),
        patch("builtins.open", side_effect=Exception("JSON error")),
        patch("builtins.print"),
    ):

        list_templates()  # Should handle exception gracefully


def test_create_new_template_overwrite():
    """Test create_new_template with overwrite confirmation."""
    template_data = {"containerEnv": {"TEST": "value"}, "cli_version": "1.0.0"}
    mock_confirm = MagicMock()
    mock_confirm.ask.return_value = True

    with (
        patch("os.path.exists", return_value=True),
        patch("questionary.confirm", return_value=mock_confirm),
        patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir"),
        patch(
            "caylent_devcontainer_cli.commands.setup_interactive.create_template_interactive",
            return_value=template_data,
        ),
        patch("caylent_devcontainer_cli.commands.setup_interactive.save_template_to_file"),
    ):

        create_new_template("existing-template")


def test_load_template_create_new_env_file():
    """Test load_template when creating new env file — no overwrite prompt."""
    template_data = {"containerEnv": {"K": "v"}, "cli_version": "2.0.0"}

    with (
        patch("os.path.exists", side_effect=lambda p: "templates" in p),
        patch("builtins.open", mock_open(read_data=json.dumps(template_data))),
        patch("json.load", return_value=template_data),
        patch("caylent_devcontainer_cli.commands.template.validate_template", side_effect=lambda d: d),
        patch("caylent_devcontainer_cli.commands.template.write_project_files") as mock_write,
    ):

        load_template("/test/path", "test-template")

        mock_write.assert_called_once()


def test_save_template_create_new_template():
    """Test save_template when creating new template."""
    mock_env_data = {"key": "value"}

    with (
        patch("os.path.exists", side_effect=[True, False]),
        patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=True),
        patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir"),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_env_data))),
        patch("json.load", return_value=mock_env_data),
        patch("json.dump"),
    ):

        save_template("/test/path", "test-template")


def test_register_command():
    """Test register_command function."""
    from caylent_devcontainer_cli.commands.template import register_command

    mock_subparsers = MagicMock()
    mock_parser = MagicMock()
    mock_template_subparsers = MagicMock()

    mock_subparsers.add_parser.return_value = mock_parser
    mock_parser.add_subparsers.return_value = mock_template_subparsers

    register_command(mock_subparsers)

    # Verify the main template parser was created
    mock_subparsers.add_parser.assert_called_once()
    call_args = mock_subparsers.add_parser.call_args
    assert call_args[0][0] == "template"
    assert call_args[1]["help"] == "Template management"
    # Verify subcommands were added
    assert mock_template_subparsers.add_parser.call_count >= 5


def test_load_template_no_confirm_action_used():
    """Test that load_template does not use confirm_action (uses questionary.confirm instead)."""
    import inspect

    from caylent_devcontainer_cli.commands import template

    source = inspect.getsource(template.load_template)
    assert "confirm_action" not in source


def test_load_template_no_raw_input():
    """Test that load_template does not use raw input()."""
    import inspect

    from caylent_devcontainer_cli.commands import template

    source = inspect.getsource(template.load_template)
    assert "input(" not in source


def test_upgrade_no_force_flag():
    """Test that register_command does not add --force flag to upgrade parser."""
    import inspect

    from caylent_devcontainer_cli.commands import template

    source = inspect.getsource(template.register_command)
    # The upgrade parser should not have --force
    assert "--force" not in source


def test_upgrade_no_try_except():
    """Test that upgrade_template_file does not use try/except."""
    import inspect

    from caylent_devcontainer_cli.commands import template

    source = inspect.getsource(template.upgrade_template_file)
    assert "try:" not in source
    assert "except" not in source


def test_upgrade_uses_validate_template():
    """Test that upgrade_template_file calls validate_template in its source."""
    import inspect

    from caylent_devcontainer_cli.commands import template

    source = inspect.getsource(template.upgrade_template_file)
    assert "validate_template" in source


def test_upgrade_no_semver_in_function():
    """Test that upgrade_template_file does not use semver comparison."""
    import inspect

    from caylent_devcontainer_cli.commands import template

    source = inspect.getsource(template.upgrade_template_file)
    assert "semver" not in source


def test_upgrade_no_upgrade_template_import():
    """Test that upgrade_template_file does not call upgrade_template from setup_interactive."""
    import inspect

    from caylent_devcontainer_cli.commands import template

    source = inspect.getsource(template.upgrade_template_file)
    assert "upgrade_template(" not in source.replace("upgrade_template_file", "")


# ---------------------------------------------------------------------------
# view_template tests
# ---------------------------------------------------------------------------


def test_handle_template_view_calls_view_template():
    """handle_template_view delegates to view_template."""
    args = MagicMock()
    args.name = "my-tmpl"
    with patch("caylent_devcontainer_cli.commands.template.view_template") as mock_view:
        handle_template_view(args)
        mock_view.assert_called_once_with("my-tmpl")


def test_view_template_prints_known_and_custom(capsys):
    """view_template prints known and custom variables."""
    template_data = {
        "containerEnv": {
            "DEVELOPER_NAME": "Alice",
            "GIT_USER": "alice",
            "MY_CUSTOM": "custom-val",
        },
        "cli_version": "2.0.0",
    }
    with (
        patch("os.path.exists", return_value=True),
        patch(
            "caylent_devcontainer_cli.commands.template.load_json_config",
            return_value=template_data,
        ),
    ):
        view_template("test-tmpl")

    output = capsys.readouterr().out
    assert "test-tmpl" in output
    assert "Path:" in output
    assert "2.0.0" in output
    assert "DEVELOPER_NAME" in output
    assert "Alice" in output
    assert "GIT_USER" in output
    assert "MY_CUSTOM" in output
    assert "custom-val" in output


def test_view_template_exits_if_not_found():
    """view_template exits with error for missing template."""
    with (
        patch("os.path.exists", return_value=False),
        pytest.raises(SystemExit),
    ):
        view_template("nonexistent")


def test_view_template_separates_known_and_custom(capsys):
    """view_template shows separate sections for known vs custom keys."""
    template_data = {
        "containerEnv": {
            "DEVELOPER_NAME": "Bob",
            "EXTRA_THING": "extra",
        },
        "cli_version": "2.0.0",
    }
    with (
        patch("os.path.exists", return_value=True),
        patch(
            "caylent_devcontainer_cli.commands.template.load_json_config",
            return_value=template_data,
        ),
    ):
        view_template("split-test")

    output = capsys.readouterr().out
    assert "Environment Variables:" in output
    assert "Custom Variables:" in output
    assert "DEVELOPER_NAME" in output
    assert "EXTRA_THING" in output


def test_view_template_empty_containerenv(capsys):
    """view_template handles empty containerEnv gracefully."""
    template_data = {
        "containerEnv": {},
        "cli_version": "2.0.0",
    }
    with (
        patch("os.path.exists", return_value=True),
        patch(
            "caylent_devcontainer_cli.commands.template.load_json_config",
            return_value=template_data,
        ),
    ):
        view_template("empty-tmpl")

    output = capsys.readouterr().out
    assert "empty-tmpl" in output
    assert "No environment variables defined" in output


def test_view_template_shows_aws_profiles(capsys):
    """view_template displays AWS profiles when present."""
    template_data = {
        "containerEnv": {
            "AWS_CONFIG_ENABLED": "true",
            "DEVELOPER_NAME": "Alice",
        },
        "aws_profile_map": {
            "default": {
                "region": "us-west-2",
                "sso_start_url": "https://example.awsapps.com/start",
                "sso_region": "us-west-2",
                "account_name": "example-dev-account",
                "account_id": "123456789012",
                "role_name": "DeveloperAccess",
            }
        },
        "cli_version": "2.0.0",
    }
    with (
        patch("os.path.exists", return_value=True),
        patch(
            "caylent_devcontainer_cli.commands.template.load_json_config",
            return_value=template_data,
        ),
    ):
        view_template("aws-tmpl")

    output = capsys.readouterr().out
    assert "AWS Profiles:" in output
    assert "default" in output
    assert "us-west-2" in output
    assert "https://example.awsapps.com/start" in output
    assert "example-dev-account" in output
    assert "123456789012" in output
    assert "DeveloperAccess" in output


def test_view_template_shows_aws_profiles_when_disabled(capsys):
    """view_template displays AWS profiles even when AWS_CONFIG_ENABLED is false."""
    template_data = {
        "containerEnv": {
            "AWS_CONFIG_ENABLED": "false",
            "DEVELOPER_NAME": "Bob",
        },
        "aws_profile_map": {
            "staging": {
                "region": "eu-west-1",
                "account_name": "staging-account",
                "account_id": "999888777666",
                "role_name": "ReadOnly",
            }
        },
        "cli_version": "2.0.0",
    }
    with (
        patch("os.path.exists", return_value=True),
        patch(
            "caylent_devcontainer_cli.commands.template.load_json_config",
            return_value=template_data,
        ),
    ):
        view_template("disabled-aws")

    output = capsys.readouterr().out
    assert "AWS Profiles:" in output
    assert "staging" in output
    assert "eu-west-1" in output
    assert "staging-account" in output


def test_view_template_shows_multiple_aws_profiles(capsys):
    """view_template displays multiple AWS profiles sorted by name."""
    template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true"},
        "aws_profile_map": {
            "production": {
                "region": "us-east-1",
                "account_name": "prod-account",
            },
            "default": {
                "region": "us-west-2",
                "account_name": "dev-account",
            },
        },
        "cli_version": "2.0.0",
    }
    with (
        patch("os.path.exists", return_value=True),
        patch(
            "caylent_devcontainer_cli.commands.template.load_json_config",
            return_value=template_data,
        ),
    ):
        view_template("multi-profile")

    output = capsys.readouterr().out
    assert "AWS Profiles:" in output
    # Both profiles present
    assert "default" in output
    assert "production" in output
    # default should appear before production (sorted)
    assert output.index("default") < output.index("production")


def test_view_template_no_aws_profiles(capsys):
    """view_template does not show AWS Profiles section when aws_profile_map is absent."""
    template_data = {
        "containerEnv": {"DEVELOPER_NAME": "Alice"},
        "cli_version": "2.0.0",
    }
    with (
        patch("os.path.exists", return_value=True),
        patch(
            "caylent_devcontainer_cli.commands.template.load_json_config",
            return_value=template_data,
        ),
    ):
        view_template("no-aws")

    output = capsys.readouterr().out
    assert "AWS Profiles:" not in output


def test_view_template_empty_aws_profiles(capsys):
    """view_template does not show AWS Profiles section when aws_profile_map is empty."""
    template_data = {
        "containerEnv": {"DEVELOPER_NAME": "Alice"},
        "aws_profile_map": {},
        "cli_version": "2.0.0",
    }
    with (
        patch("os.path.exists", return_value=True),
        patch(
            "caylent_devcontainer_cli.commands.template.load_json_config",
            return_value=template_data,
        ),
    ):
        view_template("empty-aws")

    output = capsys.readouterr().out
    assert "AWS Profiles:" not in output
