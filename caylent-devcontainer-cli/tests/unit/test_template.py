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
    list_templates,
    load_template,
    save_template,
    upgrade_template_file,
)
from caylent_devcontainer_cli.utils.constants import TEMPLATES_DIR
from caylent_devcontainer_cli.utils.template import ensure_templates_dir


# Basic functionality tests
def test_ensure_templates_dir():
    with patch("caylent_devcontainer_cli.utils.template.os.makedirs") as mock_makedirs:
        ensure_templates_dir()
        mock_makedirs.assert_called_once_with(TEMPLATES_DIR, exist_ok=True)


def test_handle_template_save():
    with patch("caylent_devcontainer_cli.commands.template.save_template") as mock_save, patch(
        "caylent_devcontainer_cli.commands.template.resolve_project_root", return_value="/test/path"
    ):
        args = MagicMock()
        args.project_root = "/test/path"
        args.name = "test-template"

        handle_template_save(args)

        mock_save.assert_called_once_with("/test/path", "test-template")


def test_handle_template_load():
    with patch("caylent_devcontainer_cli.commands.template.load_template") as mock_load, patch(
        "caylent_devcontainer_cli.commands.template.resolve_project_root", return_value="/test/path"
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


@patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=False)
@patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir")
@patch("os.path.exists", return_value=True)
def test_create_new_template_exists_cancel(mock_exists, mock_ensure_dir, mock_confirm):
    """Test creating template when it exists and user cancels."""
    create_new_template("existing-template")

    mock_confirm.assert_called_once_with("Template 'existing-template' already exists. Overwrite?")
    mock_ensure_dir.assert_called_once()


def test_handle_template_upgrade():
    """Test handling template upgrade command."""
    args = MagicMock()
    args.name = "template1"
    args.force = False

    with patch("caylent_devcontainer_cli.commands.template.upgrade_template_file") as mock_upgrade:
        handle_template_upgrade(args)
        mock_upgrade.assert_called_once_with("template1", force=False)


def test_delete_template():
    """Test deleting a template."""
    template_name = "template1"

    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove, patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch("caylent_devcontainer_cli.utils.ui.log"), patch(
        "caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"
    ):
        delete_template(template_name)

        # Check that os.remove was called
        mock_remove.assert_called_once_with("/templates/template1.json")


def test_delete_template_not_found():
    """Test deleting a template that doesn't exist."""
    template_name = "template1"

    with patch("os.path.exists", return_value=False), patch("os.remove") as mock_remove, patch(
        "caylent_devcontainer_cli.utils.ui.log"
    ), patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"):
        delete_template(template_name)

        # Check that os.remove was not called
        mock_remove.assert_not_called()


def test_delete_template_cancel():
    """Test canceling template deletion."""
    template_name = "template1"

    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove, patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=False
    ), patch("caylent_devcontainer_cli.utils.ui.log"), patch(
        "caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"
    ):
        delete_template(template_name)

        # Check that os.remove was not called
        mock_remove.assert_not_called()


def test_upgrade_template_file():
    """Test upgrading a template file."""
    template_name = "template1"
    mock_template_data = {"containerEnv": {"AWS_CONFIG_ENABLED": "true"}, "cli_version": "1.0.0"}

    with patch("os.path.exists", return_value=True), patch("builtins.open"), patch(
        "json.load", return_value=mock_template_data
    ), patch("json.dump"), patch(
        "caylent_devcontainer_cli.commands.template.upgrade_template",
        return_value={"containerEnv": {"AWS_CONFIG_ENABLED": "true"}, "cli_version": "2.0.0"},
    ), patch(
        "caylent_devcontainer_cli.__version__", "2.0.0"
    ), patch(
        "caylent_devcontainer_cli.utils.ui.log"
    ), patch(
        "caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"
    ):
        upgrade_template_file(template_name)


def test_upgrade_template_file_not_found():
    """Test upgrading a template file that doesn't exist."""
    template_name = "template1"

    with patch("os.path.exists", return_value=False), patch("caylent_devcontainer_cli.utils.ui.log"), patch(
        "sys.exit", side_effect=SystemExit(1)
    ), patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/templates"):
        with pytest.raises(SystemExit):
            upgrade_template_file(template_name)


# Additional coverage tests
def test_handle_template_save_no_project_root():
    """Test handle_template_save function with no project_root."""
    args = MagicMock()
    args.project_root = None
    args.name = "test-template"

    with patch("caylent_devcontainer_cli.commands.template.save_template") as mock_save, patch(
        "caylent_devcontainer_cli.commands.template.resolve_project_root", return_value="/current/dir"
    ):
        handle_template_save(args)
        mock_save.assert_called_once_with("/current/dir", "test-template")


def test_handle_template_load_no_project_root():
    """Test handle_template_load function with no project_root."""
    args = MagicMock()
    args.project_root = None
    args.name = "test-template"

    with patch("caylent_devcontainer_cli.commands.template.load_template") as mock_load, patch(
        "caylent_devcontainer_cli.commands.template.resolve_project_root", return_value="/current/dir"
    ):
        handle_template_load(args)
        mock_load.assert_called_once_with("/current/dir", "test-template")


def test_ensure_templates_dir_creates_dir():
    """Test ensure_templates_dir creates directory if it doesn't exist."""
    with patch("caylent_devcontainer_cli.utils.template.os.makedirs") as mock_makedirs, patch(
        "caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", "/test/templates"
    ):
        ensure_templates_dir()
        mock_makedirs.assert_called_once_with("/test/templates", exist_ok=True)


def test_list_templates_with_no_templates():
    """Test list_templates when no templates are found."""
    with patch("os.path.exists", return_value=True), patch("os.listdir", return_value=[]), patch(
        "caylent_devcontainer_cli.utils.ui.COLORS", {"YELLOW": "", "RESET": ""}
    ), patch("builtins.print") as mock_print:
        list_templates()
        mock_print.assert_called_once_with("No templates found. Create one with 'template save <n>'")


def test_list_templates_with_templates():
    """Test list_templates with templates."""
    with patch("os.path.exists", return_value=True), patch(
        "os.listdir", return_value=["template1.json", "template2.json"]
    ), patch("builtins.open", mock_open()), patch("json.load", side_effect=[{"cli_version": "1.0.0"}, {}]), patch(
        "caylent_devcontainer_cli.utils.ui.COLORS", {"CYAN": "", "GREEN": "", "RESET": ""}
    ), patch(
        "builtins.print"
    ) as mock_print:
        list_templates()
        mock_print.assert_any_call("Available templates:")
        mock_print.assert_any_call("  - template1 (created with CLI version 1.0.0)")
        mock_print.assert_any_call("  - template2 (created with CLI version unknown)")


# Tests for error handling
def test_save_template_error():
    with patch("os.path.exists", return_value=True), patch("builtins.open", side_effect=Exception("Test error")), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir"), patch(
        "sys.exit", side_effect=SystemExit(1)
    ):
        with pytest.raises(SystemExit):
            save_template("/test/path", "test-template")


def test_load_template_not_found():
    """Test load_template when template is not found."""
    with patch("os.path.exists", return_value=False), patch("caylent_devcontainer_cli.utils.ui.log"), patch(
        "sys.exit", side_effect=SystemExit(1)
    ):
        with pytest.raises(SystemExit):
            load_template("/test/path", "test-template")


def test_load_template_cancel():
    """Test canceling template loading."""
    with patch("os.path.exists", return_value=True), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=False
    ), patch("sys.exit", side_effect=SystemExit(1)):
        with pytest.raises(SystemExit):
            load_template("/test/path", "test-template")


def test_load_template_error():
    with patch("os.path.exists", return_value=True), patch("builtins.open", side_effect=Exception("Test error")), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch("sys.exit", side_effect=SystemExit(1)):
        with pytest.raises(SystemExit):
            load_template("/test/path", "test-template")


# Version-related tests
def test_save_template_adds_version():
    """Test that save_template adds the CLI version to the template data."""
    mock_env_data = {"key": "value"}

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_env_data))), patch(
        "os.path.exists", return_value=True
    ), patch("json.load", return_value=mock_env_data), patch("json.dump") as mock_dump, patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ):

        save_template("/test/path", "test-template")

        # Verify json.dump was called with the env_data that includes cli_version
        mock_dump.assert_called_once()
        # First arg is the data dict, second arg is the file object
        saved_data = mock_dump.call_args[0][0]
        assert "cli_version" in saved_data
        assert saved_data["cli_version"] == __version__


def test_load_template_version_mismatch():
    """Test that load_template handles version mismatches correctly."""
    mock_template_data = {"key": "value", "cli_version": "1.0.0"}  # Old version

    # Mock current version to be 2.0.0
    with patch("caylent_devcontainer_cli.__version__", "2.0.0"), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_template_data))
    ), patch("os.path.exists", return_value=True), patch("builtins.input", return_value="4"), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "json.load", return_value=mock_template_data
    ), patch(
        "json.dump"
    ):
        load_template("/test/path", "test-template")


def test_load_template_upgrade_choice():
    """Test that load_template handles the upgrade choice correctly."""
    mock_template_data = {"key": "value", "cli_version": "1.0.0"}  # Old version
    upgraded_data = {"upgraded": True, "cli_version": "2.0.0"}

    # Mock current version to be 2.0.0
    with patch("caylent_devcontainer_cli.__version__", "2.0.0"), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_template_data))
    ), patch("os.path.exists", return_value=True), patch("builtins.input", return_value="1"), patch(
        "caylent_devcontainer_cli.commands.template.upgrade_template", return_value=upgraded_data
    ), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "json.load", return_value=mock_template_data
    ), patch(
        "json.dump"
    ):
        load_template("/test/path", "test-template")


def test_load_template_new_profile_choice():
    """Test that load_template handles the new profile choice correctly."""
    mock_template_data = {"key": "value", "cli_version": "1.0.0"}  # Old version

    # Mock current version to be 2.0.0
    with patch("caylent_devcontainer_cli.__version__", "2.0.0"), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_template_data))
    ), patch("os.path.exists", return_value=True), patch("builtins.input", return_value="2"), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "json.load", return_value=mock_template_data
    ), patch(
        "json.dump"
    ):
        load_template("/test/path", "test-template")


def test_load_template_use_anyway_choice():
    """Test that load_template handles the 'use anyway' choice correctly."""
    mock_template_data = {"key": "value", "cli_version": "1.0.0"}  # Old version

    # Mock current version to be 2.0.0
    with patch("caylent_devcontainer_cli.__version__", "2.0.0"), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_template_data))
    ), patch("os.path.exists", return_value=True), patch("builtins.input", return_value="3"), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "json.load", return_value=mock_template_data
    ), patch(
        "json.dump"
    ):
        load_template("/test/path", "test-template")


def test_load_template_invalid_choice():
    """Test that load_template handles invalid choices correctly."""
    mock_template_data = {"key": "value", "cli_version": "1.0.0"}  # Old version

    # Mock current version to be 2.0.0
    with patch("caylent_devcontainer_cli.__version__", "2.0.0"), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_template_data))
    ), patch("os.path.exists", return_value=True), patch("builtins.input", side_effect=["invalid", "4"]), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "json.load", return_value=mock_template_data
    ), patch(
        "json.dump"
    ):
        load_template("/test/path", "test-template")


def test_upgrade_template_file_version_check():
    """Test upgrade_template_file with version check."""
    template_data = {"cli_version": "1.0.0"}
    mock_upgraded_data = {"key": "value", "cli_version": __version__}

    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=json.dumps(template_data))
    ), patch("json.load", return_value=template_data), patch(
        "caylent_devcontainer_cli.commands.template.upgrade_template", return_value=mock_upgraded_data
    ), patch(
        "json.dump"
    ):
        upgrade_template_file("test-template")


# Additional tests for missing coverage


def test_get_missing_env_vars():
    """Test get_missing_env_vars function."""
    from caylent_devcontainer_cli.utils.env import get_missing_env_vars

    container_env = {"EXISTING_VAR": "value"}
    example_values = {"EXISTING_VAR": "existing", "MISSING_VAR": "default_value", "COMPLEX_VAR": {"nested": "object"}}

    with patch("caylent_devcontainer_cli.utils.env.EXAMPLE_ENV_VALUES", example_values):
        result = get_missing_env_vars(container_env)
        assert "MISSING_VAR" in result
        assert "EXISTING_VAR" not in result
        assert "COMPLEX_VAR" not in result


def test_prompt_for_missing_vars():
    """Test prompt_for_missing_vars function."""
    from caylent_devcontainer_cli.commands.template import prompt_for_missing_vars

    missing_vars = {"VAR1": "default1", "VAR2": "default2"}

    with patch("questionary.confirm") as mock_confirm, patch("questionary.text") as mock_text:
        mock_confirm_obj = MagicMock()
        mock_confirm_obj.ask.side_effect = [True, False]  # Use default for VAR1, custom for VAR2
        mock_confirm.return_value = mock_confirm_obj

        mock_text_obj = MagicMock()
        mock_text_obj.ask.return_value = "custom_value"
        mock_text.return_value = mock_text_obj

        result = prompt_for_missing_vars(missing_vars)

        assert result["VAR1"] == "default1"
        assert result["VAR2"] == "custom_value"


def test_upgrade_template_with_missing_vars():
    """Test upgrade_template_with_missing_vars function."""
    from caylent_devcontainer_cli.commands.template import upgrade_template_with_missing_vars

    template_data = {"containerEnv": {"EXISTING": "value"}}
    upgraded_template = {"containerEnv": {"EXISTING": "value", "UPGRADED": "true"}}
    missing_vars = {"NEW_VAR": "new_value"}

    with patch(
        "caylent_devcontainer_cli.commands.setup_interactive.upgrade_template", return_value=upgraded_template
    ), patch("caylent_devcontainer_cli.commands.template.get_missing_env_vars", return_value=missing_vars), patch(
        "caylent_devcontainer_cli.commands.template.prompt_for_missing_vars", return_value=missing_vars
    ):

        result = upgrade_template_with_missing_vars(template_data)

        assert "NEW_VAR" in result["containerEnv"]
        assert result["containerEnv"]["NEW_VAR"] == "new_value"


def test_upgrade_template_with_no_missing_vars():
    """Test upgrade_template_with_missing_vars with no missing vars."""
    from caylent_devcontainer_cli.commands.template import upgrade_template_with_missing_vars

    template_data = {"containerEnv": {"EXISTING": "value"}}
    upgraded_template = {"containerEnv": {"EXISTING": "value", "UPGRADED": "true"}}

    with patch(
        "caylent_devcontainer_cli.commands.setup_interactive.upgrade_template", return_value=upgraded_template
    ), patch("caylent_devcontainer_cli.commands.template.get_missing_env_vars", return_value={}):

        result = upgrade_template_with_missing_vars(template_data)

        assert result == upgraded_template


def test_upgrade_template_file_force():
    """Test upgrade_template_file with force flag."""
    template_data = {"containerEnv": {"TEST": "value"}, "cli_version": "1.0.0"}
    upgraded_data = {"containerEnv": {"TEST": "value", "NEW": "var"}, "cli_version": __version__}

    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=json.dumps(template_data))
    ), patch("json.load", return_value=template_data), patch("json.dump"), patch(
        "caylent_devcontainer_cli.commands.template.upgrade_template_with_missing_vars", return_value=upgraded_data
    ):

        upgrade_template_file("test-template", force=True)


def test_upgrade_template_file_same_version():
    """Test upgrade_template_file when versions match."""
    template_data = {"containerEnv": {"TEST": "value"}, "cli_version": __version__}

    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=json.dumps(template_data))
    ), patch("json.load", return_value=template_data), patch("json.dump") as mock_dump:

        upgrade_template_file("test-template")

        # Should still update the version even if major.minor match
        mock_dump.assert_called_once()


def test_upgrade_template_file_version_parse_error():
    """Test upgrade_template_file with version parse error."""
    template_data = {"containerEnv": {"TEST": "value"}, "cli_version": "invalid.version"}
    upgraded_data = {"containerEnv": {"TEST": "value"}, "cli_version": __version__}

    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=json.dumps(template_data))
    ), patch("json.load", return_value=template_data), patch("json.dump"), patch(
        "caylent_devcontainer_cli.commands.setup_interactive.upgrade_template", return_value=upgraded_data
    ):

        upgrade_template_file("test-template")


def test_upgrade_template_file_no_version():
    """Test upgrade_template_file with no version in template."""
    template_data = {"containerEnv": {"TEST": "value"}}
    upgraded_data = {"containerEnv": {"TEST": "value"}, "cli_version": __version__}

    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=json.dumps(template_data))
    ), patch("json.load", return_value=template_data), patch("json.dump"), patch(
        "caylent_devcontainer_cli.commands.setup_interactive.upgrade_template", return_value=upgraded_data
    ):

        upgrade_template_file("test-template")


def test_upgrade_template_file_exception():
    """Test upgrade_template_file with exception."""
    with patch("os.path.exists", return_value=True), patch("builtins.open", side_effect=Exception("File error")), patch(
        "sys.exit", side_effect=SystemExit(1)
    ):
        with pytest.raises(SystemExit):
            upgrade_template_file("test-template")


def test_save_template_no_env_file():
    """Test save_template when environment file doesn't exist."""
    with patch("os.path.exists", return_value=False), patch(
        "caylent_devcontainer_cli.commands.template.ensure_templates_dir"
    ), patch("sys.exit", side_effect=SystemExit(1)):

        with pytest.raises(SystemExit):
            save_template("/test/path", "test-template")


def test_save_template_confirm_cancel():
    """Test save_template when user cancels confirmation."""
    with patch("os.path.exists", side_effect=[True, False]), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=False
    ), patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir"), patch(
        "sys.exit", side_effect=SystemExit(1)
    ):

        with pytest.raises(SystemExit):
            save_template("/test/path", "test-template")


def test_load_template_version_parse_error():
    """Test load_template with version parse error."""
    template_data = {"key": "value", "cli_version": "invalid.version"}

    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=json.dumps(template_data))
    ), patch("json.load", return_value=template_data), patch("json.dump"), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ):

        load_template("/test/path", "test-template")


def test_load_template_use_anyway_cancel():
    """Test load_template when user cancels 'use anyway' confirmation."""
    template_data = {"key": "value", "cli_version": "1.0.0"}

    with patch("caylent_devcontainer_cli.commands.template.__version__", "2.0.0"), patch(
        "os.path.exists", return_value=True
    ), patch("builtins.input", return_value="3"), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", side_effect=[True, False]
    ), patch(
        "json.load", return_value=template_data
    ), patch(
        "sys.exit", side_effect=SystemExit(0)
    ):

        with pytest.raises(SystemExit):
            load_template("/test/path", "test-template")


def test_delete_template_exception():
    """Test delete_template with exception during deletion."""
    with patch("os.path.exists", return_value=True), patch("os.remove", side_effect=Exception("Delete error")), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ):

        delete_template("test-template")


def test_list_templates_json_exception():
    """Test list_templates with JSON exception."""
    with patch("os.listdir", return_value=["template1.json"]), patch(
        "caylent_devcontainer_cli.commands.template.ensure_templates_dir"
    ), patch("builtins.open", side_effect=Exception("JSON error")), patch("builtins.print"):

        list_templates()  # Should handle exception gracefully


def test_create_new_template_overwrite():
    """Test create_new_template with overwrite confirmation."""
    template_data = {"containerEnv": {"TEST": "value"}, "cli_version": "1.0.0"}

    with patch("os.path.exists", return_value=True), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir"), patch(
        "caylent_devcontainer_cli.commands.setup_interactive.create_template_interactive", return_value=template_data
    ), patch(
        "caylent_devcontainer_cli.commands.setup_interactive.save_template_to_file"
    ):

        create_new_template("existing-template")


def test_load_template_create_new_env_file():
    """Test load_template when creating new env file."""
    template_data = {"key": "value"}

    with patch("os.path.exists", side_effect=[True, False]), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch("builtins.open", mock_open(read_data=json.dumps(template_data))), patch(
        "json.load", return_value=template_data
    ), patch(
        "json.dump"
    ):

        load_template("/test/path", "test-template")


def test_save_template_create_new_template():
    """Test save_template when creating new template."""
    mock_env_data = {"key": "value"}

    with patch("os.path.exists", side_effect=[True, False]), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch("caylent_devcontainer_cli.commands.template.ensure_templates_dir"), patch(
        "builtins.open", mock_open(read_data=json.dumps(mock_env_data))
    ), patch(
        "json.load", return_value=mock_env_data
    ), patch(
        "json.dump"
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
    mock_subparsers.add_parser.assert_called_with("template", help="Template management")
    # Verify subcommands were added
    assert mock_template_subparsers.add_parser.call_count >= 5


def test_load_template_version_mismatch_choices():
    """Test load_template version mismatch with different choices."""
    template_data = {"key": "value", "cli_version": "1.0.0"}

    # Test choice 1 (upgrade)
    with patch("caylent_devcontainer_cli.commands.template.__version__", "2.0.0"), patch(
        "os.path.exists", return_value=True
    ), patch("builtins.input", return_value="1"), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "builtins.open", mock_open(read_data=json.dumps(template_data))
    ), patch(
        "json.load", return_value=template_data
    ), patch(
        "json.dump"
    ), patch(
        "caylent_devcontainer_cli.commands.template.upgrade_template", return_value=template_data
    ):

        load_template("/test/path", "test-template")


def test_load_template_version_mismatch_invalid_then_valid():
    """Test load_template version mismatch with invalid then valid choice."""
    template_data = {"key": "value", "cli_version": "1.0.0"}

    with patch("caylent_devcontainer_cli.commands.template.__version__", "2.0.0"), patch(
        "os.path.exists", return_value=True
    ), patch("builtins.input", side_effect=["invalid", "1"]), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "builtins.open", mock_open(read_data=json.dumps(template_data))
    ), patch(
        "json.load", return_value=template_data
    ), patch(
        "json.dump"
    ), patch(
        "caylent_devcontainer_cli.commands.template.upgrade_template", return_value=template_data
    ), patch(
        "builtins.print"
    ):

        load_template("/test/path", "test-template")


def test_load_template_version_mismatch_exit():
    """Test load_template version mismatch with exit choice."""
    template_data = {"key": "value", "cli_version": "1.0.0"}

    with patch("caylent_devcontainer_cli.commands.template.__version__", "2.0.0"), patch(
        "os.path.exists", return_value=True
    ), patch("builtins.input", return_value="4"), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "builtins.open", mock_open(read_data=json.dumps(template_data))
    ), patch(
        "json.load", return_value=template_data
    ), patch(
        "sys.exit", side_effect=SystemExit(0)
    ):

        with pytest.raises(SystemExit):
            load_template("/test/path", "test-template")


def test_load_template_version_mismatch_new_profile():
    """Test load_template version mismatch with new profile choice."""
    template_data = {"key": "value", "cli_version": "1.0.0"}

    with patch("caylent_devcontainer_cli.commands.template.__version__", "2.0.0"), patch(
        "os.path.exists", return_value=True
    ), patch("builtins.input", return_value="2"), patch(
        "caylent_devcontainer_cli.commands.template.confirm_action", return_value=True
    ), patch(
        "builtins.open", mock_open(read_data=json.dumps(template_data))
    ), patch(
        "json.load", return_value=template_data
    ), patch(
        "sys.exit", side_effect=SystemExit(0)
    ):

        with pytest.raises(SystemExit):
            load_template("/test/path", "test-template")
