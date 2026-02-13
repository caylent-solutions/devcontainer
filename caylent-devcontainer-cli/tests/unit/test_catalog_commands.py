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
from caylent_devcontainer_cli.utils.catalog import CatalogEntry, CollectionInfo
from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ENTRY_FILENAME,
    CATALOG_REQUIRED_COMMON_ASSETS,
    CATALOG_VERSION_FILENAME,
    DEFAULT_CATALOG_URL,
)


class TestGetCatalogUrl(TestCase):
    """Test _get_catalog_url() env var precedence."""

    def test_returns_default_when_no_env_var(self):
        with patch.dict(os.environ, {}, clear=True):
            url, label = _get_catalog_url()
            self.assertEqual(url, DEFAULT_CATALOG_URL)
            self.assertEqual(label, "default catalog")

    def test_returns_env_var_when_set(self):
        with patch.dict(os.environ, {CATALOG_URL_ENV_VAR: "https://custom.com/repo.git"}):
            url, label = _get_catalog_url()
            self.assertEqual(url, "https://custom.com/repo.git")
            self.assertEqual(label, "https://custom.com/repo.git")

    def test_returns_default_when_env_var_empty(self):
        with patch.dict(os.environ, {CATALOG_URL_ENV_VAR: ""}):
            url, label = _get_catalog_url()
            self.assertEqual(url, DEFAULT_CATALOG_URL)
            self.assertEqual(label, "default catalog")


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


class TestHandleCatalogList(TestCase):
    """Test handle_catalog_list() display and filtering."""

    def _make_entries(self, entries_data):
        """Create CollectionInfo list from (name, description, tags) tuples."""
        return [
            CollectionInfo(
                path=f"/tmp/{name}",
                entry=CatalogEntry(name=name, description=desc, tags=tags),
            )
            for name, desc, tags in entries_data
        ]

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_collection_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_displays_collections(self, mock_get_url, mock_clone, mock_discover, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_discover.return_value = self._make_entries(
            [
                ("default", "General-purpose dev environment", ["general"]),
                ("java-spring", "Java Spring Boot environment", ["java"]),
            ]
        )

        args = MagicMock()
        args.tags = None

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
    @patch("caylent_devcontainer_cli.commands.catalog.discover_collection_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_filters_by_tags(self, mock_get_url, mock_clone, mock_discover, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_discover.return_value = self._make_entries(
            [
                ("default", "General", ["general", "multi-language"]),
                ("java-spring", "Java", ["java", "spring-boot"]),
                ("python-data", "Python", ["python", "data"]),
            ]
        )

        args = MagicMock()
        args.tags = "java,python"

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            handle_catalog_list(args)

        output = mock_stdout.getvalue()
        self.assertIn("java-spring", output)
        self.assertIn("python-data", output)
        # "default" collection should not appear in data lines (header contains "default catalog")
        data_lines = [line for line in output.split("\n") if line.strip() and "Available" not in line]
        data_text = "\n".join(data_lines)
        self.assertNotIn("General", data_text)  # default's description should be absent

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_collection_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_no_tag_matches(self, mock_get_url, mock_clone, mock_discover, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_discover.return_value = self._make_entries(
            [("default", "General", ["general"])],
        )

        args = MagicMock()
        args.tags = "nonexistent-tag"

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            handle_catalog_list(args)

        output = mock_stderr.getvalue()
        self.assertIn("No collections found matching tags: nonexistent-tag", output)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_collection_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_empty_catalog(self, mock_get_url, mock_clone, mock_discover, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_discover.return_value = []

        args = MagicMock()
        args.tags = None

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            handle_catalog_list(args)

        output = mock_stderr.getvalue()
        self.assertIn("No collections found", output)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_collection_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_cleans_up_on_exception(self, mock_get_url, mock_clone, mock_discover, mock_rmtree):
        mock_get_url.return_value = ("https://example.com/repo.git", "default catalog")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_discover.side_effect = RuntimeError("unexpected error")

        args = MagicMock()
        args.tags = None

        with self.assertRaises(RuntimeError):
            handle_catalog_list(args)

        mock_rmtree.assert_called_once_with("/tmp/catalog-test", ignore_errors=True)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_collection_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    @patch("caylent_devcontainer_cli.commands.catalog._get_catalog_url")
    def test_list_uses_env_var_source_label(self, mock_get_url, mock_clone, mock_discover, mock_rmtree):
        mock_get_url.return_value = ("https://custom.com/catalog.git", "https://custom.com/catalog.git")
        mock_clone.return_value = "/tmp/catalog-test"
        mock_discover.return_value = self._make_entries(
            [("my-app", "My app", [])],
        )

        args = MagicMock()
        args.tags = None

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            handle_catalog_list(args)

        output = mock_stdout.getvalue()
        self.assertIn("https://custom.com/catalog.git", output)


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

        with self.assertRaises(SystemExit):
            handle_catalog_validate(args)

        mock_rmtree.assert_called_once_with("/tmp/catalog-val", ignore_errors=True)


class TestRunValidation(TestCase):
    """Test _run_validation() output and exit codes."""

    def _create_valid_catalog(self, tmp_dir):
        """Create a minimal valid catalog."""
        assets_dir = os.path.join(tmp_dir, "common", "devcontainer-assets")
        os.makedirs(assets_dir)
        for filename in CATALOG_REQUIRED_COMMON_ASSETS:
            with open(os.path.join(assets_dir, filename), "w") as f:
                f.write("#!/bin/bash\n")

        col_dir = os.path.join(tmp_dir, "collections", "default")
        os.makedirs(col_dir)
        with open(os.path.join(col_dir, CATALOG_ENTRY_FILENAME), "w") as f:
            json.dump({"name": "default", "description": "Default"}, f)
        with open(os.path.join(col_dir, "devcontainer.json"), "w") as f:
            json.dump(
                {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode"},
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
            self.assertIn("1 collections found", output)

    def test_invalid_catalog_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Empty directory — no common assets, no collections
            with self.assertRaises(SystemExit) as ctx:
                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    _run_validation(tmp)

            self.assertEqual(ctx.exception.code, 1)
            output = mock_stderr.getvalue()
            self.assertIn("Catalog validation failed", output)

    def test_validation_lists_all_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Create catalog with invalid collection
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            os.makedirs(assets_dir)
            for filename in CATALOG_REQUIRED_COMMON_ASSETS:
                with open(os.path.join(assets_dir, filename), "w") as f:
                    f.write("#!/bin/bash\n")

            col_dir = os.path.join(tmp, "collections", "bad")
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

    def test_valid_catalog_with_multiple_collections(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_catalog(tmp)

            # Add second collection
            col2 = os.path.join(tmp, "collections", "python-app")
            os.makedirs(col2)
            with open(os.path.join(col2, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump({"name": "python-app", "description": "Python app"}, f)
            with open(os.path.join(col2, "devcontainer.json"), "w") as f:
                json.dump(
                    {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode"},
                    f,
                )
            with open(os.path.join(col2, CATALOG_VERSION_FILENAME), "w") as f:
                f.write("1.0.0")

            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                _run_validation(tmp)

            output = mock_stderr.getvalue()
            self.assertIn("2 collections found", output)
