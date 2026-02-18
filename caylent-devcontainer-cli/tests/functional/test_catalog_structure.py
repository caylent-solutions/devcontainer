"""Functional tests validating the catalog directory structure.

These tests verify that the repo's catalog structure (common/ and catalog/)
is correctly set up and passes all catalog validation from S1.4.1.
"""

import json
import os
from unittest import TestCase

from caylent_devcontainer_cli.utils.catalog import (
    CatalogEntry,
    detect_file_conflicts,
    discover_entry_paths,
    validate_catalog,
    validate_catalog_entry,
    validate_common_assets,
    validate_entry,
    validate_entry_structure,
    validate_postcreate_command,
)
from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ASSETS_DIR,
    CATALOG_COMMON_DIR,
    CATALOG_ENTRIES_DIR,
    CATALOG_ENTRY_FILENAME,
    CATALOG_REQUIRED_COMMON_ASSETS,
    CATALOG_REQUIRED_ENTRY_FILES,
    CATALOG_ROOT_ASSETS_DIR,
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


class TestDefaultEntryStructure(TestCase):
    """Tests for the catalog/default/ directory structure."""

    def setUp(self):
        self.repo_root = _repo_root()
        self.entry_dir = os.path.join(self.repo_root, CATALOG_ENTRIES_DIR, "default")

    def test_entries_directory_exists(self):
        """catalog/ directory must exist at repo root."""
        entries_dir = os.path.join(self.repo_root, CATALOG_ENTRIES_DIR)
        self.assertTrue(os.path.isdir(entries_dir))

    def test_default_entry_directory_exists(self):
        """catalog/default/ directory must exist."""
        self.assertTrue(os.path.isdir(self.entry_dir))

    def test_all_required_entry_files_present(self):
        """All required entry files must be present."""
        for filename in CATALOG_REQUIRED_ENTRY_FILES:
            filepath = os.path.join(self.entry_dir, filename)
            self.assertTrue(
                os.path.isfile(filepath),
                f"Missing required entry file: {filename}",
            )

    def test_validate_entry_structure_passes(self):
        """validate_entry_structure() must return no errors."""
        errors = validate_entry_structure(self.entry_dir)
        self.assertEqual(errors, [], f"Entry structure validation errors: {errors}")

    def test_fix_line_endings_present(self):
        """fix-line-endings.py must be present in default entry."""
        filepath = os.path.join(self.entry_dir, "fix-line-endings.py")
        self.assertTrue(os.path.isfile(filepath))

    def test_version_file_content(self):
        """VERSION file must contain a valid semver string."""
        filepath = os.path.join(self.entry_dir, "VERSION")
        with open(filepath) as f:
            version = f.read().strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")

    def test_no_file_conflicts_with_common_assets(self):
        """Entry must not contain files that conflict with common assets."""
        conflicts = detect_file_conflicts(self.entry_dir, CATALOG_REQUIRED_COMMON_ASSETS)
        self.assertEqual(conflicts, [], f"File conflicts with common assets: {conflicts}")


class TestDefaultCatalogEntryJson(TestCase):
    """Tests for the catalog/default/catalog-entry.json content."""

    def setUp(self):
        self.repo_root = _repo_root()
        self.entry_path = os.path.join(
            self.repo_root,
            CATALOG_ENTRIES_DIR,
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


class TestDefaultEntryDevcontainerJson(TestCase):
    """Tests for catalog/default/devcontainer.json."""

    def setUp(self):
        self.repo_root = _repo_root()
        self.devcontainer_path = os.path.join(
            self.repo_root,
            CATALOG_ENTRIES_DIR,
            "default",
            "devcontainer.json",
        )
        with open(self.devcontainer_path) as f:
            self.config = json.load(f)

    def test_devcontainer_json_is_valid_json(self):
        """devcontainer.json must be valid JSON."""
        self.assertIsInstance(self.config, dict)

    def test_postcreate_command_calls_postcreate_wrapper(self):
        """postCreateCommand must call postcreate-wrapper.sh."""
        post_create = self.config.get("postCreateCommand", "")
        self.assertIn("postcreate-wrapper.sh", str(post_create))

    def test_validate_postcreate_command_passes(self):
        """validate_postcreate_command() must return no errors."""
        errors = validate_postcreate_command(self.devcontainer_path)
        self.assertEqual(errors, [], f"postCreateCommand validation errors: {errors}")

    def test_postcreate_wrapper_sources_shell_env(self):
        """postcreate-wrapper.sh (called by postCreateCommand) must source shell.env."""
        assets_dir = os.path.join(self.repo_root, CATALOG_COMMON_DIR, CATALOG_ASSETS_DIR)
        wrapper_path = os.path.join(assets_dir, "postcreate-wrapper.sh")
        with open(wrapper_path) as f:
            wrapper = f.read()
        self.assertIn("source shell.env", wrapper)

    def test_postcreate_wrapper_uses_sudo_e(self):
        """postcreate-wrapper.sh must use sudo -E for environment propagation."""
        assets_dir = os.path.join(self.repo_root, CATALOG_COMMON_DIR, CATALOG_ASSETS_DIR)
        wrapper_path = os.path.join(assets_dir, "postcreate-wrapper.sh")
        with open(wrapper_path) as f:
            wrapper = f.read()
        self.assertIn("sudo -E", wrapper)


class TestFullCatalogValidation(TestCase):
    """Tests that the entire catalog structure passes validate_catalog()."""

    def setUp(self):
        self.repo_root = _repo_root()

    def test_validate_catalog_passes(self):
        """validate_catalog() must return no errors for this repo."""
        errors = validate_catalog(self.repo_root)
        self.assertEqual(errors, [], f"Full catalog validation errors: {errors}")

    def test_discover_entry_paths_finds_default(self):
        """discover_entry_paths() must find the default entry."""
        entry_paths = discover_entry_paths(self.repo_root)
        self.assertTrue(len(entry_paths) >= 1)
        default_found = any(os.path.basename(c) == "default" for c in entry_paths)
        self.assertTrue(
            default_found,
            f"Default entry not found. Entries: {entry_paths}",
        )

    def test_validate_entry_passes_for_default(self):
        """validate_entry() must return no errors for catalog/default/."""
        entry_dir = os.path.join(self.repo_root, CATALOG_ENTRIES_DIR, "default")
        errors = validate_entry(entry_dir)
        self.assertEqual(errors, [], f"Default entry validation errors: {errors}")


class TestDeployedDevcontainerDirectory(TestCase):
    """Tests that .devcontainer/ is a complete deployed instance from catalog/default/."""

    def setUp(self):
        self.repo_root = _repo_root()
        self.devcontainer_dir = os.path.join(self.repo_root, ".devcontainer")
        self.default_entry_dir = os.path.join(self.repo_root, CATALOG_ENTRIES_DIR, "default")
        self.common_assets_dir = os.path.join(self.repo_root, CATALOG_COMMON_DIR, CATALOG_ASSETS_DIR)

    def test_devcontainer_directory_exists(self):
        """.devcontainer/ must exist as a deployed catalog instance."""
        self.assertTrue(os.path.isdir(self.devcontainer_dir))

    def test_contains_entry_files(self):
        """.devcontainer/ must contain all files from catalog/default/."""
        for item in os.listdir(self.default_entry_dir):
            deployed = os.path.join(self.devcontainer_dir, item)
            self.assertTrue(
                os.path.exists(deployed),
                f"catalog/default/{item} not found in .devcontainer/",
            )

    def test_contains_common_asset_files(self):
        """.devcontainer/ must contain all files from common/devcontainer-assets/."""
        for item in os.listdir(self.common_assets_dir):
            deployed = os.path.join(self.devcontainer_dir, item)
            self.assertTrue(
                os.path.exists(deployed),
                f"common/devcontainer-assets/{item} not found in .devcontainer/",
            )


class TestCommonRootAssetsDirectory(TestCase):
    """Tests for the common/root-project-assets/ directory structure."""

    def setUp(self):
        self.repo_root = _repo_root()
        self.root_assets_dir = os.path.join(self.repo_root, CATALOG_COMMON_DIR, CATALOG_ROOT_ASSETS_DIR)

    def test_root_assets_directory_exists(self):
        """common/root-project-assets/ directory must exist."""
        self.assertTrue(os.path.isdir(self.root_assets_dir))

    def test_root_assets_contains_claude_md(self):
        """CLAUDE.md must be present in root-project-assets."""
        filepath = os.path.join(self.root_assets_dir, "CLAUDE.md")
        self.assertTrue(os.path.isfile(filepath))

    def test_root_assets_contains_claude_settings_dir(self):
        """.claude/ directory must be present in root-project-assets."""
        dirpath = os.path.join(self.root_assets_dir, ".claude")
        self.assertTrue(os.path.isdir(dirpath))

    def test_root_assets_claude_settings_json_valid(self):
        """.claude/settings.json must be valid JSON."""
        filepath = os.path.join(self.root_assets_dir, ".claude", "settings.json")
        self.assertTrue(os.path.isfile(filepath))
        with open(filepath) as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

    def test_root_assets_claude_settings_local_json_valid(self):
        """.claude/settings.local.json must be valid JSON."""
        filepath = os.path.join(self.root_assets_dir, ".claude", "settings.local.json")
        self.assertTrue(os.path.isfile(filepath))
        with open(filepath) as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

    def test_root_assets_claude_md_matches_repo_root(self):
        """CLAUDE.md in root-project-assets must match repo root CLAUDE.md."""
        root_claude = os.path.join(self.repo_root, "CLAUDE.md")
        assets_claude = os.path.join(self.root_assets_dir, "CLAUDE.md")
        with open(root_claude) as f:
            root_content = f.read()
        with open(assets_claude) as f:
            assets_content = f.read()
        self.assertEqual(root_content, assets_content)
