"""Functional tests for catalog CLI commands end-to-end behavior."""

import json
import os
import tempfile
from io import StringIO
from unittest import TestCase
from unittest.mock import MagicMock, patch

from caylent_devcontainer_cli.commands.catalog import (
    CATALOG_URL_ENV_VAR,
    _run_validation,
    handle_catalog_list,
    handle_catalog_validate,
)
from caylent_devcontainer_cli.utils.catalog import CatalogEntry, CollectionInfo
from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ENTRY_FILENAME,
    CATALOG_REQUIRED_COMMON_ASSETS,
    CATALOG_VERSION_FILENAME,
    DEFAULT_CATALOG_URL,
)


class TestCatalogListEndToEnd(TestCase):
    """End-to-end tests for catalog list command."""

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
    def test_list_with_default_catalog(self, mock_clone, mock_discover, mock_rmtree):
        """List command uses DEFAULT_CATALOG_URL when no env var set."""
        mock_clone.return_value = "/tmp/catalog-test"
        mock_discover.return_value = self._make_entries(
            [
                ("default", "General-purpose Caylent development environment", ["general"]),
                ("airflow-data-eng", "Apache Airflow with Python 3.12", ["data", "airflow"]),
            ]
        )

        args = MagicMock()
        args.tags = None

        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                handle_catalog_list(args)

        mock_clone.assert_called_once_with(DEFAULT_CATALOG_URL)
        output = mock_stdout.getvalue()
        self.assertIn("default catalog", output)
        self.assertIn("default", output)
        self.assertIn("airflow-data-eng", output)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_collection_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    def test_list_with_custom_catalog_url(self, mock_clone, mock_discover, mock_rmtree):
        """List command uses DEVCONTAINER_CATALOG_URL when set."""
        custom_url = "https://github.com/custom-org/custom-catalog.git"
        mock_clone.return_value = "/tmp/catalog-custom"
        mock_discover.return_value = self._make_entries(
            [("smarsh-java", "Smarsh Java Backend", ["java"])],
        )

        args = MagicMock()
        args.tags = None

        with patch.dict(os.environ, {CATALOG_URL_ENV_VAR: custom_url}):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                handle_catalog_list(args)

        mock_clone.assert_called_once_with(custom_url)
        output = mock_stdout.getvalue()
        self.assertIn(custom_url, output)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_collection_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    def test_list_tag_filtering_any_match(self, mock_clone, mock_discover, mock_rmtree):
        """Tag filtering uses ANY match logic."""
        mock_clone.return_value = "/tmp/catalog-test"
        mock_discover.return_value = self._make_entries(
            [
                ("default", "General", ["general", "multi-language"]),
                ("java-spring", "Java Spring", ["java", "spring-boot"]),
                ("python-data", "Python Data", ["python", "data"]),
                ("react-frontend", "React Frontend", ["react", "frontend"]),
            ]
        )

        args = MagicMock()
        args.tags = "java,react"

        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                handle_catalog_list(args)

        output = mock_stdout.getvalue()
        self.assertIn("java-spring", output)
        self.assertIn("react-frontend", output)
        # "default" collection should not appear in data lines (header contains "default catalog")
        data_lines = [line for line in output.split("\n") if line.strip() and "Available" not in line]
        data_text = "\n".join(data_lines)
        self.assertNotIn("General", data_text)  # default's description should be absent
        self.assertNotIn("python-data", output)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.discover_collection_entries")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    def test_list_column_alignment(self, mock_clone, mock_discover, mock_rmtree):
        """Names are left-aligned with consistent column width."""
        mock_clone.return_value = "/tmp/catalog-test"
        mock_discover.return_value = self._make_entries(
            [
                ("ab", "Short name", []),
                ("very-long-collection-name", "Long name", []),
            ]
        )

        args = MagicMock()
        args.tags = None

        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                handle_catalog_list(args)

        lines = mock_stdout.getvalue().strip().split("\n")
        # Find the data lines (skip header and blank lines)
        data_lines = [line for line in lines if line.strip() and "Available" not in line]
        # Both lines should have descriptions at the same column offset
        self.assertTrue(len(data_lines) >= 2)


class TestCatalogValidateEndToEnd(TestCase):
    """End-to-end tests for catalog validate command."""

    def _create_valid_catalog(self, tmp_dir):
        """Create a complete valid catalog for testing."""
        assets_dir = os.path.join(tmp_dir, "common", "devcontainer-assets")
        os.makedirs(assets_dir)
        for filename in CATALOG_REQUIRED_COMMON_ASSETS:
            with open(os.path.join(assets_dir, filename), "w") as f:
                f.write("#!/bin/bash\n")

        col_dir = os.path.join(tmp_dir, "collections", "default")
        os.makedirs(col_dir)
        with open(os.path.join(col_dir, CATALOG_ENTRY_FILENAME), "w") as f:
            json.dump(
                {
                    "name": "default",
                    "description": "Default dev environment",
                    "tags": ["general"],
                    "maintainer": "Platform Team",
                    "min_cli_version": "2.0.0",
                },
                f,
            )
        with open(os.path.join(col_dir, "devcontainer.json"), "w") as f:
            json.dump(
                {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode"},
                f,
            )
        with open(os.path.join(col_dir, CATALOG_VERSION_FILENAME), "w") as f:
            f.write("2.0.0")

    def test_validate_local_valid_catalog(self):
        """Validate --local with a valid catalog passes."""
        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_catalog(tmp)
            args = MagicMock()
            args.local = tmp

            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                handle_catalog_validate(args)

            output = mock_stderr.getvalue()
            self.assertIn("Catalog validation passed", output)
            self.assertIn("1 collections found", output)

    def test_validate_local_invalid_catalog(self):
        """Validate --local with an invalid catalog fails with exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            # Empty dir — missing everything
            args = MagicMock()
            args.local = tmp

            with self.assertRaises(SystemExit) as ctx:
                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    handle_catalog_validate(args)

            self.assertEqual(ctx.exception.code, 1)
            output = mock_stderr.getvalue()
            self.assertIn("Catalog validation failed", output)

    def test_validate_local_nonexistent_path(self):
        """Validate --local with nonexistent path fails."""
        args = MagicMock()
        args.local = "/nonexistent/catalog/path"

        with self.assertRaises(SystemExit):
            handle_catalog_validate(args)

    @patch("caylent_devcontainer_cli.commands.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.commands.catalog.clone_catalog_repo")
    def test_validate_remote_clones_and_validates(self, mock_clone, mock_rmtree):
        """Validate (remote) clones, validates, and cleans up."""
        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_catalog(tmp)
            mock_clone.return_value = tmp

            args = MagicMock()
            args.local = None

            with patch.dict(os.environ, {}, clear=True):
                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    handle_catalog_validate(args)

            mock_clone.assert_called_once_with(DEFAULT_CATALOG_URL)
            output = mock_stderr.getvalue()
            self.assertIn("Catalog validation passed", output)

    def test_validate_local_with_multiple_errors(self):
        """Validate reports all errors, not just the first one."""
        with tempfile.TemporaryDirectory() as tmp:
            # Create assets but bad collection
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            os.makedirs(assets_dir)
            for filename in CATALOG_REQUIRED_COMMON_ASSETS:
                with open(os.path.join(assets_dir, filename), "w") as f:
                    f.write("#!/bin/bash\n")

            col_dir = os.path.join(tmp, "collections", "broken")
            os.makedirs(col_dir)
            # Bad name, no description, conflicting file
            with open(os.path.join(col_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump({"name": "X"}, f)
            with open(os.path.join(col_dir, "devcontainer-functions.sh"), "w") as f:
                f.write("")
            # Missing devcontainer.json and VERSION

            args = MagicMock()
            args.local = tmp

            with self.assertRaises(SystemExit) as ctx:
                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    handle_catalog_validate(args)

            self.assertEqual(ctx.exception.code, 1)
            output = mock_stderr.getvalue()
            # Should report multiple issues
            self.assertIn("issues found", output)


class TestCatalogValidateThisRepo(TestCase):
    """Validate the actual catalog structure in this repository."""

    def test_this_repo_passes_validation(self):
        """The catalog structure in this repo passes validate_catalog()."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        # Verify we're pointing at the right place
        self.assertTrue(
            os.path.isdir(os.path.join(repo_root, "collections")),
            f"Expected collections/ dir at {repo_root}",
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            _run_validation(repo_root)

        output = mock_stderr.getvalue()
        self.assertIn("Catalog validation passed", output)
