"""Functional tests validating the catalog directory structure.

These tests verify that the repo's catalog structure (common/ and collections/)
is correctly set up and passes all catalog validation from S1.4.1.
"""

import json
import os
from unittest import TestCase

from caylent_devcontainer_cli.utils.catalog import (
    CatalogEntry,
    detect_file_conflicts,
    discover_collections,
    validate_catalog,
    validate_catalog_entry,
    validate_collection,
    validate_collection_structure,
    validate_common_assets,
    validate_postcreate_command,
)
from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ASSETS_DIR,
    CATALOG_COLLECTIONS_DIR,
    CATALOG_COMMON_DIR,
    CATALOG_ENTRY_FILENAME,
    CATALOG_REQUIRED_COLLECTION_FILES,
    CATALOG_REQUIRED_COMMON_ASSETS,
    DEFAULT_CATALOG_URL,
)


def _repo_root():
    """Return the repository root directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestDefaultCatalogUrl(TestCase):
    """Tests for DEFAULT_CATALOG_URL constant."""

    def test_default_catalog_url_is_set(self):
        """DEFAULT_CATALOG_URL must be a non-empty string."""
        self.assertIsInstance(DEFAULT_CATALOG_URL, str)
        self.assertTrue(len(DEFAULT_CATALOG_URL) > 0)

    def test_default_catalog_url_is_git_url(self):
        """DEFAULT_CATALOG_URL must end with .git."""
        self.assertTrue(DEFAULT_CATALOG_URL.endswith(".git"))

    def test_default_catalog_url_is_https(self):
        """DEFAULT_CATALOG_URL must use HTTPS protocol."""
        self.assertTrue(DEFAULT_CATALOG_URL.startswith("https://"))

    def test_default_catalog_url_points_to_this_repo(self):
        """DEFAULT_CATALOG_URL must point to the caylent-solutions/devcontainer repo."""
        self.assertIn("caylent-solutions/devcontainer", DEFAULT_CATALOG_URL)


class TestCommonAssetsDirectory(TestCase):
    """Tests for the common/devcontainer-assets/ directory structure."""

    def setUp(self):
        self.repo_root = _repo_root()
        self.assets_dir = os.path.join(self.repo_root, CATALOG_COMMON_DIR, CATALOG_ASSETS_DIR)

    def test_common_directory_exists(self):
        """common/ directory must exist at repo root."""
        common_dir = os.path.join(self.repo_root, CATALOG_COMMON_DIR)
        self.assertTrue(os.path.isdir(common_dir))

    def test_devcontainer_assets_directory_exists(self):
        """common/devcontainer-assets/ directory must exist."""
        self.assertTrue(os.path.isdir(self.assets_dir))

    def test_all_required_common_assets_present(self):
        """All required common asset files must be present."""
        for filename in CATALOG_REQUIRED_COMMON_ASSETS:
            filepath = os.path.join(self.assets_dir, filename)
            self.assertTrue(
                os.path.isfile(filepath),
                f"Missing required common asset: {filename}",
            )

    def test_postcreate_script_is_executable(self):
        """postcreate script must be executable."""
        filepath = os.path.join(self.assets_dir, ".devcontainer.postcreate.sh")
        self.assertTrue(os.access(filepath, os.X_OK))

    def test_devcontainer_functions_is_executable(self):
        """devcontainer-functions.sh must be executable."""
        filepath = os.path.join(self.assets_dir, "devcontainer-functions.sh")
        self.assertTrue(os.access(filepath, os.X_OK))

    def test_project_setup_is_executable(self):
        """project-setup.sh must be executable."""
        filepath = os.path.join(self.assets_dir, "project-setup.sh")
        self.assertTrue(os.access(filepath, os.X_OK))

    def test_validate_common_assets_passes(self):
        """validate_common_assets() must return no errors for this repo."""
        errors = validate_common_assets(self.repo_root)
        self.assertEqual(errors, [], f"Common assets validation errors: {errors}")

    def test_nix_family_os_directory_exists(self):
        """nix-family-os/ proxy toolkit must exist in common assets."""
        nix_dir = os.path.join(self.assets_dir, "nix-family-os")
        self.assertTrue(os.path.isdir(nix_dir))

    def test_wsl_family_os_directory_exists(self):
        """wsl-family-os/ proxy toolkit must exist in common assets."""
        wsl_dir = os.path.join(self.assets_dir, "wsl-family-os")
        self.assertTrue(os.path.isdir(wsl_dir))

    def test_nix_family_os_has_readme(self):
        """nix-family-os/ must contain README.md."""
        readme = os.path.join(self.assets_dir, "nix-family-os", "README.md")
        self.assertTrue(os.path.isfile(readme))

    def test_wsl_family_os_has_readme(self):
        """wsl-family-os/ must contain README.md."""
        readme = os.path.join(self.assets_dir, "wsl-family-os", "README.md")
        self.assertTrue(os.path.isfile(readme))

    def test_nix_family_os_has_tinyproxy_conf_template(self):
        """nix-family-os/ must contain tinyproxy.conf.template."""
        conf = os.path.join(self.assets_dir, "nix-family-os", "tinyproxy.conf.template")
        self.assertTrue(os.path.isfile(conf))

    def test_nix_family_os_has_tinyproxy_daemon(self):
        """nix-family-os/ must contain tinyproxy-daemon.sh."""
        daemon = os.path.join(self.assets_dir, "nix-family-os", "tinyproxy-daemon.sh")
        self.assertTrue(os.path.isfile(daemon))

    def test_wsl_family_os_has_tinyproxy_conf_template(self):
        """wsl-family-os/ must contain tinyproxy.conf.template."""
        conf = os.path.join(self.assets_dir, "wsl-family-os", "tinyproxy.conf.template")
        self.assertTrue(os.path.isfile(conf))

    def test_wsl_family_os_has_tinyproxy_daemon(self):
        """wsl-family-os/ must contain tinyproxy-daemon.sh."""
        daemon = os.path.join(self.assets_dir, "wsl-family-os", "tinyproxy-daemon.sh")
        self.assertTrue(os.path.isfile(daemon))


class TestDefaultCollectionStructure(TestCase):
    """Tests for the collections/default/ directory structure."""

    def setUp(self):
        self.repo_root = _repo_root()
        self.collection_dir = os.path.join(self.repo_root, CATALOG_COLLECTIONS_DIR, "default")

    def test_collections_directory_exists(self):
        """collections/ directory must exist at repo root."""
        collections_dir = os.path.join(self.repo_root, CATALOG_COLLECTIONS_DIR)
        self.assertTrue(os.path.isdir(collections_dir))

    def test_default_collection_directory_exists(self):
        """collections/default/ directory must exist."""
        self.assertTrue(os.path.isdir(self.collection_dir))

    def test_all_required_collection_files_present(self):
        """All required collection files must be present."""
        for filename in CATALOG_REQUIRED_COLLECTION_FILES:
            filepath = os.path.join(self.collection_dir, filename)
            self.assertTrue(
                os.path.isfile(filepath),
                f"Missing required collection file: {filename}",
            )

    def test_validate_collection_structure_passes(self):
        """validate_collection_structure() must return no errors."""
        errors = validate_collection_structure(self.collection_dir)
        self.assertEqual(errors, [], f"Collection structure validation errors: {errors}")

    def test_fix_line_endings_present(self):
        """fix-line-endings.py must be present in default collection."""
        filepath = os.path.join(self.collection_dir, "fix-line-endings.py")
        self.assertTrue(os.path.isfile(filepath))

    def test_version_file_content(self):
        """VERSION file must contain a valid semver string."""
        filepath = os.path.join(self.collection_dir, "VERSION")
        with open(filepath) as f:
            version = f.read().strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")

    def test_no_file_conflicts_with_common_assets(self):
        """Collection must not contain files that conflict with common assets."""
        conflicts = detect_file_conflicts(self.collection_dir, CATALOG_REQUIRED_COMMON_ASSETS)
        self.assertEqual(conflicts, [], f"File conflicts with common assets: {conflicts}")


class TestDefaultCatalogEntryJson(TestCase):
    """Tests for the collections/default/catalog-entry.json content."""

    def setUp(self):
        self.repo_root = _repo_root()
        self.entry_path = os.path.join(
            self.repo_root,
            CATALOG_COLLECTIONS_DIR,
            "default",
            CATALOG_ENTRY_FILENAME,
        )
        with open(self.entry_path) as f:
            self.entry_data = json.load(f)

    def test_catalog_entry_is_valid_json(self):
        """catalog-entry.json must be valid JSON (parsed in setUp)."""
        self.assertIsInstance(self.entry_data, dict)

    def test_name_is_default(self):
        """Name must be 'default'."""
        self.assertEqual(self.entry_data["name"], "default")

    def test_description_is_non_empty(self):
        """Description must be a non-empty string."""
        self.assertIsInstance(self.entry_data["description"], str)
        self.assertTrue(len(self.entry_data["description"]) > 0)

    def test_tags_are_present(self):
        """Tags must be present and non-empty."""
        self.assertIn("tags", self.entry_data)
        self.assertIsInstance(self.entry_data["tags"], list)
        self.assertTrue(len(self.entry_data["tags"]) > 0)

    def test_tags_include_expected_values(self):
        """Tags must include general, multi-language, aws, kubernetes."""
        expected_tags = {"general", "multi-language", "aws", "kubernetes"}
        actual_tags = set(self.entry_data["tags"])
        self.assertEqual(expected_tags, actual_tags)

    def test_maintainer_is_set(self):
        """Maintainer must be set."""
        self.assertEqual(self.entry_data["maintainer"], "Caylent Platform Team")

    def test_min_cli_version_is_set(self):
        """min_cli_version must be set to 2.0.0."""
        self.assertEqual(self.entry_data["min_cli_version"], "2.0.0")

    def test_validate_catalog_entry_passes(self):
        """validate_catalog_entry() must return no errors."""
        errors = validate_catalog_entry(self.entry_data)
        self.assertEqual(errors, [], f"Catalog entry validation errors: {errors}")

    def test_catalog_entry_from_dict(self):
        """CatalogEntry.from_dict() must parse the entry correctly."""
        entry = CatalogEntry.from_dict(self.entry_data)
        self.assertEqual(entry.name, "default")
        self.assertEqual(entry.maintainer, "Caylent Platform Team")
        self.assertEqual(entry.min_cli_version, "2.0.0")


class TestProjectSetupShLifecycle(TestCase):
    """Tests for the project-setup.sh lifecycle (S1.5.3).

    Validates that:
    - The template has correct bash structure (header, strict mode, sources functions)
    - The postcreate script integrates project-setup.sh (sources if exists)
    - The replacement notification covers customization merge guidance
    """

    def setUp(self):
        self.repo_root = _repo_root()
        self.assets_dir = os.path.join(self.repo_root, CATALOG_COMMON_DIR, CATALOG_ASSETS_DIR)

    def test_project_setup_has_bash_shebang(self):
        """project-setup.sh must start with a bash shebang."""
        filepath = os.path.join(self.assets_dir, "project-setup.sh")
        with open(filepath) as f:
            first_line = f.readline().strip()
        self.assertEqual(first_line, "#!/usr/bin/env bash")

    def test_project_setup_has_strict_mode(self):
        """project-setup.sh must use set -euo pipefail."""
        filepath = os.path.join(self.assets_dir, "project-setup.sh")
        with open(filepath) as f:
            content = f.read()
        self.assertIn("set -euo pipefail", content)

    def test_project_setup_sources_devcontainer_functions(self):
        """project-setup.sh must source devcontainer-functions.sh."""
        filepath = os.path.join(self.assets_dir, "project-setup.sh")
        with open(filepath) as f:
            content = f.read()
        self.assertIn("devcontainer-functions.sh", content)
        self.assertIn("source", content)

    def test_postcreate_checks_project_setup_exists(self):
        """Postcreate script must check if project-setup.sh exists before running."""
        filepath = os.path.join(self.assets_dir, ".devcontainer.postcreate.sh")
        with open(filepath) as f:
            content = f.read()
        self.assertIn("project-setup.sh", content)
        self.assertIn("-f", content)

    def test_postcreate_executes_project_setup(self):
        """Postcreate script must execute project-setup.sh via bash."""
        filepath = os.path.join(self.assets_dir, ".devcontainer.postcreate.sh")
        with open(filepath) as f:
            content = f.read()
        self.assertIn("bash", content)
        self.assertIn("project-setup.sh", content)

    def test_postcreate_warns_if_project_setup_missing(self):
        """Postcreate script must warn if project-setup.sh is missing."""
        filepath = os.path.join(self.assets_dir, ".devcontainer.postcreate.sh")
        with open(filepath) as f:
            content = f.read()
        # The else branch must log a warning about missing project-setup.sh
        self.assertIn("log_warn", content)
        self.assertIn("No project-specific setup script found", content)


class TestDefaultCollectionDevcontainerJson(TestCase):
    """Tests for collections/default/devcontainer.json."""

    def setUp(self):
        self.repo_root = _repo_root()
        self.devcontainer_path = os.path.join(
            self.repo_root,
            CATALOG_COLLECTIONS_DIR,
            "default",
            "devcontainer.json",
        )
        with open(self.devcontainer_path) as f:
            self.config = json.load(f)

    def test_devcontainer_json_is_valid_json(self):
        """devcontainer.json must be valid JSON."""
        self.assertIsInstance(self.config, dict)

    def test_postcreate_command_calls_postcreate_script(self):
        """postCreateCommand must call .devcontainer.postcreate.sh."""
        post_create = self.config.get("postCreateCommand", "")
        self.assertIn(".devcontainer.postcreate.sh", str(post_create))

    def test_validate_postcreate_command_passes(self):
        """validate_postcreate_command() must return no errors."""
        errors = validate_postcreate_command(self.devcontainer_path)
        self.assertEqual(errors, [], f"postCreateCommand validation errors: {errors}")

    def test_postcreate_sources_shell_env(self):
        """postCreateCommand must source shell.env."""
        post_create = str(self.config.get("postCreateCommand", ""))
        self.assertIn("source shell.env", post_create)

    def test_uses_sudo_e(self):
        """postCreateCommand must use sudo -E for environment propagation."""
        post_create = str(self.config.get("postCreateCommand", ""))
        self.assertIn("sudo -E", post_create)


class TestFullCatalogValidation(TestCase):
    """Tests that the entire catalog structure passes validate_catalog()."""

    def setUp(self):
        self.repo_root = _repo_root()

    def test_validate_catalog_passes(self):
        """validate_catalog() must return no errors for this repo."""
        errors = validate_catalog(self.repo_root)
        self.assertEqual(errors, [], f"Full catalog validation errors: {errors}")

    def test_discover_collections_finds_default(self):
        """discover_collections() must find the default collection."""
        collections = discover_collections(self.repo_root)
        self.assertTrue(len(collections) >= 1)
        default_found = any(os.path.basename(c) == "default" for c in collections)
        self.assertTrue(
            default_found,
            f"Default collection not found. Collections: {collections}",
        )

    def test_validate_collection_passes_for_default(self):
        """validate_collection() must return no errors for collections/default/."""
        collection_dir = os.path.join(self.repo_root, CATALOG_COLLECTIONS_DIR, "default")
        errors = validate_collection(collection_dir)
        self.assertEqual(errors, [], f"Default collection validation errors: {errors}")


class TestDevcontainerDirectoryUntouched(TestCase):
    """Tests that .devcontainer/ has NOT been modified by catalog structure creation."""

    def setUp(self):
        self.repo_root = _repo_root()
        self.devcontainer_dir = os.path.join(self.repo_root, ".devcontainer")

    def test_devcontainer_directory_exists(self):
        """.devcontainer/ must still exist."""
        self.assertTrue(os.path.isdir(self.devcontainer_dir))

    def test_devcontainer_is_not_inside_catalog(self):
        """.devcontainer/ must NOT be inside common/ or collections/."""
        common_dir = os.path.join(self.repo_root, CATALOG_COMMON_DIR)
        collections_dir = os.path.join(self.repo_root, CATALOG_COLLECTIONS_DIR)
        self.assertFalse(self.devcontainer_dir.startswith(common_dir))
        self.assertFalse(self.devcontainer_dir.startswith(collections_dir))

    def test_devcontainer_has_own_postcreate(self):
        """.devcontainer/ must still have its own postcreate script."""
        filepath = os.path.join(self.devcontainer_dir, ".devcontainer.postcreate.sh")
        self.assertTrue(os.path.isfile(filepath))

    def test_devcontainer_has_own_functions(self):
        """.devcontainer/ must still have its own devcontainer-functions.sh."""
        filepath = os.path.join(self.devcontainer_dir, "devcontainer-functions.sh")
        self.assertTrue(os.path.isfile(filepath))

    def test_devcontainer_has_own_devcontainer_json(self):
        """.devcontainer/ must still have its own devcontainer.json."""
        filepath = os.path.join(self.devcontainer_dir, "devcontainer.json")
        self.assertTrue(os.path.isfile(filepath))

    def test_no_catalog_entry_in_devcontainer(self):
        """.devcontainer/ must NOT contain a catalog-entry.json."""
        filepath = os.path.join(self.devcontainer_dir, CATALOG_ENTRY_FILENAME)
        self.assertFalse(os.path.isfile(filepath))
