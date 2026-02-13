"""Catalog data model and validation for devcontainer catalog repositories.

A catalog repo contains shared devcontainer assets and one or more collections.
Each collection provides a complete devcontainer configuration (devcontainer.json,
catalog-entry.json, VERSION, and optional extra files).

Layout:
    catalog-repo/
      common/devcontainer-assets/   (shared postcreate, functions, project-setup)
      collections/<name>/           (one or more collections)
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ASSETS_DIR,
    CATALOG_COLLECTIONS_DIR,
    CATALOG_COMMON_DIR,
    CATALOG_ENTRY_FILENAME,
    CATALOG_NAME_PATTERN,
    CATALOG_REQUIRED_COLLECTION_FILES,
    CATALOG_REQUIRED_COMMON_ASSETS,
    CATALOG_TAG_PATTERN,
)


@dataclass
class CatalogEntry:
    """Represents the contents of a catalog-entry.json file."""

    name: str
    description: str
    tags: List[str] = field(default_factory=list)
    maintainer: Optional[str] = None
    min_cli_version: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CatalogEntry":
        """Create a CatalogEntry from a dictionary (parsed JSON)."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            maintainer=data.get("maintainer"),
            min_cli_version=data.get("min_cli_version"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
        }
        if self.tags:
            result["tags"] = self.tags
        if self.maintainer is not None:
            result["maintainer"] = self.maintainer
        if self.min_cli_version is not None:
            result["min_cli_version"] = self.min_cli_version
        return result


def validate_catalog_entry(data: Dict[str, Any]) -> List[str]:
    """Validate a catalog-entry.json dictionary and return a list of errors.

    Returns an empty list if validation passes.
    """
    errors: List[str] = []

    # Required fields
    if "name" not in data or not isinstance(data["name"], str) or not data["name"]:
        errors.append("'name' is required and must be a non-empty string")
    elif not CATALOG_NAME_PATTERN.match(data["name"]):
        errors.append(
            f"'name' must be lowercase, dash-separated, min 2 chars "
            f"(pattern: {CATALOG_NAME_PATTERN.pattern}). Got: '{data['name']}'"
        )

    if "description" not in data or not isinstance(data["description"], str) or not data["description"]:
        errors.append("'description' is required and must be a non-empty string")

    # Optional: tags
    if "tags" in data:
        if not isinstance(data["tags"], list):
            errors.append("'tags' must be an array of strings")
        else:
            for i, tag in enumerate(data["tags"]):
                if not isinstance(tag, str):
                    errors.append(f"tags[{i}] must be a string")
                elif not CATALOG_TAG_PATTERN.match(tag):
                    errors.append(
                        f"tags[{i}] must be lowercase, dash-separated "
                        f"(pattern: {CATALOG_TAG_PATTERN.pattern}). Got: '{tag}'"
                    )

    # Optional: maintainer
    if "maintainer" in data:
        if not isinstance(data["maintainer"], str) or not data["maintainer"]:
            errors.append("'maintainer' must be a non-empty string when provided")

    # Optional: min_cli_version (semver)
    if "min_cli_version" in data:
        version = data["min_cli_version"]
        if not isinstance(version, str):
            errors.append("'min_cli_version' must be a string")
        elif not re.match(r"^\d+\.\d+\.\d+$", version):
            errors.append(f"'min_cli_version' must be semver (X.Y.Z). Got: '{version}'")

    return errors


def validate_collection_structure(collection_path: str) -> List[str]:
    """Validate that a collection directory has all required files.

    Returns a list of errors (empty if valid).
    """
    errors: List[str] = []

    for filename in CATALOG_REQUIRED_COLLECTION_FILES:
        filepath = os.path.join(collection_path, filename)
        if not os.path.isfile(filepath):
            errors.append(f"Missing required file: {filename}")

    return errors


def detect_file_conflicts(collection_path: str, common_assets: Tuple[str, ...]) -> List[str]:
    """Detect files in a collection that conflict with common/devcontainer-assets/.

    Collections must NOT contain files with the same name as files in
    common/devcontainer-assets/ to prevent overwrites during copy.

    Returns a list of conflicting filenames.
    """
    conflicts: List[str] = []

    if not os.path.isdir(collection_path):
        return conflicts

    collection_files = set(os.listdir(collection_path))
    for asset_name in common_assets:
        if asset_name in collection_files:
            conflicts.append(asset_name)

    return conflicts


def validate_postcreate_command(devcontainer_json_path: str) -> List[str]:
    """Validate that devcontainer.json's postCreateCommand calls the postcreate script.

    Returns a list of errors (empty if valid).
    """
    errors: List[str] = []

    if not os.path.isfile(devcontainer_json_path):
        errors.append(f"devcontainer.json not found at {devcontainer_json_path}")
        return errors

    try:
        with open(devcontainer_json_path) as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        errors.append(f"Failed to parse devcontainer.json: {e}")
        return errors

    post_create = config.get("postCreateCommand", "")
    if isinstance(post_create, str):
        if ".devcontainer.postcreate.sh" not in post_create:
            errors.append("postCreateCommand must call .devcontainer/.devcontainer.postcreate.sh")
    elif isinstance(post_create, list):
        joined = " ".join(str(item) for item in post_create)
        if ".devcontainer.postcreate.sh" not in joined:
            errors.append("postCreateCommand must call .devcontainer/.devcontainer.postcreate.sh")
    else:
        errors.append("postCreateCommand must be a string or array")

    return errors


def validate_collection(collection_path: str) -> List[str]:
    """Run all validations on a single collection directory.

    Validates structure, catalog-entry.json content, file conflicts,
    and postCreateCommand.

    Returns a list of all errors found.
    """
    errors: List[str] = []

    # 1. Structure validation
    errors.extend(validate_collection_structure(collection_path))

    # 2. catalog-entry.json content validation
    entry_path = os.path.join(collection_path, CATALOG_ENTRY_FILENAME)
    if os.path.isfile(entry_path):
        try:
            with open(entry_path) as f:
                entry_data = json.load(f)
            errors.extend(validate_catalog_entry(entry_data))
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {CATALOG_ENTRY_FILENAME}: {e}")
        except OSError as e:
            errors.append(f"Cannot read {CATALOG_ENTRY_FILENAME}: {e}")

    # 3. File conflict detection
    conflicts = detect_file_conflicts(collection_path, CATALOG_REQUIRED_COMMON_ASSETS)
    for conflict in conflicts:
        errors.append(
            f"Collection contains '{conflict}' which conflicts with " f"common/{CATALOG_ASSETS_DIR}/{conflict}"
        )

    # 4. postCreateCommand validation
    devcontainer_json = os.path.join(collection_path, "devcontainer.json")
    if os.path.isfile(devcontainer_json):
        errors.extend(validate_postcreate_command(devcontainer_json))

    return errors


def validate_common_assets(catalog_root: str) -> List[str]:
    """Validate that the catalog has the required common/devcontainer-assets/ directory.

    Returns a list of errors (empty if valid).
    """
    errors: List[str] = []
    assets_dir = os.path.join(catalog_root, CATALOG_COMMON_DIR, CATALOG_ASSETS_DIR)

    if not os.path.isdir(assets_dir):
        errors.append(f"Missing required directory: {CATALOG_COMMON_DIR}/{CATALOG_ASSETS_DIR}/")
        return errors

    for filename in CATALOG_REQUIRED_COMMON_ASSETS:
        filepath = os.path.join(assets_dir, filename)
        if not os.path.isfile(filepath):
            errors.append(f"Missing required common asset: {CATALOG_COMMON_DIR}/{CATALOG_ASSETS_DIR}/{filename}")

    return errors


def discover_collections(catalog_root: str) -> List[str]:
    """Recursively discover collections by scanning for catalog-entry.json files.

    Returns a list of absolute directory paths containing catalog-entry.json.
    """
    collections: List[str] = []
    collections_dir = os.path.join(catalog_root, CATALOG_COLLECTIONS_DIR)

    if not os.path.isdir(collections_dir):
        return collections

    for dirpath, _dirnames, filenames in os.walk(collections_dir):
        if CATALOG_ENTRY_FILENAME in filenames:
            collections.append(dirpath)

    return sorted(collections)


def validate_catalog(catalog_root: str) -> List[str]:
    """Validate an entire catalog repository.

    Checks common assets, discovers collections, validates each collection,
    and checks for duplicate collection names.

    Returns a list of all errors found.
    """
    errors: List[str] = []

    # 1. Validate common assets
    errors.extend(validate_common_assets(catalog_root))

    # 2. Discover and validate collections
    collections = discover_collections(catalog_root)
    if not collections:
        errors.append(
            f"No collections found. Expected {CATALOG_ENTRY_FILENAME} " f"files under {CATALOG_COLLECTIONS_DIR}/"
        )
        return errors

    # 3. Validate each collection and check name uniqueness
    seen_names: Dict[str, str] = {}
    for collection_path in collections:
        collection_errors = validate_collection(collection_path)
        rel_path = os.path.relpath(collection_path, catalog_root)
        for error in collection_errors:
            errors.append(f"[{rel_path}] {error}")

        # Check name uniqueness
        entry_path = os.path.join(collection_path, CATALOG_ENTRY_FILENAME)
        if os.path.isfile(entry_path):
            try:
                with open(entry_path) as f:
                    entry_data = json.load(f)
                name = entry_data.get("name", "")
                if name and name in seen_names:
                    errors.append(f"Duplicate collection name '{name}': " f"found in {rel_path} and {seen_names[name]}")
                elif name:
                    seen_names[name] = rel_path
            except (json.JSONDecodeError, OSError):
                pass  # Already reported by validate_collection

    return errors
