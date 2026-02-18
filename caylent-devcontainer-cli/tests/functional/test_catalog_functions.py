"""Functional tests for catalog shared functions end-to-end behavior."""

import json
import os
import tempfile
from unittest import TestCase
from unittest.mock import patch

from caylent_devcontainer_cli.utils.catalog import (
    clone_catalog_repo,
    copy_entry_to_project,
    copy_root_assets_to_project,
    discover_entries,
    parse_catalog_url,
    validate_catalog,
)
from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ENTRY_FILENAME,
    CATALOG_REQUIRED_COMMON_ASSETS,
    CATALOG_VERSION_FILENAME,
)


class TestUrlParsingEndToEnd(TestCase):
    """Functional tests for URL parsing across all documented formats."""

    def test_https_url_roundtrip_no_ref(self):
        url, ref = parse_catalog_url("https://github.com/caylent-solutions/devcontainer.git")
        self.assertEqual(url, "https://github.com/caylent-solutions/devcontainer.git")
        self.assertIsNone(ref)

    def test_https_url_roundtrip_with_tag(self):
        url, ref = parse_catalog_url("https://github.com/caylent-solutions/devcontainer.git@v2.0.0")
        self.assertEqual(url, "https://github.com/caylent-solutions/devcontainer.git")
        self.assertEqual(ref, "v2.0.0")

    def test_ssh_url_roundtrip_no_ref(self):
        url, ref = parse_catalog_url("git@github.com:caylent-solutions/devcontainer.git")
        self.assertEqual(url, "git@github.com:caylent-solutions/devcontainer.git")
        self.assertIsNone(ref)

    def test_ssh_url_roundtrip_with_branch(self):
        url, ref = parse_catalog_url("git@github.com:caylent-solutions/devcontainer.git@feature/catalog")
        self.assertEqual(url, "git@github.com:caylent-solutions/devcontainer.git")
        self.assertEqual(ref, "feature/catalog")

    def test_empty_url_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_catalog_url("")


class TestCloneCatalogRepoEndToEnd(TestCase):
    """Functional tests for clone_catalog_repo with mocked git."""

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    @patch("caylent_devcontainer_cli.utils.catalog.tempfile.mkdtemp")
    def test_full_clone_flow_success(self, mock_mkdtemp, mock_run):
        mock_mkdtemp.return_value = "/tmp/catalog-test"
        mock_run.return_value = type("Result", (), {"returncode": 0, "stderr": ""})()

        result = clone_catalog_repo("https://github.com/org/repo.git@v2.0")
        self.assertEqual(result, "/tmp/catalog-test")

        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], "git")
        self.assertEqual(cmd[1], "clone")
        self.assertIn("--depth", cmd)
        self.assertIn("--branch", cmd)
        self.assertIn("v2.0", cmd)

    @patch("caylent_devcontainer_cli.utils.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    @patch("caylent_devcontainer_cli.utils.catalog.tempfile.mkdtemp")
    def test_full_clone_flow_failure_error_message(self, mock_mkdtemp, mock_run, mock_rmtree):
        mock_mkdtemp.return_value = "/tmp/catalog-fail"
        mock_run.return_value = type("Result", (), {"returncode": 128, "stderr": "fatal: Authentication failed"})()

        with self.assertRaises(SystemExit) as ctx:
            clone_catalog_repo("https://github.com/org/private-repo.git")

        msg = str(ctx.exception)
        # Verify all required error message components
        self.assertIn("Failed to clone", msg)
        self.assertIn("https://github.com/org/private-repo.git", msg)
        self.assertIn("HTTPS repos", msg)
        self.assertIn("SSH repos", msg)
        self.assertIn("git ls-remote", msg)
        self.assertIn("Authentication failed", msg)
        # Verify temp dir was cleaned up
        mock_rmtree.assert_called_once()


class TestDiscoverEntriesEndToEnd(TestCase):
    """Functional tests for entry discovery and sorting."""

    def _create_catalog(self, tmp_dir, entries):
        """Create a catalog with given entries.

        Args:
            tmp_dir: Root directory for the catalog.
            entries: Dict mapping entry names to entry dicts.
        """
        # Create common assets
        assets_dir = os.path.join(tmp_dir, "common", "devcontainer-assets")
        os.makedirs(assets_dir)
        for filename in CATALOG_REQUIRED_COMMON_ASSETS:
            with open(os.path.join(assets_dir, filename), "w") as f:
                f.write("#!/bin/bash\n")

        # Create entries
        for name, entry_data in entries.items():
            col_dir = os.path.join(tmp_dir, "catalog", name)
            os.makedirs(col_dir)
            with open(os.path.join(col_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(entry_data, f)

    def test_discovers_multiple_entries_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._create_catalog(
                tmp,
                {
                    "zebra": {"name": "zebra", "description": "Zebra entry"},
                    "default": {"name": "default", "description": "Default entry"},
                    "alpha": {"name": "alpha", "description": "Alpha entry"},
                },
            )
            entries = discover_entries(tmp)
            names = [e.entry.name for e in entries]
            self.assertEqual(names, ["default", "alpha", "zebra"])

    def test_preserves_full_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._create_catalog(
                tmp,
                {
                    "my-app": {
                        "name": "my-app",
                        "description": "Full metadata test",
                        "tags": ["python", "aws"],
                        "maintainer": "platform-team",
                        "min_cli_version": "2.0.0",
                    },
                },
            )
            entries = discover_entries(tmp)
            self.assertEqual(len(entries), 1)
            entry = entries[0].entry
            self.assertEqual(entry.name, "my-app")
            self.assertEqual(entry.description, "Full metadata test")
            self.assertEqual(entry.tags, ["python", "aws"])
            self.assertEqual(entry.maintainer, "platform-team")
            self.assertEqual(entry.min_cli_version, "2.0.0")

    def test_skips_entries_with_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._create_catalog(tmp, {"valid": {"name": "valid", "description": "Valid"}})
            # Add a broken entry
            broken_dir = os.path.join(tmp, "catalog", "broken")
            os.makedirs(broken_dir)
            with open(os.path.join(broken_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                f.write("{broken json")

            entries = discover_entries(tmp)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].entry.name, "valid")


class TestCopyEntryToProjectEndToEnd(TestCase):
    """Functional tests for copy_entry_to_project full flow."""

    def _create_full_entry(self, tmp_dir):
        """Create a complete entry and common assets setup."""
        entry_src = os.path.join(tmp_dir, "collection")
        assets = os.path.join(tmp_dir, "assets")
        target = os.path.join(tmp_dir, "project", ".devcontainer")
        os.makedirs(entry_src)
        os.makedirs(assets)

        # Entry files
        entry = {
            "name": "test-app",
            "description": "Test application",
            "tags": ["python", "aws"],
            "maintainer": "team",
        }
        with open(os.path.join(entry_src, CATALOG_ENTRY_FILENAME), "w") as f:
            json.dump(entry, f)
        devcontainer = {
            "name": "test",
            "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
        }
        with open(os.path.join(entry_src, "devcontainer.json"), "w") as f:
            json.dump(devcontainer, f)
        with open(os.path.join(entry_src, CATALOG_VERSION_FILENAME), "w") as f:
            f.write("2.0.0")

        # Subdirectory in entry
        nix_dir = os.path.join(entry_src, "nix-family-os")
        os.makedirs(nix_dir)
        with open(os.path.join(nix_dir, "tinyproxy.conf"), "w") as f:
            f.write("# proxy config\n")

        # Common assets
        with open(os.path.join(assets, ".devcontainer.postcreate.sh"), "w") as f:
            f.write("#!/bin/bash\necho postcreate\n")
        with open(os.path.join(assets, "devcontainer-functions.sh"), "w") as f:
            f.write("#!/bin/bash\necho functions\n")
        with open(os.path.join(assets, "project-setup.sh"), "w") as f:
            f.write("#!/bin/bash\necho project-setup\n")

        return entry_src, assets, target

    def test_full_copy_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, target = self._create_full_entry(tmp)
            catalog_url = "https://github.com/org/repo.git@v2.0"

            copy_entry_to_project(entry_src, assets, target, catalog_url)

            # Verify entry files copied
            self.assertTrue(os.path.isfile(os.path.join(target, "devcontainer.json")))
            self.assertTrue(os.path.isfile(os.path.join(target, CATALOG_VERSION_FILENAME)))

            # Verify common assets copied
            self.assertTrue(os.path.isfile(os.path.join(target, ".devcontainer.postcreate.sh")))
            self.assertTrue(os.path.isfile(os.path.join(target, "devcontainer-functions.sh")))
            self.assertTrue(os.path.isfile(os.path.join(target, "project-setup.sh")))

            # Verify subdirectory copied
            self.assertTrue(os.path.isdir(os.path.join(target, "nix-family-os")))
            self.assertTrue(os.path.isfile(os.path.join(target, "nix-family-os", "tinyproxy.conf")))

            # Verify catalog_url augmented
            with open(os.path.join(target, CATALOG_ENTRY_FILENAME)) as f:
                entry_data = json.load(f)
            self.assertEqual(entry_data["catalog_url"], catalog_url)
            self.assertEqual(entry_data["name"], "test-app")
            self.assertEqual(entry_data["tags"], ["python", "aws"])

    def test_common_assets_take_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, target = self._create_full_entry(tmp)

            # Create conflicting file in entry
            with open(os.path.join(entry_src, "project-setup.sh"), "w") as f:
                f.write("entry version\n")

            copy_entry_to_project(entry_src, assets, target, "https://example.com/repo.git")

            # Common assets version should win
            with open(os.path.join(target, "project-setup.sh")) as f:
                content = f.read()
            self.assertEqual(content, "#!/bin/bash\necho project-setup\n")

    def test_catalog_entry_json_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, target = self._create_full_entry(tmp)
            copy_entry_to_project(entry_src, assets, target, "https://example.com/repo.git")

            with open(os.path.join(target, CATALOG_ENTRY_FILENAME)) as f:
                raw = f.read()

            # Should be indented JSON with trailing newline
            self.assertTrue(raw.endswith("\n"))
            data = json.loads(raw)
            self.assertIn("catalog_url", data)
            self.assertIn("name", data)


class TestProjectSetupOverwriteOnReSetup(TestCase):
    """Functional tests verifying project-setup.sh is overwritten on re-setup."""

    def _create_full_entry(self, tmp_dir):
        """Create a complete entry and common assets setup."""
        entry_src = os.path.join(tmp_dir, "collection")
        assets = os.path.join(tmp_dir, "assets")
        target = os.path.join(tmp_dir, "project", ".devcontainer")
        os.makedirs(entry_src)
        os.makedirs(assets)

        # Entry files
        entry = {
            "name": "test-app",
            "description": "Test application",
        }
        with open(os.path.join(entry_src, CATALOG_ENTRY_FILENAME), "w") as f:
            json.dump(entry, f)
        with open(os.path.join(entry_src, "devcontainer.json"), "w") as f:
            json.dump(
                {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode"},
                f,
            )
        with open(os.path.join(entry_src, CATALOG_VERSION_FILENAME), "w") as f:
            f.write("2.0.0")

        # Common assets
        with open(os.path.join(assets, ".devcontainer.postcreate.sh"), "w") as f:
            f.write("#!/bin/bash\necho postcreate\n")
        with open(os.path.join(assets, "devcontainer-functions.sh"), "w") as f:
            f.write("#!/bin/bash\necho functions\n")
        with open(os.path.join(assets, "project-setup.sh"), "w") as f:
            f.write("#!/bin/bash\necho original-project-setup\n")

        return entry_src, assets, target

    def test_project_setup_overwritten_on_second_copy(self):
        """project-setup.sh must be overwritten when copy_entry_to_project runs again."""
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, target = self._create_full_entry(tmp)
            catalog_url = "https://github.com/org/repo.git"

            # First copy
            copy_entry_to_project(entry_src, assets, target, catalog_url)

            # Simulate developer customization
            setup_path = os.path.join(target, "project-setup.sh")
            with open(setup_path, "w") as f:
                f.write("#!/bin/bash\necho customized-by-developer\n")

            # Verify customization is in place
            with open(setup_path) as f:
                content = f.read()
            self.assertIn("customized-by-developer", content)

            # Second copy (re-setup) — must overwrite the customization
            copy_entry_to_project(entry_src, assets, target, catalog_url)

            with open(setup_path) as f:
                content = f.read()
            self.assertIn("original-project-setup", content)
            self.assertNotIn("customized-by-developer", content)


class TestValidateCatalogEndToEnd(TestCase):
    """Functional test for validate_catalog on a realistic catalog structure."""

    def test_validate_real_catalog_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Build a complete, valid catalog
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            os.makedirs(assets_dir)
            for filename in CATALOG_REQUIRED_COMMON_ASSETS:
                with open(os.path.join(assets_dir, filename), "w") as f:
                    f.write("#!/bin/bash\n")

            # Default entry
            default_dir = os.path.join(tmp, "catalog", "default")
            os.makedirs(default_dir)
            with open(os.path.join(default_dir, CATALOG_ENTRY_FILENAME), "w") as f:
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
            with open(os.path.join(default_dir, "devcontainer.json"), "w") as f:
                json.dump(
                    {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode"},
                    f,
                )
            with open(os.path.join(default_dir, CATALOG_VERSION_FILENAME), "w") as f:
                f.write("2.0.0")

            # Second entry
            java_dir = os.path.join(tmp, "catalog", "java-spring")
            os.makedirs(java_dir)
            with open(os.path.join(java_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(
                    {
                        "name": "java-spring",
                        "description": "Java Spring Boot environment",
                        "tags": ["java", "spring-boot"],
                    },
                    f,
                )
            with open(os.path.join(java_dir, "devcontainer.json"), "w") as f:
                json.dump(
                    {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode"},
                    f,
                )
            with open(os.path.join(java_dir, CATALOG_VERSION_FILENAME), "w") as f:
                f.write("1.0.0")

            errors = validate_catalog(tmp)
            self.assertEqual(errors, [], f"Expected no errors, got: {errors}")

    def test_validate_detects_duplicate_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            os.makedirs(assets_dir)
            for filename in CATALOG_REQUIRED_COMMON_ASSETS:
                with open(os.path.join(assets_dir, filename), "w") as f:
                    f.write("#!/bin/bash\n")

            # Two entries with same name
            for dirname in ["col-a", "col-b"]:
                col_dir = os.path.join(tmp, "catalog", dirname)
                os.makedirs(col_dir)
                with open(os.path.join(col_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                    json.dump({"name": "duplicate-name", "description": "Duplicate"}, f)
                with open(os.path.join(col_dir, "devcontainer.json"), "w") as f:
                    json.dump(
                        {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh"},
                        f,
                    )
                with open(os.path.join(col_dir, CATALOG_VERSION_FILENAME), "w") as f:
                    f.write("1.0.0")

            errors = validate_catalog(tmp)
            self.assertTrue(any("Duplicate entry name" in e for e in errors))


class TestCopyEntryAndRootAssetsEndToEnd(TestCase):
    """End-to-end test: copy_entry_to_project + copy_root_assets_to_project together."""

    def _create_catalog(self, tmp_dir):
        """Create a realistic catalog with entry, common assets, and root assets."""
        # Common devcontainer assets
        assets_dir = os.path.join(tmp_dir, "common", "devcontainer-assets")
        os.makedirs(assets_dir)
        for filename in CATALOG_REQUIRED_COMMON_ASSETS:
            with open(os.path.join(assets_dir, filename), "w") as f:
                f.write("#!/bin/bash\necho test")

        # Root project assets
        root_assets_dir = os.path.join(tmp_dir, "common", "root-project-assets")
        os.makedirs(os.path.join(root_assets_dir, ".claude"))
        with open(os.path.join(root_assets_dir, "CLAUDE.md"), "w") as f:
            f.write("# Engineering Standards")
        with open(os.path.join(root_assets_dir, ".claude", "settings.json"), "w") as f:
            json.dump({"permissions": {"allow": ["Read"]}}, f)

        # Catalog entry
        entry_dir = os.path.join(tmp_dir, "catalog", "default")
        os.makedirs(entry_dir)
        with open(os.path.join(entry_dir, CATALOG_ENTRY_FILENAME), "w") as f:
            json.dump({"name": "default", "description": "Default entry"}, f)
        with open(os.path.join(entry_dir, "devcontainer.json"), "w") as f:
            json.dump(
                {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh"},
                f,
            )
        with open(os.path.join(entry_dir, CATALOG_VERSION_FILENAME), "w") as f:
            f.write("1.0.0")

        return entry_dir, assets_dir, root_assets_dir

    def test_produces_correct_project_layout(self):
        """Both .devcontainer/ and root assets are correctly placed."""
        with tempfile.TemporaryDirectory() as tmp:
            entry_dir, assets_dir, root_assets_dir = self._create_catalog(tmp)

            project = os.path.join(tmp, "my-project")
            devcontainer_target = os.path.join(project, ".devcontainer")
            os.makedirs(project)

            copy_entry_to_project(entry_dir, assets_dir, devcontainer_target, "https://example.com/repo.git")
            copy_root_assets_to_project(root_assets_dir, project)

            # .devcontainer/ files
            self.assertTrue(os.path.isfile(os.path.join(devcontainer_target, "devcontainer.json")))
            self.assertTrue(os.path.isfile(os.path.join(devcontainer_target, CATALOG_ENTRY_FILENAME)))
            for asset in CATALOG_REQUIRED_COMMON_ASSETS:
                self.assertTrue(
                    os.path.isfile(os.path.join(devcontainer_target, asset)),
                    f"Missing common asset: {asset}",
                )

            # Root project assets
            self.assertTrue(os.path.isfile(os.path.join(project, "CLAUDE.md")))
            self.assertTrue(os.path.isfile(os.path.join(project, ".claude", "settings.json")))

            # Verify content
            with open(os.path.join(project, "CLAUDE.md")) as f:
                self.assertEqual(f.read(), "# Engineering Standards")
            with open(os.path.join(project, ".claude", "settings.json")) as f:
                data = json.load(f)
            self.assertEqual(data["permissions"]["allow"], ["Read"])
