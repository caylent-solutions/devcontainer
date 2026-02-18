"""Unit tests for catalog CLI commands."""

import argparse
import json
import os
import tempfile
from io import StringIO
from unittest import TestCase
from unittest.mock import MagicMock, patch

from caylent_devcontainer_cli.commands.catalog import (
    CATALOG_URL_ENV_VAR,
    _get_catalog_url,
    _run_validation,
    handle_catalog_list,
    handle_catalog_validate,
    register_command,
)
from caylent_devcontainer_cli.utils.catalog import (
    CatalogEntry,
    EntryInfo,
    check_min_cli_version,
    compare_semver,
    find_entry_by_name,
    validate_catalog_entry_env,
)
from caylent_devcontainer_cli.utils.constants import (
    CATALOG_COMMON_SUBDIR_REQUIRED_FILES,
    CATALOG_COMMON_SUBDIRS,
    CATALOG_ENTRY_FILENAME,
    CATALOG_EXECUTABLE_COMMON_ASSETS,
    CATALOG_EXECUTABLE_SUBDIR_ASSETS,
    CATALOG_REQUIRED_COMMON_ASSETS,
    CATALOG_VERSION_FILENAME,
    DEFAULT_CATALOG_URL,
)


def _create_valid_common_assets(assets_dir):
    """Create a fully valid common/devcontainer-assets/ directory."""
    os.makedirs(assets_dir, exist_ok=True)
    for filename in CATALOG_REQUIRED_COMMON_ASSETS:
        filepath = os.path.join(assets_dir, filename)
        with open(filepath, "w") as f:
            f.write("#!/bin/bash\n")
        if filename in CATALOG_EXECUTABLE_COMMON_ASSETS:
            os.chmod(filepath, 0o755)
    for subdir in CATALOG_COMMON_SUBDIRS:
        subdir_path = os.path.join(assets_dir, subdir)
        os.makedirs(subdir_path, exist_ok=True)
        for req_file in CATALOG_COMMON_SUBDIR_REQUIRED_FILES:
            filepath = os.path.join(subdir_path, req_file)
            with open(filepath, "w") as f:
                f.write("#!/bin/bash\n" if req_file.endswith(".sh") else "# placeholder\n")
        for exec_file in CATALOG_EXECUTABLE_SUBDIR_ASSETS:
            filepath = os.path.join(subdir_path, exec_file)
            if os.path.isfile(filepath):
                os.chmod(filepath, 0o755)


class TestGetCatalogUrl(TestCase):
    """Test _get_catalog_url() env var precedence."""

    @patch("caylent_devcontainer_cli.commands.catalog.resolve_default_catalog_url")
    def test_returns_default_when_no_env_var(self, mock_resolve):
        resolved_url = f"{DEFAULT_CATALOG_URL}@2.1.0"
        mock_resolve.return_value = resolved_url
        with patch.dict(os.environ, {}, clear=True):
            url, label = _get_catalog_url()
            self.assertEqual(url, resolved_url)
            self.assertEqual(label, "default catalog")
        mock_resolve.assert_called_once()

    def test_returns_env_var_when_set(self):
        with patch.dict(os.environ, {CATALOG_URL_ENV_VAR: "https://custom.com/repo.git"}):
            url, label = _get_catalog_url()
            self.assertEqual(url, "https://custom.com/repo.git")
            self.assertEqual(label, "https://custom.com/repo.git")

    @patch("caylent_devcontainer_cli.commands.catalog.resolve_default_catalog_url")
    def test_returns_default_when_env_var_empty(self, mock_resolve):
        resolved_url = f"{DEFAULT_CATALOG_URL}@2.1.0"
        mock_resolve.return_value = resolved_url
        with patch.dict(os.environ, {CATALOG_URL_ENV_VAR: ""}):
            url, label = _get_catalog_url()
            self.assertEqual(url, resolved_url)
            self.assertEqual(label, "default catalog")
        mock_resolve.assert_called_once()


class TestRegisterCommand(TestCase):
    """Test register_command() argparse registration."""

    def test_registers_catalog_subcommand(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_command(subparsers)

        # Parse 'catalog list'
        args = parser.parse_args(["catalog", "list"])
        self.assertEqual(args.catalog_command, "list")
        self.assertTrue(hasattr(args, "func"))
        self.assertIsNone(args.tags)

    def test_registers_list_with_tags_flag(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_command(subparsers)

        args = parser.parse_args(["catalog", "list", "--tags", "java,python"])
        self.assertEqual(args.tags, "java,python")

    def test_registers_validate_subcommand(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_command(subparsers)

        args = parser.parse_args(["catalog", "validate"])
        self.assertEqual(args.catalog_command, "validate")
        self.assertTrue(hasattr(args, "func"))
        self.assertIsNone(args.local)

    def test_registers_validate_with_local_flag(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_command(subparsers)

        args = parser.parse_args(["catalog", "validate", "--local", "/path/to/catalog"])
        self.assertEqual(args.local, "/path/to/catalog")

    def test_registers_list_with_catalog_url_flag(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_command(subparsers)

        args = parser.parse_args(["catalog", "list", "--catalog-url", "https://example.com/repo.git@v2.0.0"])
        self.assertEqual(args.catalog_url, "https://example.com/repo.git@v2.0.0")

    def test_registers_validate_with_catalog_url_flag(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_command(subparsers)

        args = parser.parse_args(
            [
                "catalog",
                "validate",
                "--catalog-url",
                "https://example.com/repo.git@v2.0.0",
            ]
        )
        self.assertEqual(args.catalog_url, "https://example.com/repo.git@v2.0.0")

    def test_list_catalog_url_defaults_to_none(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_command(subparsers)

        args = parser.parse_args(["catalog", "list"])
        self.assertIsNone(args.catalog_url)

    def test_validate_catalog_url_defaults_to_none(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_command(subparsers)

        args = parser.parse_args(["catalog", "validate"])
        self.assertIsNone(args.catalog_url)


class TestHandleCatalogList(TestCase):
    """Test handle_catalog_list() display and filtering."""

    def _make_entries(self, entries_data):
        """Create EntryInfo list from (name, description, tags, min_cli_version) tuples."""
        result = []
        for item in entries_data:
            if len(item) == 3:
                name, desc, tags = item
                min_ver = None
            else:
                name, desc, tags, min_ver = item
            result.append(
                EntryInfo(
                    path=f"/tmp/{name}",
                    entry=CatalogEntry(name=name, description=desc, tags=tags, min_cli_version=min_ver),
                )
            )
        return result

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.validate_common_assets")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_displays_entries(self, mock_get_url, mock_clone, mock_validate, mock_discover, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_validate.return_value = []
        mock_discover.return_value = self._make_entries(
            [
                ("default", "General-purpose dev environment", ["general"]),
                ("java-spring", "Java Spring Boot environment", ["java"]),
            ]
        )

        args = MagicMock()
        args.tags = None
        args.catalog_url = None

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            handle_catalog_list(args)

        output = mock_stdout.getvalue()
        self.assertIn("Available DevContainer Configurations (default catalog):", output)
        self.assertIn("default", output)
        self.assertIn("General-purpose dev environment", output)
        self.assertIn("java-spring", output)
        self.assertIn("Java Spring Boot environment", output)
        mock_rmtree.assert_called_once_with("/tmp/catalog-test", ignore_errors=True)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.validate_common_assets")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_filters_by_tags(self, mock_get_url, mock_clone, mock_validate, mock_discover, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_validate.return_value = []
        mock_discover.return_value = self._make_entries(
            [
                ("default", "General", ["general", "multi-language"]),
                ("java-spring", "Java", ["java", "spring-boot"]),
                ("python-data", "Python", ["python", "data"]),
            ]
        )

        args = MagicMock()
        args.tags = "java,python"
        args.catalog_url = None

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            handle_catalog_list(args)

        output = mock_stdout.getvalue()
        self.assertIn("java-spring", output)
        self.assertIn("python-data", output)
        # "default" entry should not appear in data lines (header contains "default catalog")
        data_lines = [line for line in output.split("\n") if line.strip() and "Available" not in line]
        data_text = "\n".join(data_lines)
        self.assertNotIn("General", data_text)  # default's description should be absent

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.validate_common_assets")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_no_tag_matches(self, mock_get_url, mock_clone, mock_validate, mock_discover, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_validate.return_value = []
        mock_discover.return_value = self._make_entries(
            [("default", "General", ["general"])],
        )

        args = MagicMock()
        args.tags = "nonexistent-tag"
        args.catalog_url = None

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            handle_catalog_list(args)

        output = mock_stderr.getvalue()
        self.assertIn("No entries found matching tags: nonexistent-tag", output)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.validate_common_assets")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_empty_catalog_exits_nonzero(
        self, mock_get_url, mock_clone, mock_validate, mock_discover, mock_rmtree
    ):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_validate.return_value = []
        mock_discover.return_value = []

        args = MagicMock()
        args.tags = None
        args.catalog_url = None

        with self.assertRaises(SystemExit) as ctx:
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                handle_catalog_list(args)

        self.assertEqual(ctx.exception.code, 1)
        output = mock_stderr.getvalue()
        self.assertIn("No devcontainer entries found", output)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.validate_common_assets")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_cleans_up_on_exception(self, mock_get_url, mock_clone, mock_validate, mock_discover, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_validate.return_value = []
        mock_discover.side_effect = RuntimeError("unexpected error")

        args = MagicMock()
        args.tags = None
        args.catalog_url = None

        with self.assertRaises(RuntimeError):
            handle_catalog_list(args)

        mock_rmtree.assert_called_once_with("/tmp/catalog-test", ignore_errors=True)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.validate_common_assets")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_uses_env_var_source_label(self, mock_get_url, mock_clone, mock_validate, mock_discover, mock_rmtree):
        mock_get_url.return_value = (
            "https://custom.com/catalog.git",
            "https://custom.com/catalog.git",
        )
        mock_clone.return_value = "/tmp/catalog-test"
        mock_validate.return_value = []
        mock_discover.return_value = self._make_entries(
            [("my-app", "My app", [])],
        )

        args = MagicMock()
        args.tags = None
        args.catalog_url = None

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            handle_catalog_list(args)

        output = mock_stdout.getvalue()
        self.assertIn("https://custom.com/catalog.git", output)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.validate_common_assets")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_missing_common_assets_exits_nonzero(self, mock_get_url, mock_clone, mock_validate, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_validate.return_value = ["Missing required directory: common/devcontainer-assets/"]

        args = MagicMock()
        args.tags = None
        args.catalog_url = None

        with self.assertRaises(SystemExit) as ctx:
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                handle_catalog_list(args)

        self.assertEqual(ctx.exception.code, 1)
        output = mock_stderr.getvalue()
        self.assertIn("missing required directory", output.lower())

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.check_min_cli_version")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.validate_common_assets")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_skips_incompatible_min_cli_version(
        self,
        mock_get_url,
        mock_clone,
        mock_validate,
        mock_discover,
        mock_check_ver,
        mock_rmtree,
    ):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_validate.return_value = []
        mock_discover.return_value = self._make_entries(
            [
                ("compatible-app", "Compatible app", ["general"], "2.0.0"),
                ("future-app", "Needs future CLI", ["general"], "99.0.0"),
            ]
        )
        # compatible-app passes version check, future-app does not
        mock_check_ver.side_effect = lambda v: v == "2.0.0"

        args = MagicMock()
        args.tags = None
        args.catalog_url = None

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                handle_catalog_list(args)

        stdout_output = mock_stdout.getvalue()
        stderr_output = mock_stderr.getvalue()
        self.assertIn("compatible-app", stdout_output)
        self.assertNotIn("future-app", stdout_output)
        self.assertIn("Skipping 'future-app'", stderr_output)
        self.assertIn("99.0.0", stderr_output)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.check_min_cli_version")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.validate_common_assets")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_all_incompatible_shows_info(
        self,
        mock_get_url,
        mock_clone,
        mock_validate,
        mock_discover,
        mock_check_ver,
        mock_rmtree,
    ):
        """When all entries are filtered by min_cli_version, show info message."""
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_validate.return_value = []
        mock_discover.return_value = self._make_entries(
            [
                ("future-a", "Future A", ["general"], "99.0.0"),
                ("future-b", "Future B", ["general"], "99.0.0"),
            ]
        )
        mock_check_ver.return_value = False  # All incompatible

        args = MagicMock()
        args.tags = None
        args.catalog_url = None

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            handle_catalog_list(args)

        output = mock_stderr.getvalue()
        self.assertIn("No compatible entries found", output)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.check_min_cli_version")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.validate_common_assets")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_no_min_cli_version_included(
        self,
        mock_get_url,
        mock_clone,
        mock_validate,
        mock_discover,
        mock_check_ver,
        mock_rmtree,
    ):
        """Entries without min_cli_version are always included."""
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_validate.return_value = []
        mock_discover.return_value = self._make_entries(
            [
                ("no-version-app", "No version requirement", ["general"]),
            ]
        )
        # check_min_cli_version should NOT be called for entries without min_cli_version

        args = MagicMock()
        args.tags = None
        args.catalog_url = None

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            handle_catalog_list(args)

        stdout_output = mock_stdout.getvalue()
        self.assertIn("no-version-app", stdout_output)
        mock_check_ver.assert_not_called()

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.validate_common_assets")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    def test_list_with_catalog_url_override(self, mock_clone, mock_validate, mock_discover, mock_rmtree):
        """--catalog-url bypasses _get_catalog_url() and uses the override URL."""
        mock_clone.return_value = "/tmp/catalog-test"
        mock_validate.return_value = []
        mock_discover.return_value = self._make_entries(
            [("default", "General-purpose dev environment", ["general"])],
        )

        args = MagicMock()
        args.tags = None
        args.catalog_url = "https://example.com/repo.git@feature/test"

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            handle_catalog_list(args)

        mock_clone.assert_called_once_with("https://example.com/repo.git@feature/test")
        output = mock_stdout.getvalue()
        self.assertIn("https://example.com/repo.git@feature/test", output)


class TestHandleCatalogValidate(TestCase):
    """Test handle_catalog_validate()."""

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog._run_validation")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_validate_remote(self, mock_get_url, mock_clone, mock_run_val, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-val"

        args = MagicMock()
        args.local = None
        args.catalog_url = None

        handle_catalog_validate(args)

        mock_clone.assert_called_once_with("https://example.com/repo.git")
        mock_run_val.assert_called_once_with("/tmp/catalog-val")
        mock_rmtree.assert_called_once_with("/tmp/catalog-val", ignore_errors=True)

    @patch("caylent_devcontainer_cli.commands.catalog._run_validation")
    def test_validate_local(self, mock_run_val):
        with tempfile.TemporaryDirectory() as tmp:
            args = MagicMock()
            args.local = tmp

            handle_catalog_validate(args)

            mock_run_val.assert_called_once_with(os.path.abspath(tmp))

    def test_validate_local_nonexistent_dir(self):
        args = MagicMock()
        args.local = "/nonexistent/path/to/catalog"

        with self.assertRaises(SystemExit):
            handle_catalog_validate(args)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog._run_validation")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_validate_remote_cleans_up_on_exception(self, mock_get_url, mock_clone, mock_run_val, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-val"
        mock_run_val.side_effect = SystemExit(1)

        args = MagicMock()
        args.local = None
        args.catalog_url = None

        with self.assertRaises(SystemExit):
            handle_catalog_validate(args)

        mock_rmtree.assert_called_once_with("/tmp/catalog-val", ignore_errors=True)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog._run_validation")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    def test_validate_with_catalog_url_override(self, mock_clone, mock_run_val, mock_rmtree):
        """--catalog-url bypasses _get_catalog_url() for validate."""
        mock_clone.return_value = "/tmp/catalog-val"

        args = MagicMock()
        args.local = None
        args.catalog_url = "https://example.com/repo.git@feature/test"

        handle_catalog_validate(args)

        mock_clone.assert_called_once_with("https://example.com/repo.git@feature/test")
        mock_run_val.assert_called_once_with("/tmp/catalog-val")
        mock_rmtree.assert_called_once_with("/tmp/catalog-val", ignore_errors=True)


class TestRunValidation(TestCase):
    """Test _run_validation() output and exit codes."""

    def _create_valid_catalog(self, tmp_dir):
        """Create a minimal valid catalog."""
        assets_dir = os.path.join(tmp_dir, "common", "devcontainer-assets")
        _create_valid_common_assets(assets_dir)

        col_dir = os.path.join(tmp_dir, "catalog", "default")
        os.makedirs(col_dir)
        with open(os.path.join(col_dir, CATALOG_ENTRY_FILENAME), "w") as f:
            json.dump({"name": "default", "description": "Default"}, f)
        with open(os.path.join(col_dir, "devcontainer.json"), "w") as f:
            json.dump(
                {
                    "name": "caylent-devcontainer",
                    "image": "mcr.microsoft.com/devcontainers/base:noble",
                    "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
                },
                f,
            )
        with open(os.path.join(col_dir, CATALOG_VERSION_FILENAME), "w") as f:
            f.write("1.0.0")

    def test_valid_catalog_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_catalog(tmp)

            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                _run_validation(tmp)

            output = mock_stderr.getvalue()
            self.assertIn("Catalog validation passed", output)
            self.assertIn("1 entries found", output)

    def test_invalid_catalog_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Empty directory — no common assets, no entries
            with self.assertRaises(SystemExit) as ctx:
                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    _run_validation(tmp)

            self.assertEqual(ctx.exception.code, 1)
            output = mock_stderr.getvalue()
            self.assertIn("Catalog validation failed", output)

    def test_validation_lists_all_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Create catalog with invalid entry
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)

            col_dir = os.path.join(tmp, "catalog", "bad")
            os.makedirs(col_dir)
            # Invalid entry: missing description, bad name
            with open(os.path.join(col_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump({"name": "X"}, f)  # uppercase single char
            # Missing devcontainer.json and VERSION

            with self.assertRaises(SystemExit):
                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    _run_validation(tmp)

            output = mock_stderr.getvalue()
            self.assertIn("issues found", output)

    def test_valid_catalog_with_multiple_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_catalog(tmp)

            # Add second entry
            col2 = os.path.join(tmp, "catalog", "python-app")
            os.makedirs(col2)
            with open(os.path.join(col2, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump({"name": "python-app", "description": "Python app"}, f)
            with open(os.path.join(col2, "devcontainer.json"), "w") as f:
                json.dump(
                    {
                        "name": "caylent-devcontainer",
                        "image": "mcr.microsoft.com/devcontainers/base:noble",
                        "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
                    },
                    f,
                )
            with open(os.path.join(col2, CATALOG_VERSION_FILENAME), "w") as f:
                f.write("1.0.0")

            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                _run_validation(tmp)

            output = mock_stderr.getvalue()
            self.assertIn("2 entries found", output)


class TestCompareSemver(TestCase):
    """Test compare_semver() version comparison."""

    def test_equal_versions(self):
        self.assertEqual(compare_semver("2.0.0", "2.0.0"), 0)

    def test_greater_major(self):
        self.assertEqual(compare_semver("3.0.0", "2.0.0"), 1)

    def test_lesser_major(self):
        self.assertEqual(compare_semver("1.0.0", "2.0.0"), -1)

    def test_greater_minor(self):
        self.assertEqual(compare_semver("2.1.0", "2.0.0"), 1)

    def test_lesser_minor(self):
        self.assertEqual(compare_semver("2.0.0", "2.1.0"), -1)

    def test_greater_patch(self):
        self.assertEqual(compare_semver("2.0.1", "2.0.0"), 1)

    def test_lesser_patch(self):
        self.assertEqual(compare_semver("2.0.0", "2.0.1"), -1)

    def test_complex_comparison(self):
        self.assertEqual(compare_semver("1.10.0", "1.9.0"), 1)

    def test_invalid_version_a(self):
        with self.assertRaises(ValueError) as ctx:
            compare_semver("v2.0", "2.0.0")
        self.assertIn("v2.0", str(ctx.exception))

    def test_invalid_version_b(self):
        with self.assertRaises(ValueError) as ctx:
            compare_semver("2.0.0", "abc")
        self.assertIn("abc", str(ctx.exception))

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            compare_semver("", "2.0.0")


class TestCheckMinCliVersion(TestCase):
    """Test check_min_cli_version() compatibility check."""

    def test_current_meets_minimum(self):
        self.assertTrue(check_min_cli_version("2.0.0", current_version="2.0.0"))

    def test_current_exceeds_minimum(self):
        self.assertTrue(check_min_cli_version("1.5.0", current_version="2.0.0"))

    def test_current_below_minimum(self):
        self.assertFalse(check_min_cli_version("3.0.0", current_version="2.0.0"))

    def test_uses_package_version_by_default(self):
        # When no current_version is passed, it uses __version__
        from caylent_devcontainer_cli import __version__

        # Current version should always be >= itself
        self.assertTrue(check_min_cli_version(__version__))


class TestFindEntryByName(TestCase):
    """Test find_entry_by_name() lookup."""

    def _make_entries(self):
        return [
            EntryInfo(
                path="/tmp/default",
                entry=CatalogEntry(name="default", description="Default"),
            ),
            EntryInfo(
                path="/tmp/java-spring",
                entry=CatalogEntry(name="java-spring", description="Java"),
            ),
        ]

    def test_finds_existing_entry(self):
        entries = self._make_entries()
        result = find_entry_by_name(entries, "java-spring")
        self.assertEqual(result.entry.name, "java-spring")
        self.assertEqual(result.path, "/tmp/java-spring")

    def test_finds_default_entry(self):
        entries = self._make_entries()
        result = find_entry_by_name(entries, "default")
        self.assertEqual(result.entry.name, "default")

    def test_not_found_raises_system_exit(self):
        entries = self._make_entries()
        with self.assertRaises(SystemExit) as ctx:
            find_entry_by_name(entries, "nonexistent")
        msg = str(ctx.exception)
        self.assertIn("Entry 'nonexistent' not found", msg)
        self.assertIn("cdevcontainer catalog list", msg)

    def test_empty_list_raises_system_exit(self):
        with self.assertRaises(SystemExit):
            find_entry_by_name([], "anything")


class TestValidateCatalogEntryEnv(TestCase):
    """Test validate_catalog_entry_env() env var check."""

    def test_returns_url_when_env_set(self):
        with patch.dict(os.environ, {"DEVCONTAINER_CATALOG_URL": "https://custom.com/repo.git"}):
            result = validate_catalog_entry_env("my-collection")
            self.assertEqual(result, "https://custom.com/repo.git")

    def test_raises_when_env_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                validate_catalog_entry_env("my-collection")
            msg = str(ctx.exception)
            self.assertIn("DEVCONTAINER_CATALOG_URL is not set", msg)
            self.assertIn("--catalog-entry", msg)

    def test_raises_when_env_empty(self):
        with patch.dict(os.environ, {"DEVCONTAINER_CATALOG_URL": ""}):
            with self.assertRaises(SystemExit) as ctx:
                validate_catalog_entry_env("my-collection")
            msg = str(ctx.exception)
            self.assertIn("DEVCONTAINER_CATALOG_URL is not set", msg)
