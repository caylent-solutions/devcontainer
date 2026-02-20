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
    validate_devcontainer_json,
    validate_entry,
    validate_entry_structure,
    validate_postcreate_command,
    validate_version_file,
)
from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ASSETS_DIR,
    CATALOG_COMMON_DIR,
    CATALOG_COMMON_SUBDIR_REQUIRED_FILES,
    CATALOG_COMMON_SUBDIRS,
    CATALOG_ENTRIES_DIR,
    CATALOG_ENTRY_ALLOWED_FIELDS,
    CATALOG_ENTRY_FILENAME,
    CATALOG_EXECUTABLE_COMMON_ASSETS,
    CATALOG_EXECUTABLE_SUBDIR_ASSETS,
    CATALOG_REQUIRED_COMMON_ASSETS,
    CATALOG_REQUIRED_ENTRY_FILES,
    CATALOG_ROOT_ASSETS_DIR,
    DEFAULT_CATALOG_URL,
    DEVCONTAINER_CONTAINER_SOURCE_FIELDS,
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

    def test_postcreate_injects_devcontainer_functions_via_bash_env(self):
        """Postcreate script must inject devcontainer-functions.sh via BASH_ENV when executing project-setup.sh."""
        filepath = os.path.join(self.assets_dir, ".devcontainer.postcreate.sh")
        with open(filepath) as f:
            content = f.read()
        self.assertIn("BASH_ENV", content)
        self.assertIn("devcontainer-functions.sh", content)

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
        common_assets_dir = os.path.join(self.repo_root, CATALOG_COMMON_DIR, CATALOG_ASSETS_DIR)
        errors = validate_entry(entry_dir, common_assets_dir=common_assets_dir)
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


class TestEnhancedValidationChecks(TestCase):
    """Tests for the 8 enhanced validation checks against the real repo."""

    def setUp(self):
        self.repo_root = _repo_root()
        self.assets_dir = os.path.join(self.repo_root, CATALOG_COMMON_DIR, CATALOG_ASSETS_DIR)
        self.entry_dir = os.path.join(self.repo_root, CATALOG_ENTRIES_DIR, "default")

    def test_validate_version_file_passes(self):
        """validate_version_file() must return no errors for default entry."""
        errors = validate_version_file(self.entry_dir)
        self.assertEqual(errors, [], f"VERSION validation errors: {errors}")

    def test_validate_devcontainer_json_passes(self):
        """validate_devcontainer_json() must return no errors for default entry."""
        devcontainer_path = os.path.join(self.entry_dir, "devcontainer.json")
        errors = validate_devcontainer_json(devcontainer_path)
        self.assertEqual(errors, [], f"devcontainer.json validation errors: {errors}")

    def test_devcontainer_json_has_name_field(self):
        """devcontainer.json must have a 'name' field."""
        devcontainer_path = os.path.join(self.entry_dir, "devcontainer.json")
        with open(devcontainer_path) as f:
            config = json.load(f)
        self.assertIn("name", config)
        self.assertIsInstance(config["name"], str)
        self.assertTrue(len(config["name"]) > 0)

    def test_devcontainer_json_has_container_source(self):
        """devcontainer.json must have at least one container source field."""
        devcontainer_path = os.path.join(self.entry_dir, "devcontainer.json")
        with open(devcontainer_path) as f:
            config = json.load(f)
        has_source = any(field in config for field in DEVCONTAINER_CONTAINER_SOURCE_FIELDS)
        self.assertTrue(
            has_source,
            f"devcontainer.json must have one of {DEVCONTAINER_CONTAINER_SOURCE_FIELDS}",
        )

    def test_entry_directory_name_matches_entry_name(self):
        """Directory name must match catalog-entry.json 'name' field for all entries."""
        entry_paths = discover_entry_paths(self.repo_root)
        for entry_path in entry_paths:
            entry_file = os.path.join(entry_path, CATALOG_ENTRY_FILENAME)
            with open(entry_file) as f:
                data = json.load(f)
            dir_name = os.path.basename(entry_path)
            self.assertEqual(
                dir_name,
                data["name"],
                f"Directory '{dir_name}' does not match entry name '{data['name']}'",
            )

    def test_all_executable_scripts_have_exec_bit(self):
        """All shell scripts in CATALOG_EXECUTABLE_COMMON_ASSETS must be executable."""
        for filename in CATALOG_EXECUTABLE_COMMON_ASSETS:
            filepath = os.path.join(self.assets_dir, filename)
            self.assertTrue(
                os.access(filepath, os.X_OK),
                f"{filename} must be executable",
            )

    def test_all_subdir_executable_scripts_have_exec_bit(self):
        """All shell scripts in common asset subdirectories must be executable."""
        for subdir in CATALOG_COMMON_SUBDIRS:
            for filename in CATALOG_EXECUTABLE_SUBDIR_ASSETS:
                filepath = os.path.join(self.assets_dir, subdir, filename)
                self.assertTrue(
                    os.access(filepath, os.X_OK),
                    f"{subdir}/{filename} must be executable",
                )

    def test_common_subdirectories_have_required_files(self):
        """Each common asset subdirectory must contain its required files."""
        for subdir in CATALOG_COMMON_SUBDIRS:
            subdir_path = os.path.join(self.assets_dir, subdir)
            for req_file in CATALOG_COMMON_SUBDIR_REQUIRED_FILES:
                filepath = os.path.join(subdir_path, req_file)
                self.assertTrue(
                    os.path.isfile(filepath),
                    f"Missing required file: {subdir}/{req_file}",
                )

    def test_root_project_assets_json_files_valid(self):
        """All .json files in root-project-assets must be valid JSON."""
        root_assets_dir = os.path.join(self.repo_root, CATALOG_COMMON_DIR, CATALOG_ROOT_ASSETS_DIR)
        if not os.path.isdir(root_assets_dir):
            return
        for dirpath, _dirnames, filenames in os.walk(root_assets_dir):
            for filename in filenames:
                if filename.endswith(".json"):
                    filepath = os.path.join(dirpath, filename)
                    with open(filepath) as f:
                        try:
                            json.load(f)
                        except json.JSONDecodeError:
                            self.fail(f"Invalid JSON in root-project-assets: {filepath}")

    def test_catalog_entry_no_unknown_fields(self):
        """catalog-entry.json must not contain unknown fields."""
        entry_paths = discover_entry_paths(self.repo_root)
        for entry_path in entry_paths:
            entry_file = os.path.join(entry_path, CATALOG_ENTRY_FILENAME)
            with open(entry_file) as f:
                data = json.load(f)
            unknown = set(data.keys()) - CATALOG_ENTRY_ALLOWED_FIELDS
            self.assertEqual(
                unknown,
                set(),
                f"Unknown fields in {os.path.basename(entry_path)}/{CATALOG_ENTRY_FILENAME}: {unknown}",
            )
