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
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ASSETS_DIR,
    CATALOG_COLLECTIONS_DIR,
    CATALOG_COMMON_DIR,
    CATALOG_ENTRY_FILENAME,
    CATALOG_NAME_PATTERN,
    CATALOG_REQUIRED_COLLECTION_FILES,
    CATALOG_REQUIRED_COMMON_ASSETS,
    CATALOG_TAG_PATTERN,
    DEFAULT_CATALOG_URL,
    MIN_CATALOG_TAG_VERSION,
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


@dataclass
class CollectionInfo:
    """A discovered collection with its path and parsed metadata."""

    path: str
    entry: CatalogEntry


def compare_semver(version_a: str, version_b: str) -> int:
    """Compare two semantic version strings.

    Args:
        version_a: First version (e.g. ``"2.1.0"``).
        version_b: Second version (e.g. ``"2.0.0"``).

    Returns:
        -1 if *version_a* < *version_b*, 0 if equal, 1 if greater.

    Raises:
        ValueError: If either version is not valid semver (X.Y.Z).
    """
    pattern = re.compile(r"^\d+\.\d+\.\d+$")
    if not pattern.match(version_a):
        raise ValueError(f"Invalid semver: '{version_a}'")
    if not pattern.match(version_b):
        raise ValueError(f"Invalid semver: '{version_b}'")

    parts_a = tuple(int(x) for x in version_a.split("."))
    parts_b = tuple(int(x) for x in version_b.split("."))

    if parts_a < parts_b:
        return -1
    if parts_a > parts_b:
        return 1
    return 0


def check_min_cli_version(min_version: str, current_version: Optional[str] = None) -> bool:
    """Check whether the current CLI version meets a minimum version requirement.

    Args:
        min_version: The required minimum version (semver string).
        current_version: Override for the current CLI version.  Defaults to
            ``caylent_devcontainer_cli.__version__``.

    Returns:
        ``True`` if the current version is greater than or equal to
        *min_version*.
    """
    if current_version is None:
        current_version = __version__
    return compare_semver(current_version, min_version) >= 0


def find_collection_by_name(entries: List[CollectionInfo], name: str) -> CollectionInfo:
    """Look up a collection by name from a list of discovered entries.

    Args:
        entries: The list of discovered :class:`CollectionInfo` objects.
        name: The collection name to search for.

    Returns:
        The matching :class:`CollectionInfo`.

    Raises:
        SystemExit: If no collection with *name* is found.
    """
    for entry_info in entries:
        if entry_info.entry.name == name:
            return entry_info
    raise SystemExit(
        f"Collection '{name}' not found. " "Run 'cdevcontainer catalog list' to see available collections."
    )


def validate_catalog_entry_env(catalog_entry_name: str) -> str:
    """Validate that DEVCONTAINER_CATALOG_URL is set when ``--catalog-entry`` is used.

    Args:
        catalog_entry_name: The collection name supplied via ``--catalog-entry``.

    Returns:
        The catalog URL from the environment variable.

    Raises:
        SystemExit: If DEVCONTAINER_CATALOG_URL is not set.
    """
    catalog_url = os.environ.get("DEVCONTAINER_CATALOG_URL")
    if not catalog_url:
        raise SystemExit(
            "DEVCONTAINER_CATALOG_URL is not set. " "The --catalog-entry flag requires a specialized catalog."
        )
    return catalog_url


def parse_catalog_url(url_with_ref: str) -> Tuple[str, Optional[str]]:
    """Parse a catalog URL with an optional @ref suffix.

    Format: ``<git-clone-url>[@<branch-or-tag>]``

    The ``.git`` suffix is the anchor for splitting.  When there is no
    ``.git``, the last ``@`` is used as the delimiter unless it is the
    SSH user prefix (``git@host:path``).

    Returns:
        (clone_url, ref) where *ref* is ``None`` when the default branch
        should be used.

    Raises:
        ValueError: If *url_with_ref* is empty.
    """
    if not url_with_ref:
        raise ValueError("Catalog URL must not be empty")

    git_idx = url_with_ref.rfind(".git")
    if git_idx != -1:
        after_git = url_with_ref[git_idx + 4 :]
        if after_git.startswith("@") and len(after_git) > 1:
            return (url_with_ref[: git_idx + 4], after_git[1:])
        # .git with nothing useful after it
        return (url_with_ref, None)

    # No .git suffix — split on the last @ if it is not the SSH prefix.
    last_at = url_with_ref.rfind("@")
    if last_at == -1:
        return (url_with_ref, None)

    # Determine whether this single @ is part of the SSH user prefix.
    at_count = url_with_ref.count("@")
    if at_count > 1:
        # Multiple @ — the last one delimits the ref.
        ref = url_with_ref[last_at + 1 :]
        return (url_with_ref[:last_at], ref if ref else None)

    # Single @.  SSH pattern: user@host:path  (colon after the @).
    after_at = url_with_ref[last_at + 1 :]
    if ":" in after_at:
        return (url_with_ref, None)

    ref = url_with_ref[last_at + 1 :]
    return (url_with_ref[:last_at], ref if ref else None)


def clone_catalog_repo(url_with_ref: str) -> str:
    """Clone a catalog repository to a temporary directory.

    Performs a shallow clone (``--depth 1``).  When a ref is specified in
    the URL the clone targets that branch/tag.

    Returns:
        The path to the cloned repository (a temporary directory).  The
        caller is responsible for cleaning it up.

    Raises:
        SystemExit: On clone failure with actionable error messages.
    """
    clone_url, ref = parse_catalog_url(url_with_ref)

    temp_dir = tempfile.mkdtemp(prefix="catalog-")

    cmd: List[str] = ["git", "clone", "--depth", "1"]
    if ref:
        cmd.extend(["--branch", ref])
    cmd.extend([clone_url, temp_dir])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        # Clean up on failure
        shutil.rmtree(temp_dir, ignore_errors=True)

        error_lines = [
            f"Failed to clone the devcontainer catalog from '{clone_url}'",
        ]
        if ref:
            error_lines[0] += f" (ref: {ref})"
        error_lines.extend(
            [
                "For HTTPS repos: verify a valid token or credential helper is configured.",
                "For SSH repos: verify your SSH key is loaded and the host is in known_hosts.",
                f"You can test access by running: git ls-remote {clone_url}",
            ]
        )
        stderr_snippet = result.stderr.strip()
        if stderr_snippet:
            error_lines.append(f"Git error: {stderr_snippet}")

        raise SystemExit("\n".join(error_lines))

    return temp_dir


def resolve_latest_catalog_tag(clone_url: str, min_version: str) -> str:
    """Resolve the latest semver tag >= *min_version* from a remote git repository.

    Runs ``git ls-remote --tags`` against *clone_url*, parses the output for
    valid semver tags, filters for those >= *min_version*, and returns the
    highest one.

    Args:
        clone_url: The git clone URL to query.
        min_version: Minimum semver version to consider (e.g. ``"2.0.0"``).

    Returns:
        The tag name of the latest compatible version (e.g. ``"2.1.0"``).

    Raises:
        SystemExit: If ``git ls-remote`` fails or no compatible tags are found.
    """
    cmd = ["git", "ls-remote", "--tags", clone_url]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        stderr_snippet = result.stderr.strip()
        raise SystemExit(f"Failed to query tags from '{clone_url}'" + (f": {stderr_snippet}" if stderr_snippet else ""))

    semver_pattern = re.compile(r"^\d+\.\d+\.\d+$")
    candidates: List[str] = []

    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        ref = parts[1]
        # Skip dereferenced annotated tag entries (e.g. refs/tags/2.0.0^{})
        if ref.endswith("^{}"):
            continue
        tag = ref.removeprefix("refs/tags/")
        if semver_pattern.match(tag) and compare_semver(tag, min_version) >= 0:
            candidates.append(tag)

    if not candidates:
        raise SystemExit(
            f"No catalog tags >= {min_version} found in '{clone_url}'. "
            "Ensure the catalog repository has semver tags (e.g. 2.0.0)."
        )

    candidates.sort(key=lambda t: tuple(int(x) for x in t.split(".")))
    return candidates[-1]


def resolve_default_catalog_url() -> str:
    """Resolve the default catalog URL with the latest compatible semver tag.

    Queries the default catalog repository for tags and returns the URL
    with an ``@tag`` suffix targeting the latest tag >= ``MIN_CATALOG_TAG_VERSION``.

    Returns:
        The default catalog URL with a tag ref (e.g.
        ``"https://github.com/caylent-solutions/devcontainer.git@2.1.0"``).

    Raises:
        SystemExit: If no compatible tags are found.
    """
    tag = resolve_latest_catalog_tag(DEFAULT_CATALOG_URL, MIN_CATALOG_TAG_VERSION)
    return f"{DEFAULT_CATALOG_URL}@{tag}"


def discover_collection_entries(
    catalog_root: str,
    skip_incomplete: bool = False,
) -> List[CollectionInfo]:
    """Discover collections and return them with parsed metadata.

    Scans for ``catalog-entry.json`` files, parses each one into a
    :class:`CatalogEntry`, and returns the list sorted with ``default``
    first followed by A-Z order of collection names.

    Args:
        catalog_root: Path to the catalog repository root.
        skip_incomplete: When ``True``, collections missing a
            ``devcontainer.json`` are silently skipped.  Useful for
            list/browse mode.  In validate mode this should be ``False``
            so that all collections are discovered and checked.
    """
    raw_paths = discover_collections(catalog_root)
    entries: List[CollectionInfo] = []

    for path in raw_paths:
        entry_path = os.path.join(path, CATALOG_ENTRY_FILENAME)
        if not os.path.isfile(entry_path):
            continue

        if skip_incomplete:
            devcontainer_path = os.path.join(path, "devcontainer.json")
            if not os.path.isfile(devcontainer_path):
                continue

        try:
            with open(entry_path) as f:
                data = json.load(f)
            entry = CatalogEntry.from_dict(data)
            entries.append(CollectionInfo(path=path, entry=entry))
        except (json.JSONDecodeError, OSError):
            continue

    # Sort: "default" first, then alphabetically by name.
    def _sort_key(info: CollectionInfo) -> Tuple[int, str]:
        return (0 if info.entry.name == "default" else 1, info.entry.name)

    entries.sort(key=_sort_key)
    return entries


def copy_collection_to_project(
    collection_path: str,
    common_assets_path: str,
    target_path: str,
    catalog_url: str,
) -> None:
    """Copy collection files and common assets into a project ``.devcontainer/``.

    1. Copies all files/dirs from *collection_path* to *target_path*.
    2. Copies all files/dirs from *common_assets_path* to *target_path*
       (common assets take precedence on name collisions).
    3. Augments the copied ``catalog-entry.json`` with *catalog_url*.
    4. Removes example files from *target_path*.
    """
    os.makedirs(target_path, exist_ok=True)

    # 1. Copy collection files
    for item in os.listdir(collection_path):
        src = os.path.join(collection_path, item)
        dst = os.path.join(target_path, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    # 2. Copy common assets (overwrites on collision)
    for item in os.listdir(common_assets_path):
        src = os.path.join(common_assets_path, item)
        dst = os.path.join(target_path, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    # 3. Augment catalog-entry.json with catalog_url
    entry_path = os.path.join(target_path, CATALOG_ENTRY_FILENAME)
    if os.path.isfile(entry_path):
        with open(entry_path) as f:
            entry_data = json.load(f)
        entry_data["catalog_url"] = catalog_url
        with open(entry_path, "w") as f:
            json.dump(entry_data, f, indent=2)
            f.write("\n")


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
