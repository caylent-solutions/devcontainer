#!/usr/bin/env python3
import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands.setup import (
    _browse_entries,
    _display_and_confirm_entry,
    _display_entry_metadata,
    _ensure_tool_versions,
    _has_python_entry,
    _prompt_replace_decision,
    _prompt_source_selection,
    _run_informational_validation,
    _select_and_copy_catalog,
    _show_existing_config,
    _show_python_notice,
    _show_replace_notification,
    create_version_file,
    handle_setup,
    interactive_setup,
    register_command,
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
from caylent_devcontainer_cli.utils.catalog import CatalogEntry, EntryInfo

# ─── register_command ───────────────────────────────────────────────────────


class TestRegisterCommand:
    """Tests for register_command() — verifies arg parser configuration."""

    def test_registers_setup_devcontainer(self):
        mock_subparsers = MagicMock()
        mock_parser = MagicMock()
        mock_subparsers.add_parser.return_value = mock_parser

        register_command(mock_subparsers)

        mock_subparsers.add_parser.assert_called_once()
        call_args = mock_subparsers.add_parser.call_args
        assert call_args[0][0] == "setup-devcontainer"
        assert call_args[1]["help"] == "Set up a devcontainer in a project directory"
        mock_parser.set_defaults.assert_called_once_with(func=handle_setup)

    def test_no_manual_flag(self):
        """Verify --manual flag was removed."""
        mock_subparsers = MagicMock()
        mock_parser = MagicMock()
        mock_subparsers.add_parser.return_value = mock_parser

        register_command(mock_subparsers)

        for call in mock_parser.add_argument.call_args_list:
            args = call[0] if call[0] else []
            assert "--manual" not in args, "--manual flag should be removed"

    def test_no_ref_flag(self):
        """Verify --ref flag was removed."""
        mock_subparsers = MagicMock()
        mock_parser = MagicMock()
        mock_subparsers.add_parser.return_value = mock_parser

        register_command(mock_subparsers)

        for call in mock_parser.add_argument.call_args_list:
            args = call[0] if call[0] else []
            assert "--ref" not in args, "--ref flag should be removed"

    def test_registers_catalog_entry_flag(self):
        """Verify --catalog-entry flag is registered."""
        mock_subparsers = MagicMock()
        mock_parser = MagicMock()
        mock_subparsers.add_parser.return_value = mock_parser

        register_command(mock_subparsers)

        catalog_entry_found = False
        for call in mock_parser.add_argument.call_args_list:
            args = call[0] if call[0] else []
            if "--catalog-entry" in args:
                catalog_entry_found = True
                kwargs = call[1] if call[1] else {}
                assert kwargs.get("type") is str
                assert kwargs.get("default") is None
        assert catalog_entry_found, "--catalog-entry flag should be registered"


# ─── _ensure_tool_versions ──────────────────────────────────────────────────


class TestEnsureToolVersions:
    """Tests for _ensure_tool_versions()."""

    def test_creates_empty_file_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _ensure_tool_versions(tmpdir)
            tv_path = os.path.join(tmpdir, ".tool-versions")
            assert os.path.exists(tv_path)
            with open(tv_path, "r") as f:
                assert f.read() == ""

    def test_does_not_overwrite_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tv_path = os.path.join(tmpdir, ".tool-versions")
            with open(tv_path, "w") as f:
                f.write("python 3.12.9\n")

            _ensure_tool_versions(tmpdir)

            with open(tv_path, "r") as f:
                assert f.read() == "python 3.12.9\n"


# ─── _has_python_entry ──────────────────────────────────────────────────────


class TestHasPythonEntry:
    """Tests for _has_python_entry()."""

    def test_returns_true_for_python_line(self):
        assert _has_python_entry("python 3.12.9\n") is True

    def test_returns_true_for_python_with_other_entries(self):
        assert _has_python_entry("nodejs 18.0.0\npython 3.12.9\nruby 3.2.0\n") is True

    def test_returns_false_for_empty(self):
        assert _has_python_entry("") is False

    def test_returns_false_for_no_python(self):
        assert _has_python_entry("nodejs 18.0.0\nruby 3.2.0\n") is False

    def test_returns_false_for_comment_with_python(self):
        assert _has_python_entry("# python 3.12.9\n") is False


# ─── _show_existing_config ──────────────────────────────────────────────────


class TestShowExistingConfig:
    """Tests for _show_existing_config()."""

    def test_shows_version_from_file(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            devcontainer_dir = os.path.join(tmpdir, ".devcontainer")
            os.makedirs(devcontainer_dir)
            with open(os.path.join(devcontainer_dir, "VERSION"), "w") as f:
                f.write("1.14.0\n")

            _show_existing_config(tmpdir)

            captured = capsys.readouterr()
            assert "Current version: 1.14.0" in captured.err

    def test_shows_version_unknown_when_no_version_file(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            devcontainer_dir = os.path.join(tmpdir, ".devcontainer")
            os.makedirs(devcontainer_dir)

            _show_existing_config(tmpdir)

            captured = capsys.readouterr()
            assert "Current version: unknown" in captured.err

    def test_shows_catalog_entry_info(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            devcontainer_dir = os.path.join(tmpdir, ".devcontainer")
            os.makedirs(devcontainer_dir)
            catalog_data = {
                "name": "default",
                "catalog_url": "https://github.com/example/catalog.git",
            }
            with open(os.path.join(devcontainer_dir, "catalog-entry.json"), "w") as f:
                json.dump(catalog_data, f)

            _show_existing_config(tmpdir)

            captured = capsys.readouterr()
            assert "Catalog entry: default" in captured.err
            assert "Catalog URL: https://github.com/example/catalog.git" in captured.err

    def test_no_catalog_entry_no_error(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            devcontainer_dir = os.path.join(tmpdir, ".devcontainer")
            os.makedirs(devcontainer_dir)

            _show_existing_config(tmpdir)

            captured = capsys.readouterr()
            assert "Catalog entry" not in captured.err

    def test_displays_replace_notice(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            devcontainer_dir = os.path.join(tmpdir, ".devcontainer")
            os.makedirs(devcontainer_dir)

            _show_existing_config(tmpdir)

            captured = capsys.readouterr()
            assert "asked whether to replace" in captured.err


# ─── _show_python_notice ────────────────────────────────────────────────────


class TestShowPythonNotice:
    """Tests for _show_python_notice()."""

    def test_shows_notice_when_python_in_tool_versions(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tv_path = os.path.join(tmpdir, ".tool-versions")
            with open(tv_path, "w") as f:
                f.write("python 3.12.9\n")

            _show_python_notice(tmpdir)

            captured = capsys.readouterr()
            assert "Python entry" in captured.err
            assert "devcontainer.json" in captured.err

    def test_no_notice_when_no_python(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            tv_path = os.path.join(tmpdir, ".tool-versions")
            with open(tv_path, "w") as f:
                f.write("nodejs 18.0.0\n")

            _show_python_notice(tmpdir)

            captured = capsys.readouterr()
            assert "Python entry" not in captured.err

    def test_no_notice_when_no_tool_versions(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            _show_python_notice(tmpdir)

            captured = capsys.readouterr()
            assert "Python entry" not in captured.err


# ─── _prompt_replace_decision ───────────────────────────────────────────────


class TestPromptReplaceDecision:
    """Tests for _prompt_replace_decision()."""

    @patch("questionary.confirm")
    def test_returns_true_when_user_confirms(self, mock_confirm):
        mock_confirm.return_value.ask.return_value = True
        assert _prompt_replace_decision() is True

    @patch("questionary.confirm")
    def test_returns_false_when_user_declines(self, mock_confirm):
        mock_confirm.return_value.ask.return_value = False
        assert _prompt_replace_decision() is False


# ─── _show_replace_notification ─────────────────────────────────────────────


class TestShowReplaceNotification:
    """Tests for _show_replace_notification()."""

    @patch("questionary.confirm")
    def test_proceeds_when_acknowledged(self, mock_confirm, capsys):
        mock_confirm.return_value.ask.return_value = True
        _show_replace_notification()

        captured = capsys.readouterr()
        assert "Overwrite existing" in captured.out

    @patch("questionary.confirm")
    def test_exits_when_not_acknowledged(self, mock_confirm):
        mock_confirm.return_value.ask.return_value = False
        with pytest.raises(SystemExit):
            _show_replace_notification()


# ─── _run_informational_validation ──────────────────────────────────────────


class TestRunInformationalValidation:
    """Tests for _run_informational_validation()."""

    def test_skips_when_no_project_files(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            _run_informational_validation(tmpdir)

            captured = capsys.readouterr()
            assert "configuration issues" not in captured.err

    def test_skips_when_only_env_json_exists(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "devcontainer-environment-variables.json"), "w") as f:
                json.dump({"containerEnv": {}}, f)

            _run_informational_validation(tmpdir)

            captured = capsys.readouterr()
            assert "configuration issues" not in captured.err

    def test_displays_issues_when_both_files_exist(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create env json with missing keys
            env_data = {"containerEnv": {"DEVELOPER_NAME": "Test"}}
            with open(os.path.join(tmpdir, "devcontainer-environment-variables.json"), "w") as f:
                json.dump(env_data, f)
            with open(os.path.join(tmpdir, "shell.env"), "w") as f:
                f.write("export DEVELOPER_NAME='Test'\n")

            _run_informational_validation(tmpdir)

            captured = capsys.readouterr()
            assert "configuration issues were detected" in captured.err

    def test_silent_when_no_issues(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create complete env json with all keys
            from caylent_devcontainer_cli.commands.setup import EXAMPLE_ENV_VALUES

            env_data = {
                "containerEnv": dict(EXAMPLE_ENV_VALUES),
                "template_name": "test",
                "template_path": "/path/test.json",
                "cli_version": "2.0.0",
            }
            with open(os.path.join(tmpdir, "devcontainer-environment-variables.json"), "w") as f:
                json.dump(env_data, f)

            # Create shell.env with all exports
            lines = [f"export {k}='{v}'" for k, v in EXAMPLE_ENV_VALUES.items()]
            lines.append("# Template: test")
            lines.append("# Template Path: /path/test.json")
            lines.append("# CLI Version: 2.0.0")
            with open(os.path.join(tmpdir, "shell.env"), "w") as f:
                f.write("\n".join(lines) + "\n")

            # Need to create the template file too for Steps 2-3
            with patch(
                "caylent_devcontainer_cli.utils.validation._step2_locate_template",
                return_value=(False, None),
            ):
                _run_informational_validation(tmpdir)

            captured = capsys.readouterr()
            # May show "template not found" but should not show missing keys
            assert "Missing base keys" not in captured.err


# ─── handle_setup ───────────────────────────────────────────────────────────


class TestHandleSetup:
    """Tests for the rewritten handle_setup()."""

    def test_exits_on_invalid_path(self):
        args = MagicMock()
        args.path = "/nonexistent/path"

        with pytest.raises(SystemExit):
            handle_setup(args)

    @patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
    @patch("caylent_devcontainer_cli.commands.setup._run_informational_validation")
    @patch("caylent_devcontainer_cli.commands.setup._select_and_copy_catalog")
    def test_creates_tool_versions_and_runs_setup(self, mock_catalog, mock_validation, mock_interactive):
        with tempfile.TemporaryDirectory() as tmpdir:
            args = MagicMock()
            args.path = tmpdir
            args.catalog_entry = None
            args.catalog_url = None

            handle_setup(args)

            # .tool-versions should be created
            assert os.path.exists(os.path.join(tmpdir, ".tool-versions"))
            mock_catalog.assert_called_once_with(tmpdir, catalog_entry=None, catalog_url_override=None)
            mock_interactive.assert_called_once_with(tmpdir)

    @patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
    @patch("caylent_devcontainer_cli.commands.setup._run_informational_validation")
    @patch("caylent_devcontainer_cli.commands.setup._select_and_copy_catalog")
    @patch("caylent_devcontainer_cli.commands.setup._show_replace_notification")
    @patch(
        "caylent_devcontainer_cli.commands.setup._prompt_replace_decision",
        return_value=True,
    )
    @patch("caylent_devcontainer_cli.commands.setup._show_python_notice")
    @patch("caylent_devcontainer_cli.commands.setup._show_existing_config")
    def test_existing_config_replace_flow(
        self,
        mock_show_config,
        mock_python_notice,
        mock_replace_decision,
        mock_replace_notification,
        mock_catalog,
        mock_validation,
        mock_interactive,
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".devcontainer"))

            args = MagicMock()
            args.path = tmpdir
            args.catalog_entry = None
            args.catalog_url = None

            handle_setup(args)

            mock_show_config.assert_called_once_with(tmpdir)
            mock_python_notice.assert_called_once_with(tmpdir)
            mock_replace_decision.assert_called_once()
            mock_replace_notification.assert_called_once()
            mock_catalog.assert_called_once_with(tmpdir, catalog_entry=None, catalog_url_override=None)
            mock_interactive.assert_called_once_with(tmpdir)

    @patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
    @patch("caylent_devcontainer_cli.commands.setup._run_informational_validation")
    @patch("caylent_devcontainer_cli.commands.setup._select_and_copy_catalog")
    @patch(
        "caylent_devcontainer_cli.commands.setup._prompt_replace_decision",
        return_value=False,
    )
    @patch("caylent_devcontainer_cli.commands.setup._show_python_notice")
    @patch("caylent_devcontainer_cli.commands.setup._show_existing_config")
    def test_existing_config_no_replace_flow(
        self,
        mock_show_config,
        mock_python_notice,
        mock_replace_decision,
        mock_catalog,
        mock_validation,
        mock_interactive,
        capsys,
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".devcontainer"))

            args = MagicMock()
            args.path = tmpdir
            args.catalog_entry = None
            args.catalog_url = None

            handle_setup(args)

            mock_replace_decision.assert_called_once()
            mock_catalog.assert_not_called()
            mock_interactive.assert_called_once_with(tmpdir)

            captured = capsys.readouterr()
            assert "Keeping existing .devcontainer/ files" in captured.err


# ─── handle_setup catalog_entry passthrough ─────────────────────────────────


class TestHandleSetupCatalogEntry:
    """Tests for handle_setup() with --catalog-entry flag."""

    @patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
    @patch("caylent_devcontainer_cli.commands.setup._run_informational_validation")
    @patch("caylent_devcontainer_cli.commands.setup._select_and_copy_catalog")
    def test_passes_catalog_entry_to_select_and_copy(self, mock_catalog, mock_validation, mock_interactive):
        with tempfile.TemporaryDirectory() as tmpdir:
            args = MagicMock()
            args.path = tmpdir
            args.catalog_entry = "my-collection"
            args.catalog_url = None

            handle_setup(args)

            mock_catalog.assert_called_once_with(tmpdir, catalog_entry="my-collection", catalog_url_override=None)

    @patch("caylent_devcontainer_cli.commands.setup.interactive_setup")
    @patch("caylent_devcontainer_cli.commands.setup._run_informational_validation")
    @patch("caylent_devcontainer_cli.commands.setup._select_and_copy_catalog")
    def test_passes_none_when_no_catalog_entry(self, mock_catalog, mock_validation, mock_interactive):
        with tempfile.TemporaryDirectory() as tmpdir:
            args = MagicMock()
            args.path = tmpdir
            args.catalog_entry = None
            args.catalog_url = None

            handle_setup(args)

            mock_catalog.assert_called_once_with(tmpdir, catalog_entry=None, catalog_url_override=None)


# ─── _select_and_copy_catalog ───────────────────────────────────────────────


def _make_entry(name="default", description="Default entry", tags=None, min_cli_version=None):
    """Helper to create a EntryInfo for testing."""
    return EntryInfo(
        path=f"/tmp/catalog/catalog/{name}",
        entry=CatalogEntry(
            name=name,
            description=description,
            tags=tags or [],
            min_cli_version=min_cli_version,
        ),
    )


class TestSelectAndCopyCatalog:
    """Tests for _select_and_copy_catalog()."""

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.copy_entry_to_project")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.check_min_cli_version",
        return_value=True,
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.resolve_default_catalog_url",
        return_value="https://example.com/repo.git@2.1.0",
    )
    def test_default_flow_no_env_url(
        self,
        mock_resolve,
        mock_clone,
        mock_version,
        mock_discover,
        mock_copy,
        mock_rmtree,
    ):
        """No DEVCONTAINER_CATALOG_URL → resolve default tag, clone, auto-select single entry."""
        entry = _make_entry()
        mock_discover.return_value = [entry]

        with patch.dict(os.environ, {}, clear=True):
            _select_and_copy_catalog("/target")

        mock_resolve.assert_called_once()
        mock_clone.assert_called_once()
        mock_copy.assert_called_once()
        # Verify temp dir cleanup
        mock_rmtree.assert_called_once_with("/tmp/catalog", ignore_errors=True)

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.copy_entry_to_project")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.check_min_cli_version",
        return_value=True,
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.resolve_default_catalog_url",
        return_value="https://example.com/repo.git@2.1.0",
    )
    def test_auto_select_single_entry(
        self,
        mock_resolve,
        mock_clone,
        mock_version,
        mock_discover,
        mock_copy,
        mock_rmtree,
    ):
        """When only one compatible entry, auto-select it."""
        entry = _make_entry()
        mock_discover.return_value = [entry]

        with patch.dict(os.environ, {}, clear=True):
            _select_and_copy_catalog("/target")

        # Should log auto-selection, not prompt
        mock_copy.assert_called_once()
        call_args = mock_copy.call_args
        assert call_args[0][0] == entry.path

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.copy_entry_to_project")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.check_min_cli_version",
        return_value=True,
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.validate_catalog_entry_env",
        return_value="https://example.com/catalog.git",
    )
    @patch("caylent_devcontainer_cli.commands.setup._display_and_confirm_entry")
    @patch("caylent_devcontainer_cli.utils.catalog.find_entry_by_name")
    def test_catalog_entry_flag_flow(
        self,
        mock_find,
        mock_confirm,
        mock_validate_env,
        mock_clone,
        mock_version,
        mock_discover,
        mock_copy,
        mock_rmtree,
    ):
        """--catalog-entry flag: validate env, find by name, confirm, copy."""
        entry = _make_entry(name="my-collection")
        mock_discover.return_value = [entry]
        mock_find.return_value = entry

        _select_and_copy_catalog("/target", catalog_entry="my-collection")

        mock_validate_env.assert_called_once_with("my-collection")
        mock_clone.assert_called_once_with("https://example.com/catalog.git")
        mock_find.assert_called_once()
        mock_confirm.assert_called_once_with(entry)
        mock_copy.assert_called_once()

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.copy_entry_to_project")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.check_min_cli_version",
        return_value=True,
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch(
        "caylent_devcontainer_cli.commands.setup._prompt_source_selection",
        return_value="default",
    )
    @patch("caylent_devcontainer_cli.utils.catalog.find_entry_by_name")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.resolve_default_catalog_url",
        return_value="https://example.com/repo.git@2.1.0",
    )
    def test_env_url_default_selection(
        self,
        mock_resolve,
        mock_find,
        mock_source,
        mock_clone,
        mock_version,
        mock_discover,
        mock_copy,
        mock_rmtree,
    ):
        """DEVCONTAINER_CATALOG_URL set, user picks 'Default'."""
        entry = _make_entry()
        other = _make_entry(name="other")
        mock_discover.return_value = [entry, other]
        mock_find.return_value = entry

        with patch.dict(os.environ, {"DEVCONTAINER_CATALOG_URL": "https://example.com/cat.git"}):
            _select_and_copy_catalog("/target")

        mock_resolve.assert_called_once()
        mock_source.assert_called_once()
        mock_find.assert_called_once()
        # Verify find was called with "default" name
        assert mock_find.call_args[0][1] == "default"
        mock_copy.assert_called_once()

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.copy_entry_to_project")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.check_min_cli_version",
        return_value=True,
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch(
        "caylent_devcontainer_cli.commands.setup._prompt_source_selection",
        return_value="browse",
    )
    @patch("caylent_devcontainer_cli.commands.setup._browse_entries")
    def test_env_url_browse_selection(
        self,
        mock_browse,
        mock_source,
        mock_clone,
        mock_version,
        mock_discover,
        mock_copy,
        mock_rmtree,
    ):
        """DEVCONTAINER_CATALOG_URL set, user picks 'Browse'. No duplicate confirm."""
        entry = _make_entry(name="java-backend")
        entry2 = _make_entry(name="angular-frontend")
        mock_discover.return_value = [entry, entry2]
        mock_browse.return_value = entry

        with patch.dict(os.environ, {"DEVCONTAINER_CATALOG_URL": "https://example.com/cat.git"}):
            _select_and_copy_catalog("/target")

        mock_source.assert_called_once()
        mock_browse.assert_called_once()
        mock_copy.assert_called_once()

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.copy_entry_to_project")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.check_min_cli_version",
        return_value=True,
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch(
        "caylent_devcontainer_cli.commands.setup._prompt_source_selection",
        return_value="browse",
    )
    @patch("caylent_devcontainer_cli.commands.setup._browse_entries")
    def test_browse_single_entry_shows_ui(
        self,
        mock_browse,
        mock_source,
        mock_clone,
        mock_version,
        mock_discover,
        mock_copy,
        mock_rmtree,
    ):
        """Browse with single entry still shows selection UI instead of auto-selecting."""
        entry = _make_entry(name="java-backend")
        mock_discover.return_value = [entry]
        mock_browse.return_value = entry

        with patch.dict(os.environ, {"DEVCONTAINER_CATALOG_URL": "https://example.com/cat.git"}):
            _select_and_copy_catalog("/target")

        mock_source.assert_called_once()
        mock_browse.assert_called_once()
        mock_copy.assert_called_once()

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.copy_entry_to_project")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.check_min_cli_version",
        return_value=True,
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    def test_catalog_url_override_bypasses_tag_resolution(
        self, mock_clone, mock_version, mock_discover, mock_copy, mock_rmtree
    ):
        """--catalog-url overrides default tag resolution and env var."""
        entry = _make_entry()
        mock_discover.return_value = [entry]

        with patch.dict(os.environ, {}, clear=True):
            _select_and_copy_catalog(
                "/target",
                catalog_url_override="https://example.com/repo.git@feature/test",
            )

        mock_clone.assert_called_once_with("https://example.com/repo.git@feature/test")
        mock_copy.assert_called_once()

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.copy_entry_to_project")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.check_min_cli_version",
        return_value=True,
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch("caylent_devcontainer_cli.commands.setup._display_and_confirm_entry")
    @patch("caylent_devcontainer_cli.utils.catalog.find_entry_by_name")
    def test_catalog_url_override_with_catalog_entry(
        self,
        mock_find,
        mock_confirm,
        mock_clone,
        mock_version,
        mock_discover,
        mock_copy,
        mock_rmtree,
    ):
        """--catalog-url with --catalog-entry: clone from override, select by name."""
        entry = _make_entry(name="my-collection")
        mock_discover.return_value = [entry]
        mock_find.return_value = entry

        _select_and_copy_catalog(
            "/target",
            catalog_entry="my-collection",
            catalog_url_override="https://example.com/repo.git@v2.0.0",
        )

        mock_clone.assert_called_once_with("https://example.com/repo.git@v2.0.0")
        mock_find.assert_called_once()
        mock_confirm.assert_called_once_with(entry)
        mock_copy.assert_called_once()

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.copy_entry_to_project")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.check_min_cli_version",
        return_value=True,
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch("caylent_devcontainer_cli.commands.setup._prompt_source_selection")
    def test_catalog_url_override_takes_precedence_over_env(
        self,
        mock_source,
        mock_clone,
        mock_version,
        mock_discover,
        mock_copy,
        mock_rmtree,
    ):
        """--catalog-url takes precedence over DEVCONTAINER_CATALOG_URL — no source prompt shown."""
        entry = _make_entry()
        mock_discover.return_value = [entry]

        with patch.dict(
            os.environ,
            {"DEVCONTAINER_CATALOG_URL": "https://example.com/env-catalog.git"},
        ):
            _select_and_copy_catalog(
                "/target",
                catalog_url_override="https://example.com/repo.git@feature/test",
            )

        mock_clone.assert_called_once_with("https://example.com/repo.git@feature/test")
        mock_source.assert_not_called()
        mock_copy.assert_called_once()

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.check_min_cli_version",
        return_value=False,
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.resolve_default_catalog_url",
        return_value="https://example.com/repo.git@2.1.0",
    )
    def test_no_compatible_entries_exits(self, mock_resolve, mock_clone, mock_version, mock_discover, mock_rmtree):
        """Exits when all entries filtered by min_cli_version."""
        mock_discover.return_value = [_make_entry(min_cli_version="99.0.0")]

        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(SystemExit),
        ):
            _select_and_copy_catalog("/target")

        mock_rmtree.assert_called_once_with("/tmp/catalog", ignore_errors=True)

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.copy_entry_to_project")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch("caylent_devcontainer_cli.utils.catalog.check_min_cli_version")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.resolve_default_catalog_url",
        return_value="https://example.com/repo.git@2.1.0",
    )
    def test_filters_incompatible_and_uses_compatible(
        self,
        mock_resolve,
        mock_clone,
        mock_version,
        mock_discover,
        mock_copy,
        mock_rmtree,
        capsys,
    ):
        """Warns about incompatible entries and uses compatible ones."""
        compatible = _make_entry(name="compatible")
        incompatible = _make_entry(name="incompatible", min_cli_version="99.0.0")
        mock_discover.return_value = [compatible, incompatible]
        mock_version.side_effect = lambda v: v != "99.0.0"

        with patch.dict(os.environ, {}, clear=True):
            _select_and_copy_catalog("/target")

        captured = capsys.readouterr()
        assert "Skipping 'incompatible'" in captured.err
        mock_copy.assert_called_once()

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.resolve_default_catalog_url",
        return_value="https://example.com/repo.git@2.1.0",
    )
    def test_cleanup_on_exception(self, mock_resolve, mock_clone, mock_discover, mock_rmtree):
        """Temp dir cleaned up even on exception."""
        mock_discover.side_effect = RuntimeError("test error")

        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(RuntimeError),
        ):
            _select_and_copy_catalog("/target")

        mock_rmtree.assert_called_once_with("/tmp/catalog", ignore_errors=True)

    @patch("shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.copy_entry_to_project")
    @patch("caylent_devcontainer_cli.utils.catalog.discover_entries")
    @patch(
        "caylent_devcontainer_cli.utils.catalog.check_min_cli_version",
        return_value=True,
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.clone_catalog_repo",
        return_value="/tmp/catalog",
    )
    @patch(
        "caylent_devcontainer_cli.utils.catalog.resolve_default_catalog_url",
        return_value="https://example.com/repo.git@2.1.0",
    )
    def test_no_min_cli_version_included(
        self,
        mock_resolve,
        mock_clone,
        mock_version,
        mock_discover,
        mock_copy,
        mock_rmtree,
    ):
        """Entries without min_cli_version are always included."""
        entry = _make_entry(min_cli_version=None)
        mock_discover.return_value = [entry]

        with patch.dict(os.environ, {}, clear=True):
            _select_and_copy_catalog("/target")

        mock_copy.assert_called_once()
        # check_min_cli_version should not be called for None min_cli_version
        mock_version.assert_not_called()


# ─── _prompt_source_selection ────────────────────────────────────────────────


class TestPromptSourceSelection:
    """Tests for _prompt_source_selection()."""

    @patch("questionary.select")
    def test_returns_default_when_selected(self, mock_select):
        mock_select.return_value.ask.return_value = "default"
        result = _prompt_source_selection()
        assert result == "default"

    @patch("questionary.select")
    def test_returns_browse_when_selected(self, mock_select):
        mock_select.return_value.ask.return_value = "browse"
        result = _prompt_source_selection()
        assert result == "browse"

    @patch("questionary.select")
    def test_exits_on_none(self, mock_select):
        mock_select.return_value.ask.return_value = None
        with pytest.raises(SystemExit):
            _prompt_source_selection()


# ─── _browse_entries ─────────────────────────────────────────────────────


class TestBrowseEntries:
    """Tests for _browse_entries()."""

    @patch("questionary.confirm")
    @patch("questionary.select")
    def test_returns_selected_on_confirm(self, mock_select, mock_confirm):
        entry = _make_entry(name="java-backend", description="Java Backend")
        mock_select.return_value.ask.return_value = entry
        mock_confirm.return_value.ask.return_value = True

        result = _browse_entries([entry])

        assert result == entry
        mock_select.assert_called_once()
        mock_confirm.assert_called_once()

    @patch("questionary.confirm")
    @patch("questionary.select")
    def test_loops_on_decline_then_confirms(self, mock_select, mock_confirm):
        entry1 = _make_entry(name="java-backend", description="Java Backend")
        entry2 = _make_entry(name="angular-frontend", description="Angular Frontend")
        mock_select.return_value.ask.side_effect = [entry1, entry2]
        mock_confirm.return_value.ask.side_effect = [False, True]

        result = _browse_entries([entry1, entry2])

        assert result == entry2
        assert mock_select.return_value.ask.call_count == 2
        assert mock_confirm.return_value.ask.call_count == 2

    @patch("questionary.confirm")
    @patch("questionary.select")
    def test_exits_on_select_none(self, mock_select, mock_confirm):
        mock_select.return_value.ask.return_value = None
        with pytest.raises(SystemExit):
            _browse_entries([_make_entry()])


# ─── _display_entry_metadata ────────────────────────────────────────────


class TestDisplayEntryMetadata:
    """Tests for _display_entry_metadata()."""

    def test_displays_name_and_description(self, capsys):
        entry = _make_entry(name="test-collection", description="A test collection")
        _display_entry_metadata(entry)

        captured = capsys.readouterr()
        assert "test-collection" in captured.out
        assert "A test collection" in captured.out

    def test_displays_tags(self, capsys):
        entry = _make_entry(tags=["java", "spring"])
        _display_entry_metadata(entry)

        captured = capsys.readouterr()
        assert "java, spring" in captured.out

    def test_displays_maintainer(self, capsys):
        entry = EntryInfo(
            path="/tmp/test",
            entry=CatalogEntry(
                name="test",
                description="Test",
                maintainer="Team A",
            ),
        )
        _display_entry_metadata(entry)

        captured = capsys.readouterr()
        assert "Team A" in captured.out

    def test_displays_min_cli_version(self, capsys):
        entry = _make_entry(min_cli_version="2.0.0")
        _display_entry_metadata(entry)

        captured = capsys.readouterr()
        assert "2.0.0" in captured.out

    def test_hides_optional_fields_when_empty(self, capsys):
        entry = _make_entry(tags=[], min_cli_version=None)
        _display_entry_metadata(entry)

        captured = capsys.readouterr()
        assert "Tags:" not in captured.out
        assert "Maintainer:" not in captured.out
        assert "Min CLI:" not in captured.out


# ─── _display_and_confirm_entry ─────────────────────────────────────────


class TestDisplayAndConfirmEntry:
    """Tests for _display_and_confirm_entry()."""

    @patch("questionary.confirm")
    def test_proceeds_when_confirmed(self, mock_confirm, capsys):
        mock_confirm.return_value.ask.return_value = True
        entry = _make_entry(name="my-collection", description="My Collection")

        _display_and_confirm_entry(entry)

        captured = capsys.readouterr()
        assert "my-collection" in captured.out

    @patch("questionary.confirm")
    def test_exits_when_declined(self, mock_confirm):
        mock_confirm.return_value.ask.return_value = False
        entry = _make_entry()

        with pytest.raises(SystemExit):
            _display_and_confirm_entry(entry)

    @patch("questionary.confirm")
    def test_exits_on_none(self, mock_confirm):
        mock_confirm.return_value.ask.return_value = None
        entry = _make_entry()

        with pytest.raises(SystemExit):
            _display_and_confirm_entry(entry)


# ─── create_version_file ────────────────────────────────────────────────────


@patch("builtins.open", new_callable=mock_open)
def test_create_version_file(mock_file):
    target_path = "/test/path"
    create_version_file(target_path)

    mock_file.assert_called_once_with(os.path.join(target_path, ".devcontainer", "VERSION"), "w")
    mock_file().write.assert_called_once_with(__version__ + "\n")


# ─── setup_interactive tests (unchanged) ────────────────────────────────────


def test_json_validator_valid():
    validator = JsonValidator()
    document = MagicMock()
    document.text = '{"key": "value"}'
    validator.validate(document)


def test_json_validator_invalid():
    validator = JsonValidator()
    document = MagicMock()
    document.text = '{"key": value}'

    with pytest.raises(Exception):
        validator.validate(document)


def test_json_validator_empty():
    validator = JsonValidator()
    document = MagicMock()
    document.text = ""
    validator.validate(document)


@patch("os.path.exists", return_value=True)
@patch(
    "os.listdir",
    return_value=["template1.json", "template2.json", "not-a-template.txt"],
)
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


@patch(
    "caylent_devcontainer_cli.commands.setup_interactive.list_templates",
    return_value=["template1"],
)
@patch("questionary.confirm")
def test_prompt_use_template_with_templates(mock_confirm, mock_list):
    mock_confirm.return_value.ask.return_value = True
    result = prompt_use_template()
    assert result is True
    mock_confirm.assert_called_once()


@patch(
    "caylent_devcontainer_cli.commands.setup_interactive.list_templates",
    return_value=[],
)
def test_prompt_use_template_no_templates(mock_list):
    result = prompt_use_template()
    assert result is False


@patch(
    "caylent_devcontainer_cli.commands.setup_interactive.list_templates",
    return_value=["template1", "template2"],
)
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
    mock_select.return_value.ask.return_value = "true"
    mock_text.return_value.ask.side_effect = [
        "main",
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
    assert result["DEVELOPER_NAME"] == "Test User"
    assert result["GIT_TOKEN"] == "token123"


@patch("questionary.confirm")
def test_prompt_aws_profile_map_skip(mock_confirm):
    mock_confirm.return_value.ask.return_value = False
    result = prompt_aws_profile_map()
    assert result == {}


@patch("questionary.confirm")
@patch("questionary.text")
@patch("questionary.select")
def test_prompt_aws_profile_map(mock_select, mock_text, mock_confirm):
    mock_confirm.return_value.ask.return_value = True
    mock_select.return_value.ask.return_value = "JSON format (paste complete configuration)"
    mock_text.return_value.ask.return_value = '{"default": {"region": "us-west-2"}}'

    result = prompt_aws_profile_map()
    assert result == {"default": {"region": "us-west-2"}}


@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map")
@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_custom_env_vars")
@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_with_confirmation")
def test_create_template_interactive_with_aws(mock_pwc, mock_custom, mock_aws):
    mock_pwc.side_effect = [
        "true",  # 1. AWS_CONFIG_ENABLED
        "main",  # 2. DEFAULT_GIT_BRANCH
        "Dev Name",  # 3. DEVELOPER_NAME
        "github.com",  # 4. GIT_PROVIDER_URL
        "token",  # 5. GIT_AUTH_METHOD
        "user",  # 6. GIT_USER
        "e@e.com",  # 7. GIT_USER_EMAIL
        "tok123",  # 8. GIT_TOKEN
        "",  # 9. EXTRA_APT_PACKAGES
        "cat",  # 10. PAGER
        "json",  # 11. AWS_DEFAULT_OUTPUT
        "false",  # 12. HOST_PROXY
    ]
    mock_custom.return_value = {}
    mock_aws.return_value = {"default": {"region": "us-west-2"}}

    result = create_template_interactive()

    assert result["containerEnv"]["AWS_CONFIG_ENABLED"] == "true"
    assert result["aws_profile_map"] == {"default": {"region": "us-west-2"}}


@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_custom_env_vars")
@patch("caylent_devcontainer_cli.commands.setup_interactive.prompt_with_confirmation")
def test_create_template_interactive_without_aws(mock_pwc, mock_custom):
    mock_pwc.side_effect = [
        "false",  # 1. AWS_CONFIG_ENABLED
        "main",  # 2. DEFAULT_GIT_BRANCH
        "Dev Name",  # 3. DEVELOPER_NAME
        "github.com",  # 4. GIT_PROVIDER_URL
        "token",  # 5. GIT_AUTH_METHOD
        "user",  # 6. GIT_USER
        "e@e.com",  # 7. GIT_USER_EMAIL
        "tok123",  # 8. GIT_TOKEN
        "",  # 9. EXTRA_APT_PACKAGES
        "cat",  # 10. PAGER
        "false",  # 11. HOST_PROXY
    ]
    mock_custom.return_value = {}

    result = create_template_interactive()

    assert result["containerEnv"]["AWS_CONFIG_ENABLED"] == "false"
    assert result["aws_profile_map"] == {}


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
    assert template_data["template_name"] == "test-template"
    assert "template_path" in template_data


@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data='{"env_values": {}}')
def test_load_template_from_file(mock_file, mock_exists):
    with patch("json.load", return_value={"env_values": {}}):
        result = load_template_from_file("test-template")

    assert "env_values" in result
    assert "cli_version" in result


@patch("os.path.exists", return_value=False)
def test_load_template_from_file_not_found(mock_exists):
    with patch("sys.exit", side_effect=SystemExit(1)):
        with pytest.raises(SystemExit):
            load_template_from_file("non-existent")


def test_load_template_from_file_with_version_parsing_error():
    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true"},
        "cli_version": "invalid-version",
    }

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_template_data))),
        patch("json.load", return_value=mock_template_data),
    ):
        result = load_template_from_file("test-template")

    assert result == mock_template_data


# ─── apply_template tests (updated — no check_and_create_tool_versions) ─────


@patch("caylent_devcontainer_cli.commands.setup_interactive.write_project_files")
def test_apply_template_without_aws(mock_write_files):
    template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "false"},
        "aws_profile_map": {},
    }

    apply_template(template_data, "/target")

    mock_write_files.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.write_project_files")
def test_apply_template_with_aws(mock_write_files):
    template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "true"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
    }

    apply_template(template_data, "/target")

    mock_write_files.assert_called_once()


@patch("caylent_devcontainer_cli.commands.setup_interactive.write_project_files")
def test_apply_template_containerenv(mock_write_files):
    template_data = {
        "containerEnv": {"TEST_VAR": "test_value", "AWS_CONFIG_ENABLED": "false"},
        "aws_profile_map": {},
    }

    apply_template(template_data, "/target")

    mock_write_files.assert_called_once()
    call_args = mock_write_files.call_args
    assert call_args[0][0] == "/target"
    assert call_args[0][1] == template_data


# ─── upgrade_template tests ─────────────────────────────────────────────────


def test_upgrade_template_real():
    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
        "cli_version": "1.0.0",
    }

    with patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["containerEnv"] == mock_template_data["containerEnv"]
    assert result["aws_profile_map"] == mock_template_data["aws_profile_map"]


def test_upgrade_template_with_env_values_real():
    mock_template_data = {
        "env_values": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "aws_profile_map": {"default": {"region": "us-west-2"}},
        "cli_version": "1.0.0",
    }

    with patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["containerEnv"] == mock_template_data["env_values"]


def test_upgrade_template_without_env_values_real():
    mock_template_data = {"cli_version": "1.0.0"}

    with (
        patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"),
        patch(
            "caylent_devcontainer_cli.commands.setup_interactive.prompt_env_values",
            return_value={"AWS_CONFIG_ENABLED": "false"},
        ),
    ):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["containerEnv"] == {"AWS_CONFIG_ENABLED": "false"}


def test_upgrade_template_with_aws_enabled_no_profile_real():
    mock_template_data = {
        "containerEnv": {"AWS_CONFIG_ENABLED": "true", "DEFAULT_GIT_BRANCH": "main"},
        "cli_version": "1.0.0",
    }

    with (
        patch("caylent_devcontainer_cli.commands.setup_interactive.__version__", "2.0.0"),
        patch(
            "caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map",
            return_value={"default": {"region": "us-west-2"}},
        ),
    ):
        result = upgrade_template(mock_template_data)

    assert result["cli_version"] == "2.0.0"
    assert result["aws_profile_map"] == {"default": {"region": "us-west-2"}}


# ─── interactive_setup tests ────────────────────────────────────────────────


@patch(
    "caylent_devcontainer_cli.commands.setup_interactive.prompt_use_template",
    return_value=True,
)
@patch(
    "caylent_devcontainer_cli.commands.setup_interactive.select_template",
    return_value="test-template",
)
@patch("caylent_devcontainer_cli.commands.setup_interactive.load_template_from_file")
@patch("caylent_devcontainer_cli.utils.template.validate_template", side_effect=lambda d: d)
@patch("caylent_devcontainer_cli.commands.setup_interactive.apply_template")
def test_interactive_setup_with_template(mock_apply, mock_validate, mock_load, mock_select, mock_prompt):
    mock_load.return_value = {"env_values": {}, "aws_profile_map": {}}

    interactive_setup("/target")

    mock_prompt.assert_called_once()
    mock_select.assert_called_once()
    mock_load.assert_called_once_with("test-template")
    mock_validate.assert_called_once()
    mock_apply.assert_called_once()


@patch(
    "caylent_devcontainer_cli.commands.setup_interactive.prompt_use_template",
    return_value=False,
)
@patch("caylent_devcontainer_cli.commands.setup_interactive.create_template_interactive")
@patch(
    "caylent_devcontainer_cli.commands.setup_interactive.prompt_save_template",
    return_value=False,
)
@patch("caylent_devcontainer_cli.commands.setup_interactive.apply_template")
def test_interactive_setup_without_template(mock_apply, mock_save_prompt, mock_create, mock_prompt):
    mock_create.return_value = {"env_values": {}, "aws_profile_map": {}}

    interactive_setup("/target")

    mock_prompt.assert_called_once()
    mock_create.assert_called_once()
    mock_save_prompt.assert_called_once()
    mock_apply.assert_called_once()


@patch(
    "caylent_devcontainer_cli.commands.setup_interactive.prompt_use_template",
    return_value=False,
)
@patch("caylent_devcontainer_cli.commands.setup_interactive.create_template_interactive")
@patch(
    "caylent_devcontainer_cli.commands.setup_interactive.prompt_save_template",
    return_value=True,
)
@patch(
    "caylent_devcontainer_cli.commands.setup_interactive.prompt_template_name",
    return_value="new-template",
)
@patch("caylent_devcontainer_cli.commands.setup_interactive.save_template_to_file")
@patch("caylent_devcontainer_cli.commands.setup_interactive.apply_template")
def test_interactive_setup_save_new_template(
    mock_apply, mock_save, mock_name, mock_save_prompt, mock_create, mock_prompt
):
    mock_create.return_value = {"env_values": {}, "aws_profile_map": {}}

    interactive_setup("/target")

    mock_save.assert_called_once_with({"env_values": {}, "aws_profile_map": {}}, "new-template")
    mock_apply.assert_called_once()


@patch(
    "caylent_devcontainer_cli.commands.setup_interactive.prompt_use_template",
    side_effect=KeyboardInterrupt,
)
def test_interactive_setup_keyboard_interrupt(mock_prompt):
    with pytest.raises(SystemExit):
        interactive_setup("/target")


# ─── EXAMPLE_ENV_VALUES ─────────────────────────────────────────────────────


def test_example_env_values_includes_required_keys():
    from caylent_devcontainer_cli.commands.setup import EXAMPLE_ENV_VALUES

    assert "GIT_AUTH_METHOD" in EXAMPLE_ENV_VALUES
    assert EXAMPLE_ENV_VALUES["GIT_AUTH_METHOD"] == "token"
    assert "HOST_PROXY" in EXAMPLE_ENV_VALUES
    assert EXAMPLE_ENV_VALUES["HOST_PROXY"] == "false"
    assert "HOST_PROXY_URL" in EXAMPLE_ENV_VALUES
    assert EXAMPLE_ENV_VALUES["HOST_PROXY_URL"] == ""
    assert "CICD" not in EXAMPLE_ENV_VALUES
