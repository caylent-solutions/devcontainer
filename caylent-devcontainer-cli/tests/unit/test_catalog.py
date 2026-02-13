"""Unit tests for catalog data model and validation."""

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
    CATALOG_ENTRY_FILENAME,
    CATALOG_NAME_PATTERN,
    CATALOG_REQUIRED_COLLECTION_FILES,
    CATALOG_REQUIRED_COMMON_ASSETS,
    CATALOG_TAG_PATTERN,
    CATALOG_VERSION_FILENAME,
)


class TestCatalogEntry(TestCase):
    """Test CatalogEntry dataclass."""

    def test_from_dict_all_fields(self):
        data = {
            "name": "my-collection",
            "description": "A test collection",
            "tags": ["java", "spring-boot"],
            "maintainer": "team-a",
            "min_cli_version": "2.0.0",
        }
        entry = CatalogEntry.from_dict(data)
        self.assertEqual(entry.name, "my-collection")
        self.assertEqual(entry.description, "A test collection")
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


class TestValidateCollectionStructure(TestCase):
    """Test collection directory structure validation."""

    def test_valid_collection(self, tmp_path=None):
        if tmp_path is None:
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                self._run_valid_test(tmp)
        else:
            self._run_valid_test(str(tmp_path))

    def _run_valid_test(self, tmp_dir):
        for filename in CATALOG_REQUIRED_COLLECTION_FILES:
            with open(os.path.join(tmp_dir, filename), "w") as f:
                f.write("{}" if filename.endswith(".json") else "1.0.0")
        errors = validate_collection_structure(tmp_dir)
        self.assertEqual(errors, [])

    def test_missing_all_files(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            errors = validate_collection_structure(tmp)
            self.assertEqual(len(errors), len(CATALOG_REQUIRED_COLLECTION_FILES))

    def test_missing_one_file(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            # Create all but VERSION
            for filename in CATALOG_REQUIRED_COLLECTION_FILES:
                if filename != CATALOG_VERSION_FILENAME:
                    with open(os.path.join(tmp, filename), "w") as f:
                        f.write("{}")
            errors = validate_collection_structure(tmp)
            self.assertEqual(len(errors), 1)
            self.assertIn("VERSION", errors[0])


class TestDetectFileConflicts(TestCase):
    """Test file conflict detection between collection and common assets."""

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
            config = {"postCreateCommand": ["bash", ".devcontainer/.devcontainer.postcreate.sh"]}
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


class TestDiscoverCollections(TestCase):
    """Test collection discovery."""

    def test_discovers_collections(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            col1 = os.path.join(tmp, "collections", "app-a")
            col2 = os.path.join(tmp, "collections", "app-b")
            os.makedirs(col1)
            os.makedirs(col2)
            with open(os.path.join(col1, CATALOG_ENTRY_FILENAME), "w") as f:
                f.write("{}")
            with open(os.path.join(col2, CATALOG_ENTRY_FILENAME), "w") as f:
                f.write("{}")
            result = discover_collections(tmp)
            self.assertEqual(len(result), 2)

    def test_discovers_nested_collections(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            nested = os.path.join(tmp, "collections", "group", "subgroup", "app")
            os.makedirs(nested)
            with open(os.path.join(nested, CATALOG_ENTRY_FILENAME), "w") as f:
                f.write("{}")
            result = discover_collections(tmp)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0], nested)

    def test_no_collections_dir(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result = discover_collections(tmp)
            self.assertEqual(result, [])

    def test_empty_collections_dir(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "collections"))
            result = discover_collections(tmp)
            self.assertEqual(result, [])

    def test_results_sorted(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            for name in ["zebra", "alpha", "middle"]:
                col = os.path.join(tmp, "collections", name)
                os.makedirs(col)
                with open(os.path.join(col, CATALOG_ENTRY_FILENAME), "w") as f:
                    f.write("{}")
            result = discover_collections(tmp)
            basenames = [os.path.basename(p) for p in result]
            self.assertEqual(basenames, ["alpha", "middle", "zebra"])


class TestValidateCommonAssets(TestCase):
    """Test common assets directory validation."""

    def test_valid_common_assets(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            os.makedirs(assets_dir)
            for filename in CATALOG_REQUIRED_COMMON_ASSETS:
                with open(os.path.join(assets_dir, filename), "w") as f:
                    f.write("#!/bin/bash")
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
            os.makedirs(assets_dir)
            # Create all but project-setup.sh
            for filename in CATALOG_REQUIRED_COMMON_ASSETS:
                if filename != "project-setup.sh":
                    with open(os.path.join(assets_dir, filename), "w") as f:
                        f.write("")
            errors = validate_common_assets(tmp)
            self.assertEqual(len(errors), 1)
            self.assertIn("project-setup.sh", errors[0])


class TestValidateCollection(TestCase):
    """Test full collection validation."""

    def _create_valid_collection(self, tmp_dir):
        """Create a minimal valid collection in tmp_dir."""
        entry = {"name": "test-app", "description": "Test application"}
        with open(os.path.join(tmp_dir, CATALOG_ENTRY_FILENAME), "w") as f:
            json.dump(entry, f)
        devcontainer = {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode"}
        with open(os.path.join(tmp_dir, "devcontainer.json"), "w") as f:
            json.dump(devcontainer, f)
        with open(os.path.join(tmp_dir, CATALOG_VERSION_FILENAME), "w") as f:
            f.write("1.0.0")

    def test_valid_collection(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_collection(tmp)
            errors = validate_collection(tmp)
            self.assertEqual(errors, [])

    def test_invalid_entry_json(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_collection(tmp)
            # Overwrite with invalid entry
            with open(os.path.join(tmp, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump({"name": "A"}, f)  # uppercase, no description
            errors = validate_collection(tmp)
            self.assertTrue(len(errors) >= 2)  # name pattern + missing description

    def test_conflict_with_common_assets(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_collection(tmp)
            with open(os.path.join(tmp, "devcontainer-functions.sh"), "w") as f:
                f.write("")
            errors = validate_collection(tmp)
            self.assertTrue(any("conflicts with" in e for e in errors))

    def test_broken_json_in_entry(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_collection(tmp)
            with open(os.path.join(tmp, CATALOG_ENTRY_FILENAME), "w") as f:
                f.write("not json")
            errors = validate_collection(tmp)
            self.assertTrue(any("Invalid JSON" in e for e in errors))


class TestValidateCatalog(TestCase):
    """Test full catalog validation."""

    def _create_valid_catalog(self, tmp_dir):
        """Create a minimal valid catalog structure."""
        # Common assets
        assets_dir = os.path.join(tmp_dir, "common", "devcontainer-assets")
        os.makedirs(assets_dir)
        for filename in CATALOG_REQUIRED_COMMON_ASSETS:
            with open(os.path.join(assets_dir, filename), "w") as f:
                f.write("#!/bin/bash")

        # One collection
        col_dir = os.path.join(tmp_dir, "collections", "default")
        os.makedirs(col_dir)
        entry = {"name": "default", "description": "Default collection"}
        with open(os.path.join(col_dir, CATALOG_ENTRY_FILENAME), "w") as f:
            json.dump(entry, f)
        devcontainer = {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh vscode"}
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
            # Only create collection, no common
            col_dir = os.path.join(tmp, "collections", "app")
            os.makedirs(col_dir)
            entry = {"name": "app", "description": "App"}
            with open(os.path.join(col_dir, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(entry, f)
            with open(os.path.join(col_dir, "devcontainer.json"), "w") as f:
                json.dump({"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh"}, f)
            with open(os.path.join(col_dir, CATALOG_VERSION_FILENAME), "w") as f:
                f.write("1.0.0")
            errors = validate_catalog(tmp)
            self.assertTrue(any("Missing required directory" in e for e in errors))

    def test_no_collections(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = os.path.join(tmp, "common", "devcontainer-assets")
            os.makedirs(assets_dir)
            for filename in CATALOG_REQUIRED_COMMON_ASSETS:
                with open(os.path.join(assets_dir, filename), "w") as f:
                    f.write("")
            errors = validate_catalog(tmp)
            self.assertTrue(any("No collections found" in e for e in errors))

    def test_duplicate_collection_names(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self._create_valid_catalog(tmp)
            # Add a second collection with same name
            col2 = os.path.join(tmp, "collections", "other")
            os.makedirs(col2)
            entry = {"name": "default", "description": "Duplicate name"}
            with open(os.path.join(col2, CATALOG_ENTRY_FILENAME), "w") as f:
                json.dump(entry, f)
            devcontainer = {"postCreateCommand": "bash .devcontainer/.devcontainer.postcreate.sh"}
            with open(os.path.join(col2, "devcontainer.json"), "w") as f:
                json.dump(devcontainer, f)
            with open(os.path.join(col2, CATALOG_VERSION_FILENAME), "w") as f:
                f.write("1.0.0")
            errors = validate_catalog(tmp)
            self.assertTrue(any("Duplicate collection name" in e for e in errors))


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

    def test_required_collection_files_defined(self):
        self.assertIn(CATALOG_ENTRY_FILENAME, CATALOG_REQUIRED_COLLECTION_FILES)
        self.assertIn("devcontainer.json", CATALOG_REQUIRED_COLLECTION_FILES)
        self.assertIn(CATALOG_VERSION_FILENAME, CATALOG_REQUIRED_COLLECTION_FILES)
