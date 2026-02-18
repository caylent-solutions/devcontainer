"""Unit tests for catalog data model and validation."""

import json
import os
import tempfile
from unittest import TestCase
from unittest.mock import patch

from caylent_devcontainer_cli.utils.catalog import (
    CatalogEntry,
    EntryInfo,
    clone_catalog_repo,
    copy_entry_to_project,
    copy_root_assets_to_project,
    detect_file_conflicts,
    discover_entries,
    discover_entry_paths,
    parse_catalog_url,
    resolve_default_catalog_url,
    resolve_latest_catalog_tag,
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
    CATALOG_COMMON_SUBDIR_REQUIRED_FILES,
    CATALOG_COMMON_SUBDIRS,
    CATALOG_ENTRY_ALLOWED_FIELDS,
    CATALOG_ENTRY_FILENAME,
    CATALOG_EXECUTABLE_SUBDIR_ASSETS,
    CATALOG_NAME_PATTERN,
    CATALOG_REQUIRED_COMMON_ASSETS,
    CATALOG_REQUIRED_ENTRY_FILES,
    CATALOG_TAG_PATTERN,
    CATALOG_VERSION_FILENAME,
    DEFAULT_CATALOG_URL,
    DEVCONTAINER_CONTAINER_SOURCE_FIELDS,
    MIN_CATALOG_TAG_VERSION,
    SEMVER_PATTERN,
)


def _create_valid_common_assets(assets_dir):
    """Create a fully valid common/devcontainer-assets/ directory."""
    os.makedirs(assets_dir, exist_ok=True)
    for filename in CATALOG_REQUIRED_COMMON_ASSETS:
        filepath = os.path.join(assets_dir, filename)
        with open(filepath, "w") as f:
            f.write("#!/bin/bash\n")
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


class TestCatalogEntry(TestCase):
    """Test CatalogEntry dataclass."""

    def test_from_dict_all_fields(self):
        data = {
            "name": "my-collection",
            "description": "A test entry",
            "tags": ["java", "spring-boot"],
            "maintainer": "team-a",
            "min_cli_version": "2.0.0",
        }
        entry = CatalogEntry.from_dict(data)
        self.assertEqual(entry.name, "my-collection")
        self.assertEqual(entry.description, "A test entry")
        self.assertEqual(entry.tags, ["java", "spring-boot"])
        self.assertEqual(entry.maintainer, "team-a")
        self.assertEqual(entry.min_cli_version, "2.0.0")

    def test_from_dict_required_only(self):
        data = {"name": "basic", "description": "Basic setup"}
        entry = CatalogEntry.from_dict(data)
        self.assertEqual(entry.name, "basic")
        self.assertEqual(entry.description, "Basic setup")
        self.assertEqual(entry.tags, [])
        self.assertIsNone(entry.maintainer)
        self.assertIsNone(entry.min_cli_version)

    def test_from_dict_empty(self):
        entry = CatalogEntry.from_dict({})
        self.assertEqual(entry.name, "")
        self.assertEqual(entry.description, "")

    def test_to_dict_all_fields(self):
        entry = CatalogEntry(
            name="my-collection",
            description="Desc",
            tags=["java"],
            maintainer="team",
            min_cli_version="1.0.0",
        )
        result = entry.to_dict()
        self.assertEqual(result["name"], "my-collection")
        self.assertEqual(result["description"], "Desc")
        self.assertEqual(result["tags"], ["java"])
        self.assertEqual(result["maintainer"], "team")
        self.assertEqual(result["min_cli_version"], "1.0.0")

    def test_to_dict_required_only(self):
        entry = CatalogEntry(name="basic", description="Desc")
        result = entry.to_dict()
        self.assertEqual(set(result.keys()), {"name", "description"})

    def test_to_dict_omits_none_optional(self):
        entry = CatalogEntry(name="ab", description="D", maintainer=None)
        result = entry.to_dict()
        self.assertNotIn("maintainer", result)
        self.assertNotIn("min_cli_version", result)
        self.assertNotIn("tags", result)


class TestValidateCatalogEntry(TestCase):
    """Test catalog-entry.json validation."""

    def test_valid_minimal(self):
        data = {"name": "my-app", "description": "An application setup"}
        errors = validate_catalog_entry(data)
        self.assertEqual(errors, [])

    def test_valid_all_fields(self):
        data = {
            "name": "java-spring",
            "description": "Java Spring Boot",
            "tags": ["java", "spring-boot"],
            "maintainer": "platform-team",
            "min_cli_version": "2.0.0",
        }
        errors = validate_catalog_entry(data)
        self.assertEqual(errors, [])

    def test_missing_name(self):
        data = {"description": "No name"}
        errors = validate_catalog_entry(data)
        self.assertTrue(any("'name' is required" in e for e in errors))

    def test_empty_name(self):
        data = {"name": "", "description": "Empty name"}
        errors = validate_catalog_entry(data)
        self.assertTrue(any("'name' is required" in e for e in errors))

    def test_name_not_string(self):
        data = {"name": 123, "description": "Not a string"}
        errors = validate_catalog_entry(data)
        self.assertTrue(any("'name' is required" in e for e in errors))

    def test_missing_description(self):
        data = {"name": "valid-name"}
        errors = validate_catalog_entry(data)
        self.assertTrue(any("'description' is required" in e for e in errors))

    def test_empty_description(self):
        data = {"name": "valid-name", "description": ""}
        errors = validate_catalog_entry(data)
        self.assertTrue(any("'description' is required" in e for e in errors))

    def test_name_pattern_valid(self):
        valid_names = ["ab", "my-app", "java-spring-boot", "a1", "app2go"]
        for name in valid_names:
            data = {"name": name, "description": "Test"}
            errors = validate_catalog_entry(data)
            self.assertEqual(errors, [], f"Expected no errors for name '{name}'")

    def test_name_pattern_invalid(self):
        invalid_names = [
            "a",  # too short
            "A",  # uppercase
            "My-App",  # uppercase
            "my app",  # space
            "-my-app",  # starts with dash
            "my-app-",  # ends with dash
            "my_app",  # underscore
            "123",  # starts with number
        ]
        for name in invalid_names:
            data = {"name": name, "description": "Test"}
            errors = validate_catalog_entry(data)
            self.assertTrue(
                any("pattern" in e for e in errors),
                f"Expected pattern error for name '{name}', got {errors}",
            )

    def test_tags_valid(self):
        data = {"name": "ab", "description": "D", "tags": ["java", "spring-boot"]}
        errors = validate_catalog_entry(data)
        self.assertEqual(errors, [])

    def test_tags_not_array(self):
        data = {"name": "ab", "description": "D", "tags": "java"}
        errors = validate_catalog_entry(data)
        self.assertTrue(any("'tags' must be an array" in e for e in errors))

    def test_tags_invalid_format(self):
        data = {"name": "ab", "description": "D", "tags": ["Java", "valid-tag"]}
        errors = validate_catalog_entry(data)
        self.assertTrue(any("tags[0]" in e for e in errors))

    def test_tags_non_string_element(self):
        data = {"name": "ab", "description": "D", "tags": [123]}
        errors = validate_catalog_entry(data)
        self.assertTrue(any("tags[0] must be a string" in e for e in errors))

    def test_maintainer_valid(self):
        data = {"name": "ab", "description": "D", "maintainer": "team-a"}
        errors = validate_catalog_entry(data)
        self.assertEqual(errors, [])

    def test_maintainer_empty(self):
        data = {"name": "ab", "description": "D", "maintainer": ""}
        errors = validate_catalog_entry(data)
        self.assertTrue(any("'maintainer' must be a non-empty" in e for e in errors))

    def test_min_cli_version_valid(self):
        data = {"name": "ab", "description": "D", "min_cli_version": "2.0.0"}
        errors = validate_catalog_entry(data)
        self.assertEqual(errors, [])

    def test_min_cli_version_invalid(self):
        data = {"name": "ab", "description": "D", "min_cli_version": "v2.0"}
        errors = validate_catalog_entry(data)
        self.assertTrue(any("semver" in e for e in errors))

    def test_min_cli_version_not_string(self):
        data = {"name": "ab", "description": "D", "min_cli_version": 200}
        errors = validate_catalog_entry(data)
        self.assertTrue(any("must be a string" in e for e in errors))


class TestValidateEntryStructure(TestCase):
    """Test entry directory structure validation."""

    def test_valid_entry(self, tmp_path=None):
        if tmp_path is None:
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                self._run_valid_test(tmp)
        else:
            self._run_valid_test(str(tmp_path))

    def _run_valid_test(self, tmp_dir):
        for filename in CATALOG_REQUIRED_ENTRY_FILES:
            with open(os.path.join(tmp_dir, filename), "w") as f:
                f.write("{}" if filename.endswith(".json") else "1.0.0")
        errors = validate_entry_structure(tmp_dir)
        self.assertEqual(errors, [])

    def test_missing_all_files(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            errors = validate_entry_structure(tmp)
            self.assertEqual(len(errors), len(CATALOG_REQUIRED_ENTRY_FILES))

    def test_missing_one_file(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            # Create all but VERSION
            for filename in CATALOG_REQUIRED_ENTRY_FILES:
                if filename != CATALOG_VERSION_FILENAME:
                    with open(os.path.join(tmp, filename), "w") as f:
                        f.write("{}")
            errors = validate_entry_structure(tmp)
            self.assertEqual(len(errors), 1)
            self.assertIn("VERSION", errors[0])


class TestDetectFileConflicts(TestCase):
    """Test file conflict detection between entry and common assets."""

    def test_no_conflicts(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "devcontainer.json"), "w") as f:
                f.write("{}")
            conflicts = detect_file_conflicts(tmp, CATALOG_REQUIRED_COMMON_ASSETS)
            self.assertEqual(conflicts, [])

    def test_conflict_detected(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            # Create a file that conflicts with common assets
            with open(os.path.join(tmp, ".devcontainer.postcreate.sh"), "w") as f:
                f.write("#!/bin/bash")
            conflicts = detect_file_conflicts(tmp, CATALOG_REQUIRED_COMMON_ASSETS)
            self.assertEqual(conflicts, [".devcontainer.postcreate.sh"])

    def test_multiple_conflicts(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            for asset in CATALOG_REQUIRED_COMMON_ASSETS:
                with open(os.path.join(tmp, asset), "w") as f:
                    f.write("")
            conflicts = detect_file_conflicts(tmp, CATALOG_REQUIRED_COMMON_ASSETS)
            self.assertEqual(len(conflicts), len(CATALOG_REQUIRED_COMMON_ASSETS))

    def test_nonexistent_directory(self):
        conflicts = detect_file_conflicts("/nonexistent/path", CATALOG_REQUIRED_COMMON_ASSETS)
        self.assertEqual(conflicts, [])


class TestValidatePostcreateCommand(TestCase):
    """Test postCreateCommand validation in devcontainer.json."""

    def test_valid_string_command(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode"}
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_postcreate_command(path)
            self.assertEqual(errors, [])

    def test_valid_complex_command(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            cmd = "bash -c 'source shell.env && sudo -E bash" " .devcontainer/.devcontainer.postcreate.sh vscode'"
            config = {"postCreateCommand": cmd}
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_postcreate_command(path)
            self.assertEqual(errors, [])

    def test_valid_wrapper_command(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            cmd = (
                "bash -c 'set -o pipefail; bash .devcontainer/"
                "postcreate-wrapper.sh 2>&1 | tee /tmp/devcontainer-setup.log'"
            )
            config = {"postCreateCommand": cmd}
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_postcreate_command(path)
            self.assertEqual(errors, [])

    def test_missing_postcreate_reference(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {"postCreateCommand": "echo hello"}
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_postcreate_command(path)
            self.assertTrue(any("postcreate" in e for e in errors))

    def test_array_command_valid(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {
                "postCreateCommand": [
                    "bash",
                    ".devcontainer/.devcontainer.postcreate.sh",
                ]
            }
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_postcreate_command(path)
            self.assertEqual(errors, [])

    def test_array_command_missing_postcreate(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {"postCreateCommand": ["echo", "hello"]}
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_postcreate_command(path)
            self.assertTrue(any("postcreate" in e for e in errors))

    def test_no_post_create_command(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {"name": "test"}
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_postcreate_command(path)
            self.assertTrue(any("postcreate" in e for e in errors))

    def test_file_not_found(self):
        errors = validate_postcreate_command("/nonexistent/devcontainer.json")
        self.assertTrue(any("not found" in e for e in errors))

    def test_invalid_json(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            with open(path, "w") as f:
                f.write("not json")
            errors = validate_postcreate_command(path)
            self.assertTrue(any("parse" in e.lower() for e in errors))


class TestDiscoverEntryPaths(TestCase):
    """Test entry path discovery."""

    def test_discovers_entries(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            col1 = os.path.join(tmp, "catalog", "app-a")
            col2 = os.path.join(tmp, "catalog", "app-b")
            os.makedirs(col1)
            os.makedirs(col2)
            with open(os.path.join(col1, CATALOG_ENTRY_FILENAME), "w") as f:
                f.write("{}")
            with open(os.path.join(col2, CATALOG_ENTRY_FILENAME), "w") as f:
                f.write("{}")
            result = discover_entry_paths(tmp)
            self.assertEqual(len(result), 2)

    def test_discovers_nested_entries(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            nested = os.path.join(tmp, "catalog", "group", "subgroup", "app")
            os.makedirs(nested)
            with open(os.path.join(nested, CATALOG_ENTRY_FILENAME), "w") as f:
                f.write("{}")
            result = discover_entry_paths(tmp)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0], nested)

    def test_no_entries_dir(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result = discover_entry_paths(tmp)
            self.assertEqual(result, [])

    def test_empty_entries_dir(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "catalog"))
            result = discover_entry_paths(tmp)
            self.assertEqual(result, [])

    def test_results_sorted(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            for name in ["zebra", "alpha", "middle"]:
                col = os.path.join(tmp, "catalog", name)
                os.makedirs(col)
                with open(os.path.join(col, CATALOG_ENTRY_FILENAME), "w") as f:
                    f.write("{}")
            result = discover_entry_paths(tmp)
            basenames = [os.path.basename(p) for p in result]
            self.assertEqual(basenames, ["alpha", "middle", "zebra"])


class TestValidateCommonAssets(TestCase):
    """Test common assets directory validation."""

    def test_valid_common_assets(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)
            errors = validate_common_assets(tmp)
            self.assertEqual(errors, [])

    def test_missing_assets_dir(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            errors = validate_common_assets(tmp)
            self.assertTrue(any("Missing required directory" in e for e in errors))

    def test_missing_one_asset(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)
            # Remove one required asset
            os.remove(os.path.join(assets_dir, "project-setup.sh"))
            errors = validate_common_assets(tmp)
            self.assertTrue(any("project-setup.sh" in e for e in errors))


class TestValidateEntry(TestCase):
    """Test full entry validation."""

    def _create_valid_entry(self, parent_dir, entry_name="test-app"):
        """Create a minimal valid entry in parent_dir/<entry_name>."""
        entry_dir = os.path.join(parent_dir, entry_name)
        os.makedirs(entry_dir, exist_ok=True)
        entry = {"name": entry_name, "description": "Test application"}
        with open(os.path.join(entry_dir, CATALOG_ENTRY_FILENAME), "w") as f:
            json.dump(entry, f)
        devcontainer = {
            "name": "caylent-devcontainer",
            "image": "mcr.microsoft.com/devcontainers/base:noble",
            "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
        }
        with open(os.path.join(entry_dir, "devcontainer.json"), "w") as f:
            json.dump(devcontainer, f)
        with open(os.path.join(entry_dir, CATALOG_VERSION_FILENAME), "w") as f:
            f.write("1.0.0")
        return entry_dir

    def test_valid_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_dir = self._create_valid_entry(tmp)
            errors = validate_entry(entry_dir)
            self.assertEqual(errors, [])

    def test_invalid_entry_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_dir = self._create_valid_entry(tmp)
            # Overwrite with invalid entry
            with open(os.path.join(entry_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump({"name": "A"}, f)  # uppercase, no description
            errors = validate_entry(entry_dir)
            self.assertTrue(len(errors) >= 2)  # name pattern + missing description

    def test_conflict_with_common_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_dir = self._create_valid_entry(tmp)
            with open(os.path.join(entry_dir, "devcontainer-functions.sh"), "w") as f:
                f.write("")
            errors = validate_entry(entry_dir)
            self.assertTrue(any("conflicts with" in e for e in errors))

    def test_broken_json_in_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_dir = self._create_valid_entry(tmp)
            with open(os.path.join(entry_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                f.write("not json")
            errors = validate_entry(entry_dir)
            self.assertTrue(any("Invalid JSON" in e for e in errors))


class TestValidateCatalog(TestCase):
    """Test full catalog validation."""

    def _create_valid_catalog(self, tmp_dir):
        """Create a minimal valid catalog structure."""
        assets_dir = os.path.join(tmp_dir, "common", "devcontainer-assets")
        _create_valid_common_assets(assets_dir)

        col_dir = os.path.join(tmp_dir, "catalog", "default")
        os.makedirs(col_dir)
        entry = {"name": "default", "description": "Default entry"}
        with open(os.path.join(col_dir, CATALOG_ENTRY_FILENAME), "w") as f:
            json.dump(entry, f)
        devcontainer = {
            "name": "caylent-devcontainer",
            "image": "mcr.microsoft.com/devcontainers/base:noble",
            "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
        }
        with open(os.path.join(col_dir, "devcontainer.json"), "w") as f:
            json.dump(devcontainer, f)
        with open(os.path.join(col_dir, CATALOG_VERSION_FILENAME), "w") as f:
            f.write("1.0.0")

    def test_valid_catalog(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_catalog(tmp)
            errors = validate_catalog(tmp)
            self.assertEqual(errors, [])

    def test_missing_common_assets(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            col_dir = os.path.join(tmp, "catalog", "app")
            os.makedirs(col_dir)
            entry = {"name": "app", "description": "App"}
            with open(os.path.join(col_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(entry, f)
            with open(os.path.join(col_dir, "devcontainer.json"), "w") as f:
                json.dump(
                    {
                        "name": "caylent-devcontainer",
                        "image": "mcr.microsoft.com/devcontainers/base:noble",
                        "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh",
                    },
                    f,
                )
            with open(os.path.join(col_dir, CATALOG_VERSION_FILENAME), "w") as f:
                f.write("1.0.0")
            errors = validate_catalog(tmp)
            self.assertTrue(any("Missing required directory" in e for e in errors))

    def test_no_entries(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)
            errors = validate_catalog(tmp)
            self.assertTrue(any("No entries found" in e for e in errors))

    def test_duplicate_entry_names(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_catalog(tmp)
            # Add a second entry with same name
            col2 = os.path.join(tmp, "catalog", "other")
            os.makedirs(col2)
            entry = {"name": "default", "description": "Duplicate name"}
            with open(os.path.join(col2, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(entry, f)
            devcontainer = {
                "name": "caylent-devcontainer",
                "image": "mcr.microsoft.com/devcontainers/base:noble",
                "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh",
            }
            with open(os.path.join(col2, "devcontainer.json"), "w") as f:
                json.dump(devcontainer, f)
            with open(os.path.join(col2, CATALOG_VERSION_FILENAME), "w") as f:
                f.write("1.0.0")
            errors = validate_catalog(tmp)
            self.assertTrue(any("Duplicate entry name" in e for e in errors))


class TestConstants(TestCase):
    """Verify catalog constants are properly defined."""

    def test_name_pattern_matches_valid(self):
        self.assertIsNotNone(CATALOG_NAME_PATTERN.match("ab"))
        self.assertIsNotNone(CATALOG_NAME_PATTERN.match("my-app"))
        self.assertIsNotNone(CATALOG_NAME_PATTERN.match("java-spring-boot-21"))

    def test_name_pattern_rejects_invalid(self):
        self.assertIsNone(CATALOG_NAME_PATTERN.match("a"))
        self.assertIsNone(CATALOG_NAME_PATTERN.match("A"))
        self.assertIsNone(CATALOG_NAME_PATTERN.match("-ab"))
        self.assertIsNone(CATALOG_NAME_PATTERN.match("ab-"))

    def test_tag_pattern_matches_valid(self):
        self.assertIsNotNone(CATALOG_TAG_PATTERN.match("java"))
        self.assertIsNotNone(CATALOG_TAG_PATTERN.match("spring-boot"))

    def test_required_common_assets_defined(self):
        self.assertIn(".devcontainer.postcreate.sh", CATALOG_REQUIRED_COMMON_ASSETS)
        self.assertIn("devcontainer-functions.sh", CATALOG_REQUIRED_COMMON_ASSETS)
        self.assertIn("project-setup.sh", CATALOG_REQUIRED_COMMON_ASSETS)

    def test_required_entry_files_defined(self):
        self.assertIn(CATALOG_ENTRY_FILENAME, CATALOG_REQUIRED_ENTRY_FILES)
        self.assertIn("devcontainer.json", CATALOG_REQUIRED_ENTRY_FILES)
        self.assertIn(CATALOG_VERSION_FILENAME, CATALOG_REQUIRED_ENTRY_FILES)


class TestEntryInfo(TestCase):
    """Test EntryInfo dataclass."""

    def test_creation(self):
        entry = CatalogEntry(name="my-app", description="App")
        info = EntryInfo(path="/some/path", entry=entry)
        self.assertEqual(info.path, "/some/path")
        self.assertEqual(info.entry.name, "my-app")
        self.assertEqual(info.entry.description, "App")

    def test_different_entries(self):
        entry1 = CatalogEntry(name="app-a", description="A", tags=["java"])
        entry2 = CatalogEntry(name="app-b", description="B", maintainer="team")
        info1 = EntryInfo(path="/path/a", entry=entry1)
        info2 = EntryInfo(path="/path/b", entry=entry2)
        self.assertNotEqual(info1.path, info2.path)
        self.assertNotEqual(info1.entry.name, info2.entry.name)


class TestParseCatalogUrl(TestCase):
    """Test parse_catalog_url() for all URL format variations."""

    def test_https_with_git_suffix_no_ref(self):
        url, ref = parse_catalog_url("https://github.com/org/repo.git")
        self.assertEqual(url, "https://github.com/org/repo.git")
        self.assertIsNone(ref)

    def test_https_with_git_suffix_and_ref(self):
        url, ref = parse_catalog_url("https://github.com/org/repo.git@v2.0")
        self.assertEqual(url, "https://github.com/org/repo.git")
        self.assertEqual(ref, "v2.0")

    def test_https_with_git_suffix_and_branch_ref(self):
        url, ref = parse_catalog_url("https://github.com/org/repo.git@feature/branch")
        self.assertEqual(url, "https://github.com/org/repo.git")
        self.assertEqual(ref, "feature/branch")

    def test_https_without_git_suffix_no_ref(self):
        url, ref = parse_catalog_url("https://github.com/org/repo")
        self.assertEqual(url, "https://github.com/org/repo")
        self.assertIsNone(ref)

    def test_https_without_git_suffix_with_ref(self):
        url, ref = parse_catalog_url("https://github.com/org/repo@v2.0")
        self.assertEqual(url, "https://github.com/org/repo")
        self.assertEqual(ref, "v2.0")

    def test_ssh_url_no_ref(self):
        url, ref = parse_catalog_url("git@github.com:org/repo.git")
        self.assertEqual(url, "git@github.com:org/repo.git")
        self.assertIsNone(ref)

    def test_ssh_url_with_ref(self):
        url, ref = parse_catalog_url("git@github.com:org/repo.git@main")
        self.assertEqual(url, "git@github.com:org/repo.git")
        self.assertEqual(ref, "main")

    def test_ssh_url_no_git_suffix_no_ref(self):
        # Single @ with colon after -> SSH prefix, not a ref delimiter
        url, ref = parse_catalog_url("git@github.com:org/repo")
        self.assertEqual(url, "git@github.com:org/repo")
        self.assertIsNone(ref)

    def test_ssh_url_no_git_suffix_with_ref(self):
        # Two @s: first is SSH prefix, second is ref delimiter
        url, ref = parse_catalog_url("git@github.com:org/repo@v1.0")
        self.assertEqual(url, "git@github.com:org/repo")
        self.assertEqual(ref, "v1.0")

    def test_empty_url_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_catalog_url("")
        self.assertIn("must not be empty", str(ctx.exception))

    def test_git_suffix_with_trailing_at_only(self):
        # .git@ with nothing after the @
        url, ref = parse_catalog_url("https://github.com/org/repo.git@")
        self.assertEqual(url, "https://github.com/org/repo.git@")
        self.assertIsNone(ref)

    def test_no_at_no_git_suffix(self):
        url, ref = parse_catalog_url("https://github.com/org/repo")
        self.assertEqual(url, "https://github.com/org/repo")
        self.assertIsNone(ref)

    def test_multiple_at_last_one_is_ref(self):
        url, ref = parse_catalog_url("git@github.com:org/repo@develop")
        self.assertEqual(url, "git@github.com:org/repo")
        self.assertEqual(ref, "develop")

    def test_git_suffix_in_middle_of_path(self):
        # .git appears but with a path after — still anchors on .git
        url, ref = parse_catalog_url("https://github.com/org/repo.git@release/1.0")
        self.assertEqual(url, "https://github.com/org/repo.git")
        self.assertEqual(ref, "release/1.0")

    def test_single_at_no_colon_after(self):
        # Single @ without colon after it -> ref delimiter
        url, ref = parse_catalog_url("https://example.com/repo@tag")
        self.assertEqual(url, "https://example.com/repo")
        self.assertEqual(ref, "tag")

    def test_multiple_at_empty_ref(self):
        # Multiple @s but last one has empty string after
        url, ref = parse_catalog_url("git@github.com:org/repo@")
        self.assertEqual(url, "git@github.com:org/repo")
        self.assertIsNone(ref)


class TestCloneCatalogRepo(TestCase):
    """Test clone_catalog_repo() with mocked subprocess."""

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    @patch("caylent_devcontainer_cli.utils.catalog.tempfile.mkdtemp")
    def test_clone_success_no_ref(self, mock_mkdtemp, mock_run):
        mock_mkdtemp.return_value = "/tmp/catalog-abc"
        mock_run.return_value = type("Result", (), {"returncode": 0, "stderr": ""})()

        result = clone_catalog_repo("https://github.com/org/repo.git")

        self.assertEqual(result, "/tmp/catalog-abc")
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertEqual(
            cmd,
            [
                "git",
                "clone",
                "--depth",
                "1",
                "https://github.com/org/repo.git",
                "/tmp/catalog-abc",
            ],
        )

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    @patch("caylent_devcontainer_cli.utils.catalog.tempfile.mkdtemp")
    def test_clone_success_with_ref(self, mock_mkdtemp, mock_run):
        mock_mkdtemp.return_value = "/tmp/catalog-xyz"
        mock_run.return_value = type("Result", (), {"returncode": 0, "stderr": ""})()

        result = clone_catalog_repo("https://github.com/org/repo.git@v2.0")

        self.assertEqual(result, "/tmp/catalog-xyz")
        cmd = mock_run.call_args[0][0]
        self.assertEqual(
            cmd,
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                "v2.0",
                "https://github.com/org/repo.git",
                "/tmp/catalog-xyz",
            ],
        )

    @patch("caylent_devcontainer_cli.utils.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    @patch("caylent_devcontainer_cli.utils.catalog.tempfile.mkdtemp")
    def test_clone_failure_exits(self, mock_mkdtemp, mock_run, mock_rmtree):
        mock_mkdtemp.return_value = "/tmp/catalog-fail"
        mock_run.return_value = type("Result", (), {"returncode": 128, "stderr": "fatal: repo not found"})()

        with self.assertRaises(SystemExit) as ctx:
            clone_catalog_repo("https://github.com/org/repo.git")

        error_msg = str(ctx.exception)
        self.assertIn("Failed to clone", error_msg)
        self.assertIn("https://github.com/org/repo.git", error_msg)
        self.assertIn("HTTPS repos", error_msg)
        self.assertIn("SSH repos", error_msg)
        self.assertIn("git ls-remote", error_msg)
        self.assertIn("fatal: repo not found", error_msg)
        mock_rmtree.assert_called_once_with("/tmp/catalog-fail", ignore_errors=True)

    @patch("caylent_devcontainer_cli.utils.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    @patch("caylent_devcontainer_cli.utils.catalog.tempfile.mkdtemp")
    def test_clone_failure_with_ref_includes_ref_in_message(self, mock_mkdtemp, mock_run, mock_rmtree):
        mock_mkdtemp.return_value = "/tmp/catalog-fail2"
        mock_run.return_value = type("Result", (), {"returncode": 128, "stderr": "branch not found"})()

        with self.assertRaises(SystemExit) as ctx:
            clone_catalog_repo("https://github.com/org/repo.git@v999")

        error_msg = str(ctx.exception)
        self.assertIn("ref: v999", error_msg)

    @patch("caylent_devcontainer_cli.utils.catalog.shutil.rmtree")
    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    @patch("caylent_devcontainer_cli.utils.catalog.tempfile.mkdtemp")
    def test_clone_failure_no_stderr(self, mock_mkdtemp, mock_run, mock_rmtree):
        mock_mkdtemp.return_value = "/tmp/catalog-fail3"
        mock_run.return_value = type("Result", (), {"returncode": 1, "stderr": ""})()

        with self.assertRaises(SystemExit) as ctx:
            clone_catalog_repo("https://github.com/org/repo.git")

        error_msg = str(ctx.exception)
        self.assertIn("Failed to clone", error_msg)
        self.assertNotIn("Git error:", error_msg)

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    @patch("caylent_devcontainer_cli.utils.catalog.tempfile.mkdtemp")
    def test_clone_uses_shallow_depth(self, mock_mkdtemp, mock_run):
        mock_mkdtemp.return_value = "/tmp/catalog-shallow"
        mock_run.return_value = type("Result", (), {"returncode": 0, "stderr": ""})()

        clone_catalog_repo("https://github.com/org/repo.git")

        cmd = mock_run.call_args[0][0]
        self.assertIn("--depth", cmd)
        depth_idx = cmd.index("--depth")
        self.assertEqual(cmd[depth_idx + 1], "1")


class TestDiscoverEntries(TestCase):
    """Test discover_entries() metadata parsing and sorting."""

    def test_default_first_then_alpha(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Create entries in non-alpha order
            for name in ["zebra", "default", "alpha"]:
                col = os.path.join(tmp, "catalog", name)
                os.makedirs(col)
                entry = {"name": name, "description": f"Desc for {name}"}
                with open(os.path.join(col, CATALOG_ENTRY_FILENAME), "w") as f:
                    json.dump(entry, f)
            entries = discover_entries(tmp)
            self.assertEqual(len(entries), 3)
            self.assertEqual(entries[0].entry.name, "default")
            self.assertEqual(entries[1].entry.name, "alpha")
            self.assertEqual(entries[2].entry.name, "zebra")

    def test_parses_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            col = os.path.join(tmp, "catalog", "my-app")
            os.makedirs(col)
            entry = {
                "name": "my-app",
                "description": "My application",
                "tags": ["python", "aws"],
                "maintainer": "team-a",
                "min_cli_version": "2.0.0",
            }
            with open(os.path.join(col, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(entry, f)
            entries = discover_entries(tmp)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].entry.name, "my-app")
            self.assertEqual(entries[0].entry.tags, ["python", "aws"])
            self.assertEqual(entries[0].entry.maintainer, "team-a")
            self.assertEqual(entries[0].entry.min_cli_version, "2.0.0")
            self.assertEqual(entries[0].path, col)

    def test_skips_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            col = os.path.join(tmp, "catalog", "broken")
            os.makedirs(col)
            with open(os.path.join(col, CATALOG_ENTRY_FILENAME), "w") as f:
                f.write("not valid json")
            entries = discover_entries(tmp)
            self.assertEqual(len(entries), 0)

    def test_empty_entries_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "catalog"))
            entries = discover_entries(tmp)
            self.assertEqual(len(entries), 0)

    def test_no_entries_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = discover_entries(tmp)
            self.assertEqual(len(entries), 0)

    def test_without_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["beta", "alpha"]:
                col = os.path.join(tmp, "catalog", name)
                os.makedirs(col)
                entry = {"name": name, "description": f"Desc {name}"}
                with open(os.path.join(col, CATALOG_ENTRY_FILENAME), "w") as f:
                    json.dump(entry, f)
            entries = discover_entries(tmp)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0].entry.name, "alpha")
            self.assertEqual(entries[1].entry.name, "beta")

    def test_skip_incomplete_filters_missing_devcontainer_json(self):
        """Entries missing devcontainer.json are skipped when skip_incomplete=True."""
        with tempfile.TemporaryDirectory() as tmp:
            # Complete entry
            complete = os.path.join(tmp, "catalog", "complete")
            os.makedirs(complete)
            with open(os.path.join(complete, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump({"name": "complete", "description": "Has all files"}, f)
            with open(os.path.join(complete, "devcontainer.json"), "w") as f:
                json.dump({"name": "test"}, f)

            # Incomplete entry (missing devcontainer.json)
            incomplete = os.path.join(tmp, "catalog", "incomplete")
            os.makedirs(incomplete)
            with open(os.path.join(incomplete, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(
                    {"name": "incomplete", "description": "Missing devcontainer.json"},
                    f,
                )

            # Without skip_incomplete: both returned
            entries_all = discover_entries(tmp, skip_incomplete=False)
            self.assertEqual(len(entries_all), 2)

            # With skip_incomplete: only complete returned
            entries_filtered = discover_entries(tmp, skip_incomplete=True)
            self.assertEqual(len(entries_filtered), 1)
            self.assertEqual(entries_filtered[0].entry.name, "complete")

    def test_skip_incomplete_default_false(self):
        """By default, skip_incomplete is False — incomplete entries are included."""
        with tempfile.TemporaryDirectory() as tmp:
            col = os.path.join(tmp, "catalog", "no-devcontainer")
            os.makedirs(col)
            with open(os.path.join(col, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(
                    {"name": "no-devcontainer", "description": "No devcontainer.json"},
                    f,
                )

            entries = discover_entries(tmp)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].entry.name, "no-devcontainer")


class TestCopyEntryToProject(TestCase):
    """Test copy_entry_to_project() file merging and augmentation."""

    def _setup_entry_and_assets(self, tmp_dir):
        """Create an entry dir and common assets dir for testing."""
        entry_src = os.path.join(tmp_dir, "collection")
        assets = os.path.join(tmp_dir, "assets")
        target = os.path.join(tmp_dir, "target")
        os.makedirs(entry_src)
        os.makedirs(assets)

        # Entry files
        entry = {"name": "test-app", "description": "Test app"}
        with open(os.path.join(entry_src, CATALOG_ENTRY_FILENAME), "w") as f:
            json.dump(entry, f)
        with open(os.path.join(entry_src, "devcontainer.json"), "w") as f:
            json.dump({"name": "test"}, f)
        with open(os.path.join(entry_src, "VERSION"), "w") as f:
            f.write("1.0.0")

        # Common assets
        with open(os.path.join(assets, ".devcontainer.postcreate.sh"), "w") as f:
            f.write("#!/bin/bash\necho postcreate")
        with open(os.path.join(assets, "devcontainer-functions.sh"), "w") as f:
            f.write("#!/bin/bash\necho functions")
        with open(os.path.join(assets, "project-setup.sh"), "w") as f:
            f.write("#!/bin/bash\necho setup")

        return entry_src, assets, target

    def test_copies_entry_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, target = self._setup_entry_and_assets(tmp)
            copy_entry_to_project(entry_src, assets, target, "https://example.com/repo.git")

            self.assertTrue(os.path.isfile(os.path.join(target, "devcontainer.json")))
            self.assertTrue(os.path.isfile(os.path.join(target, "VERSION")))

    def test_copies_common_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, target = self._setup_entry_and_assets(tmp)
            copy_entry_to_project(entry_src, assets, target, "https://example.com/repo.git")

            self.assertTrue(os.path.isfile(os.path.join(target, ".devcontainer.postcreate.sh")))
            self.assertTrue(os.path.isfile(os.path.join(target, "devcontainer-functions.sh")))
            self.assertTrue(os.path.isfile(os.path.join(target, "project-setup.sh")))

    def test_common_assets_override_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, target = self._setup_entry_and_assets(tmp)
            # Add a file to entry that also exists in assets
            with open(os.path.join(entry_src, "project-setup.sh"), "w") as f:
                f.write("entry version")
            with open(os.path.join(assets, "project-setup.sh"), "w") as f:
                f.write("assets version")

            copy_entry_to_project(entry_src, assets, target, "https://example.com/repo.git")

            with open(os.path.join(target, "project-setup.sh")) as f:
                content = f.read()
            self.assertEqual(content, "assets version")

    def test_augments_catalog_entry_with_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, target = self._setup_entry_and_assets(tmp)
            catalog_url = "https://github.com/org/repo.git@v2.0"
            copy_entry_to_project(entry_src, assets, target, catalog_url)

            with open(os.path.join(target, CATALOG_ENTRY_FILENAME)) as f:
                data = json.load(f)
            self.assertEqual(data["catalog_url"], catalog_url)
            self.assertEqual(data["name"], "test-app")

    def test_creates_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, _ = self._setup_entry_and_assets(tmp)
            target = os.path.join(tmp, "nested", "deep", "target")
            copy_entry_to_project(entry_src, assets, target, "https://example.com/repo.git")

            self.assertTrue(os.path.isdir(target))

    def test_copies_subdirectories(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, target = self._setup_entry_and_assets(tmp)
            # Add a subdirectory to entry
            subdir = os.path.join(entry_src, "nix-family-os")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "tinyproxy.conf"), "w") as f:
                f.write("proxy config")

            copy_entry_to_project(entry_src, assets, target, "https://example.com/repo.git")

            self.assertTrue(os.path.isdir(os.path.join(target, "nix-family-os")))
            self.assertTrue(os.path.isfile(os.path.join(target, "nix-family-os", "tinyproxy.conf")))

    def test_catalog_entry_json_has_trailing_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, target = self._setup_entry_and_assets(tmp)
            copy_entry_to_project(entry_src, assets, target, "https://example.com/repo.git")

            with open(os.path.join(target, CATALOG_ENTRY_FILENAME)) as f:
                content = f.read()
            self.assertTrue(content.endswith("\n"))

    def test_no_example_files_present_no_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_src, assets, target = self._setup_entry_and_assets(tmp)
            # No example files exist — should not raise
            copy_entry_to_project(entry_src, assets, target, "https://example.com/repo.git")
            self.assertTrue(os.path.isdir(target))


class TestResolveLatestCatalogTag(TestCase):
    """Test resolve_latest_catalog_tag() tag parsing, filtering, and sorting."""

    def _make_ls_remote_output(self, tags):
        """Build git ls-remote --tags stdout from a list of tag names."""
        lines = []
        for tag in tags:
            lines.append(f"abc123\trefs/tags/{tag}")
        return "\n".join(lines)

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_returns_highest_tag(self, mock_run):
        mock_run.return_value = type(
            "Result",
            (),
            {
                "returncode": 0,
                "stderr": "",
                "stdout": self._make_ls_remote_output(["2.0.0", "2.1.0", "2.0.1"]),
            },
        )()
        result = resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        self.assertEqual(result, "2.1.0")

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_filters_below_min_version(self, mock_run):
        mock_run.return_value = type(
            "Result",
            (),
            {
                "returncode": 0,
                "stderr": "",
                "stdout": self._make_ls_remote_output(["1.0.0", "1.9.9", "2.0.0"]),
            },
        )()
        result = resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        self.assertEqual(result, "2.0.0")

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_includes_exact_min_version(self, mock_run):
        mock_run.return_value = type(
            "Result",
            (),
            {
                "returncode": 0,
                "stderr": "",
                "stdout": self._make_ls_remote_output(["2.0.0"]),
            },
        )()
        result = resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        self.assertEqual(result, "2.0.0")

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_skips_dereferenced_tags(self, mock_run):
        stdout = (
            "abc123\trefs/tags/2.0.0\ndef456\trefs/tags/2.0.0^{}\nabc789\trefs/tags/2.1.0\ndef012\trefs/tags/2.1.0^{}"
        )
        mock_run.return_value = type("Result", (), {"returncode": 0, "stderr": "", "stdout": stdout})()
        result = resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        self.assertEqual(result, "2.1.0")

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_skips_non_semver_tags(self, mock_run):
        stdout = self._make_ls_remote_output(["v2.0.0", "release-2.0", "2.0.0", "latest"])
        mock_run.return_value = type("Result", (), {"returncode": 0, "stderr": "", "stdout": stdout})()
        result = resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        self.assertEqual(result, "2.0.0")

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_no_compatible_tags_raises_system_exit(self, mock_run):
        mock_run.return_value = type(
            "Result",
            (),
            {
                "returncode": 0,
                "stderr": "",
                "stdout": self._make_ls_remote_output(["1.0.0", "1.5.0"]),
            },
        )()
        with self.assertRaises(SystemExit) as ctx:
            resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        msg = str(ctx.exception)
        self.assertIn("No catalog tags >= 2.0.0", msg)
        self.assertIn("https://example.com/repo.git", msg)

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_empty_output_raises_system_exit(self, mock_run):
        mock_run.return_value = type("Result", (), {"returncode": 0, "stderr": "", "stdout": ""})()
        with self.assertRaises(SystemExit) as ctx:
            resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        msg = str(ctx.exception)
        self.assertIn("No catalog tags >= 2.0.0", msg)

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_git_failure_raises_system_exit(self, mock_run):
        mock_run.return_value = type(
            "Result",
            (),
            {"returncode": 128, "stderr": "fatal: repository not found", "stdout": ""},
        )()
        with self.assertRaises(SystemExit) as ctx:
            resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        msg = str(ctx.exception)
        self.assertIn("Failed to query tags", msg)
        self.assertIn("https://example.com/repo.git", msg)
        self.assertIn("fatal: repository not found", msg)

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_git_failure_no_stderr(self, mock_run):
        mock_run.return_value = type("Result", (), {"returncode": 1, "stderr": "", "stdout": ""})()
        with self.assertRaises(SystemExit) as ctx:
            resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        msg = str(ctx.exception)
        self.assertIn("Failed to query tags", msg)
        self.assertNotIn(": ", msg.split("Failed to query tags")[1][:2])

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_semver_sorting_across_major_minor_patch(self, mock_run):
        tags = ["2.0.0", "3.0.0", "2.10.0", "2.9.0", "2.1.0", "10.0.0"]
        mock_run.return_value = type(
            "Result",
            (),
            {
                "returncode": 0,
                "stderr": "",
                "stdout": self._make_ls_remote_output(tags),
            },
        )()
        result = resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        self.assertEqual(result, "10.0.0")

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_malformed_lines_ignored(self, mock_run):
        stdout = "malformed line\nabc123\trefs/tags/2.0.0\n\n"
        mock_run.return_value = type("Result", (), {"returncode": 0, "stderr": "", "stdout": stdout})()
        result = resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        self.assertEqual(result, "2.0.0")

    @patch("caylent_devcontainer_cli.utils.catalog.subprocess.run")
    def test_calls_git_ls_remote_with_correct_args(self, mock_run):
        mock_run.return_value = type(
            "Result",
            (),
            {
                "returncode": 0,
                "stderr": "",
                "stdout": self._make_ls_remote_output(["2.0.0"]),
            },
        )()
        resolve_latest_catalog_tag("https://example.com/repo.git", "2.0.0")
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd, ["git", "ls-remote", "--tags", "https://example.com/repo.git"])


class TestResolveDefaultCatalogUrl(TestCase):
    """Test resolve_default_catalog_url() returns URL with tag suffix."""

    @patch("caylent_devcontainer_cli.utils.catalog.resolve_latest_catalog_tag")
    def test_returns_url_with_tag(self, mock_resolve):
        mock_resolve.return_value = "2.1.0"
        result = resolve_default_catalog_url()
        self.assertEqual(result, f"{DEFAULT_CATALOG_URL}@2.1.0")

    @patch("caylent_devcontainer_cli.utils.catalog.resolve_latest_catalog_tag")
    def test_calls_resolve_with_correct_args(self, mock_resolve):
        mock_resolve.return_value = "2.0.0"
        resolve_default_catalog_url()
        mock_resolve.assert_called_once_with(DEFAULT_CATALOG_URL, MIN_CATALOG_TAG_VERSION)

    @patch("caylent_devcontainer_cli.utils.catalog.resolve_latest_catalog_tag")
    def test_propagates_system_exit(self, mock_resolve):
        mock_resolve.side_effect = SystemExit("No catalog tags >= 2.0.0 found")
        with self.assertRaises(SystemExit):
            resolve_default_catalog_url()


class TestCopyRootAssetsToProject(TestCase):
    """Test copy_root_assets_to_project() file copying to project root."""

    def test_copies_files_to_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root_assets = os.path.join(tmp, "root-assets")
            project = os.path.join(tmp, "project")
            os.makedirs(root_assets)
            os.makedirs(project)

            with open(os.path.join(root_assets, "CLAUDE.md"), "w") as f:
                f.write("# Standards")

            copy_root_assets_to_project(root_assets, project)

            copied = os.path.join(project, "CLAUDE.md")
            self.assertTrue(os.path.isfile(copied))
            with open(copied) as f:
                self.assertEqual(f.read(), "# Standards")

    def test_copies_directories_to_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root_assets = os.path.join(tmp, "root-assets")
            project = os.path.join(tmp, "project")
            os.makedirs(os.path.join(root_assets, ".claude"))
            os.makedirs(project)

            with open(os.path.join(root_assets, ".claude", "settings.json"), "w") as f:
                json.dump({"permissions": {"allow": []}}, f)

            copy_root_assets_to_project(root_assets, project)

            copied = os.path.join(project, ".claude", "settings.json")
            self.assertTrue(os.path.isfile(copied))
            with open(copied) as f:
                data = json.load(f)
            self.assertIn("permissions", data)

    def test_overwrites_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root_assets = os.path.join(tmp, "root-assets")
            project = os.path.join(tmp, "project")
            os.makedirs(root_assets)
            os.makedirs(project)

            with open(os.path.join(project, "CLAUDE.md"), "w") as f:
                f.write("old content")
            with open(os.path.join(root_assets, "CLAUDE.md"), "w") as f:
                f.write("new content")

            copy_root_assets_to_project(root_assets, project)

            with open(os.path.join(project, "CLAUDE.md")) as f:
                self.assertEqual(f.read(), "new content")

    def test_skips_when_directory_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = os.path.join(tmp, "project")
            os.makedirs(project)

            # Should not raise when root_assets_path does not exist
            copy_root_assets_to_project(os.path.join(tmp, "nonexistent"), project)

            # Project should be unmodified
            self.assertEqual(os.listdir(project), [])

    def test_preserves_other_project_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root_assets = os.path.join(tmp, "root-assets")
            project = os.path.join(tmp, "project")
            os.makedirs(root_assets)
            os.makedirs(project)

            # Existing project file
            with open(os.path.join(project, "README.md"), "w") as f:
                f.write("# My Project")

            # Root asset
            with open(os.path.join(root_assets, "CLAUDE.md"), "w") as f:
                f.write("# Standards")

            copy_root_assets_to_project(root_assets, project)

            # Both files should exist
            self.assertTrue(os.path.isfile(os.path.join(project, "README.md")))
            self.assertTrue(os.path.isfile(os.path.join(project, "CLAUDE.md")))
            with open(os.path.join(project, "README.md")) as f:
                self.assertEqual(f.read(), "# My Project")

    def test_merges_into_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root_assets = os.path.join(tmp, "root-assets")
            project = os.path.join(tmp, "project")
            os.makedirs(os.path.join(root_assets, ".claude"))
            os.makedirs(os.path.join(project, ".claude"))

            # Existing file in project .claude/
            with open(os.path.join(project, ".claude", "existing.json"), "w") as f:
                json.dump({"existing": True}, f)

            # New file from root assets
            with open(os.path.join(root_assets, ".claude", "settings.json"), "w") as f:
                json.dump({"new": True}, f)

            copy_root_assets_to_project(root_assets, project)

            # Both files should exist in .claude/
            self.assertTrue(os.path.isfile(os.path.join(project, ".claude", "existing.json")))
            self.assertTrue(os.path.isfile(os.path.join(project, ".claude", "settings.json")))


class TestValidateCommonAssetsRootAssets(TestCase):
    """Test validate_common_assets() with root-project-assets."""

    def test_root_assets_file_instead_of_dir_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)

            root_assets_path = os.path.join(tmp, "common", "root-project-assets")
            with open(root_assets_path, "w") as f:
                f.write("not a directory")

            errors = validate_common_assets(tmp)
            self.assertTrue(any("root-project-assets" in e and "not a directory" in e for e in errors))

    def test_no_root_assets_dir_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)

            errors = validate_common_assets(tmp)
            self.assertEqual(errors, [])


class TestValidateVersionFile(TestCase):
    """Test VERSION file content validation."""

    def test_valid_semver(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "VERSION"), "w") as f:
                f.write("1.0.0")
            errors = validate_version_file(tmp)
            self.assertEqual(errors, [])

    def test_valid_semver_with_whitespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "VERSION"), "w") as f:
                f.write("  2.1.3  \n")
            errors = validate_version_file(tmp)
            self.assertEqual(errors, [])

    def test_invalid_format_v_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "VERSION"), "w") as f:
                f.write("v1.0.0")
            errors = validate_version_file(tmp)
            self.assertTrue(any("semver" in e for e in errors))

    def test_invalid_format_two_parts(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "VERSION"), "w") as f:
                f.write("1.0")
            errors = validate_version_file(tmp)
            self.assertTrue(any("semver" in e for e in errors))

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "VERSION"), "w") as f:
                f.write("")
            errors = validate_version_file(tmp)
            self.assertTrue(any("empty" in e for e in errors))

    def test_missing_file_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = validate_version_file(tmp)
            self.assertEqual(errors, [])

    def test_invalid_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "VERSION"), "w") as f:
                f.write("latest")
            errors = validate_version_file(tmp)
            self.assertTrue(any("semver" in e for e in errors))


class TestValidateDevcontainerJson(TestCase):
    """Test devcontainer.json structural validation."""

    def test_valid_with_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {
                "name": "test-container",
                "image": "mcr.microsoft.com/devcontainers/base:noble",
                "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
            }
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_devcontainer_json(path)
            self.assertEqual(errors, [])

    def test_valid_with_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {
                "name": "test-container",
                "build": {"dockerfile": "Dockerfile"},
                "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
            }
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_devcontainer_json(path)
            self.assertEqual(errors, [])

    def test_valid_with_docker_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {
                "name": "test-container",
                "dockerFile": "Dockerfile",
                "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
            }
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_devcontainer_json(path)
            self.assertEqual(errors, [])

    def test_valid_with_docker_compose_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {
                "name": "test-container",
                "dockerComposeFile": "docker-compose.yml",
                "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
            }
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_devcontainer_json(path)
            self.assertEqual(errors, [])

    def test_missing_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {
                "image": "mcr.microsoft.com/devcontainers/base:noble",
                "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
            }
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_devcontainer_json(path)
            self.assertTrue(any("'name' is required" in e for e in errors))

    def test_empty_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {
                "name": "",
                "image": "mcr.microsoft.com/devcontainers/base:noble",
                "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
            }
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_devcontainer_json(path)
            self.assertTrue(any("'name' is required" in e for e in errors))

    def test_missing_container_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {
                "name": "test-container",
                "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
            }
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_devcontainer_json(path)
            self.assertTrue(any("container source" in e for e in errors))

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            with open(path, "w") as f:
                f.write("not json")
            errors = validate_devcontainer_json(path)
            self.assertTrue(any("parse" in e.lower() for e in errors))

    def test_file_not_found(self):
        errors = validate_devcontainer_json("/nonexistent/devcontainer.json")
        self.assertTrue(any("not found" in e for e in errors))

    def test_delegates_postcreate_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "devcontainer.json")
            config = {
                "name": "test-container",
                "image": "mcr.microsoft.com/devcontainers/base:noble",
                "postCreateCommand": "echo hello",
            }
            with open(path, "w") as f:
                json.dump(config, f)
            errors = validate_devcontainer_json(path)
            self.assertTrue(any("postcreate" in e for e in errors))


class TestValidateCatalogEntryUnknownFields(TestCase):
    """Test unknown field detection in catalog-entry.json."""

    def test_unknown_field_detected(self):
        data = {
            "name": "test-app",
            "description": "Test",
            "unknown_field": "value",
        }
        errors = validate_catalog_entry(data)
        self.assertTrue(any("Unknown fields" in e for e in errors))
        self.assertTrue(any("unknown_field" in e for e in errors))

    def test_multiple_unknown_fields(self):
        data = {
            "name": "test-app",
            "description": "Test",
            "foo": 1,
            "bar": 2,
        }
        errors = validate_catalog_entry(data)
        self.assertTrue(any("Unknown fields" in e for e in errors))
        self.assertTrue(any("bar" in e and "foo" in e for e in errors))

    def test_all_known_fields_pass(self):
        data = {
            "name": "test-app",
            "description": "Test",
            "tags": ["test"],
            "maintainer": "team",
            "min_cli_version": "2.0.0",
        }
        errors = validate_catalog_entry(data)
        self.assertEqual(errors, [])


class TestValidateEntryExtended(TestCase):
    """Test extended entry validation (VERSION, dir/name, devcontainer.json)."""

    def test_invalid_version_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_dir = os.path.join(tmp, "test-app")
            os.makedirs(entry_dir)
            entry = {"name": "test-app", "description": "Test"}
            with open(os.path.join(entry_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(entry, f)
            devcontainer = {
                "name": "caylent-devcontainer",
                "image": "mcr.microsoft.com/devcontainers/base:noble",
                "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
            }
            with open(os.path.join(entry_dir, "devcontainer.json"), "w") as f:
                json.dump(devcontainer, f)
            with open(os.path.join(entry_dir, CATALOG_VERSION_FILENAME), "w") as f:
                f.write("not-semver")
            errors = validate_entry(entry_dir)
            self.assertTrue(any("semver" in e for e in errors))

    def test_directory_name_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry_dir = os.path.join(tmp, "wrong-dir-name")
            os.makedirs(entry_dir)
            entry = {"name": "correct-name", "description": "Test"}
            with open(os.path.join(entry_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(entry, f)
            devcontainer = {
                "name": "caylent-devcontainer",
                "image": "mcr.microsoft.com/devcontainers/base:noble",
                "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
            }
            with open(os.path.join(entry_dir, "devcontainer.json"), "w") as f:
                json.dump(devcontainer, f)
            with open(os.path.join(entry_dir, CATALOG_VERSION_FILENAME), "w") as f:
                f.write("1.0.0")
            errors = validate_entry(entry_dir)
            self.assertTrue(any("does not match" in e for e in errors))

    def test_subdirectory_conflict_with_common_assets_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Create common assets dir with a subdirectory
            common_dir = os.path.join(tmp, "common")
            os.makedirs(common_dir)
            with open(os.path.join(common_dir, "script.sh"), "w") as f:
                f.write("")
            os.makedirs(os.path.join(common_dir, "nix-family-os"))

            # Create entry that has a conflicting subdirectory
            entry_dir = os.path.join(tmp, "test-app")
            os.makedirs(entry_dir)
            entry = {"name": "test-app", "description": "Test"}
            with open(os.path.join(entry_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(entry, f)
            devcontainer = {
                "name": "caylent-devcontainer",
                "image": "mcr.microsoft.com/devcontainers/base:noble",
                "postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode",
            }
            with open(os.path.join(entry_dir, "devcontainer.json"), "w") as f:
                json.dump(devcontainer, f)
            with open(os.path.join(entry_dir, CATALOG_VERSION_FILENAME), "w") as f:
                f.write("1.0.0")
            # Add conflicting subdir
            os.makedirs(os.path.join(entry_dir, "nix-family-os"))

            errors = validate_entry(entry_dir, common_assets_dir=common_dir)
            self.assertTrue(any("nix-family-os" in e and "conflicts" in e for e in errors))


class TestValidateCommonAssetsExtended(TestCase):
    """Test extended common assets validation (subdirs, permissions, JSON)."""

    def test_missing_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)
            # Remove one subdirectory
            import shutil

            shutil.rmtree(os.path.join(assets_dir, "nix-family-os"))
            errors = validate_common_assets(tmp)
            self.assertTrue(any("nix-family-os" in e and "Missing" in e for e in errors))

    def test_missing_subdir_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)
            # Remove a required file from a subdirectory
            os.remove(os.path.join(assets_dir, "nix-family-os", "tinyproxy.conf.template"))
            errors = validate_common_assets(tmp)
            self.assertTrue(any("tinyproxy.conf.template" in e for e in errors))

    def test_non_executable_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)
            # Remove executable bit from a script
            os.chmod(os.path.join(assets_dir, ".devcontainer.postcreate.sh"), 0o644)
            errors = validate_common_assets(tmp)
            self.assertTrue(any("executable" in e and ".devcontainer.postcreate.sh" in e for e in errors))

    def test_non_executable_subdir_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)
            # Remove executable bit from subdir script
            os.chmod(os.path.join(assets_dir, "nix-family-os", "tinyproxy-daemon.sh"), 0o644)
            errors = validate_common_assets(tmp)
            self.assertTrue(any("executable" in e and "tinyproxy-daemon.sh" in e for e in errors))

    def test_root_project_assets_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)
            # Create root-project-assets with invalid JSON
            root_assets = os.path.join(tmp, "common", "root-project-assets", ".claude")
            os.makedirs(root_assets)
            with open(os.path.join(root_assets, "settings.json"), "w") as f:
                f.write("not valid json")
            errors = validate_common_assets(tmp)
            self.assertTrue(any("Invalid JSON" in e and "settings.json" in e for e in errors))

    def test_root_project_assets_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            _create_valid_common_assets(assets_dir)
            # Create root-project-assets with valid JSON
            root_assets = os.path.join(tmp, "common", "root-project-assets", ".claude")
            os.makedirs(root_assets)
            with open(os.path.join(root_assets, "settings.json"), "w") as f:
                json.dump({"permissions": {}}, f)
            errors = validate_common_assets(tmp)
            self.assertEqual(errors, [])


class TestNewConstants(TestCase):
    """Verify new catalog constants are properly defined."""

    def test_semver_pattern_matches_valid(self):
        self.assertIsNotNone(SEMVER_PATTERN.match("1.0.0"))
        self.assertIsNotNone(SEMVER_PATTERN.match("10.20.30"))

    def test_semver_pattern_rejects_invalid(self):
        self.assertIsNone(SEMVER_PATTERN.match("v1.0.0"))
        self.assertIsNone(SEMVER_PATTERN.match("1.0"))
        self.assertIsNone(SEMVER_PATTERN.match(""))

    def test_common_subdirs_defined(self):
        self.assertIn("nix-family-os", CATALOG_COMMON_SUBDIRS)
        self.assertIn("wsl-family-os", CATALOG_COMMON_SUBDIRS)

    def test_container_source_fields_defined(self):
        self.assertIn("image", DEVCONTAINER_CONTAINER_SOURCE_FIELDS)
        self.assertIn("build", DEVCONTAINER_CONTAINER_SOURCE_FIELDS)

    def test_entry_allowed_fields_defined(self):
        self.assertIn("name", CATALOG_ENTRY_ALLOWED_FIELDS)
        self.assertIn("description", CATALOG_ENTRY_ALLOWED_FIELDS)
        self.assertIn("tags", CATALOG_ENTRY_ALLOWED_FIELDS)
        self.assertIn("maintainer", CATALOG_ENTRY_ALLOWED_FIELDS)
        self.assertIn("min_cli_version", CATALOG_ENTRY_ALLOWED_FIELDS)
