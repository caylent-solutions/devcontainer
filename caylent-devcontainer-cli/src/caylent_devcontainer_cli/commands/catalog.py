"""Catalog command for the Caylent Devcontainer CLI."""

import os
import shutil
import sys

from caylent_devcontainer_cli.utils.catalog import (
    check_min_cli_version,
    clone_catalog_repo,
    discover_entries,
    resolve_default_catalog_url,
    validate_catalog,
    validate_common_assets,
)
from caylent_devcontainer_cli.utils.ui import log

CATALOG_URL_ENV_VAR = "DEVCONTAINER_CATALOG_URL"


def _get_catalog_url():
    """Return the catalog URL from the environment or the default.

    Returns:
        Tuple of (url, source_label) where source_label describes
        the origin for display purposes.
    """
    env_url = os.environ.get(CATALOG_URL_ENV_VAR)
    if env_url:
        return (env_url, env_url)
    return (resolve_default_catalog_url(), "default catalog")


def register_command(subparsers):
    """Register the catalog command and its subcommands."""
    from caylent_devcontainer_cli.cli import _HelpFormatter, build_env_epilog

    catalog_parser = subparsers.add_parser(
        "catalog",
        help="Catalog management",
        formatter_class=_HelpFormatter,
        epilog=build_env_epilog("catalog"),
    )
    catalog_subparsers = catalog_parser.add_subparsers(dest="catalog_command")

    # 'catalog list' command
    list_parser = catalog_subparsers.add_parser("list", help="List available catalog entries")
    list_parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="Comma-separated tags to filter by (ANY match)",
    )
    list_parser.add_argument(
        "--catalog-url",
        type=str,
        default=None,
        metavar="URL",
        help="Override the catalog repository URL (bypasses tag resolution and DEVCONTAINER_CATALOG_URL)",
    )
    list_parser.set_defaults(func=handle_catalog_list)

    # 'catalog validate' command
    validate_parser = catalog_subparsers.add_parser("validate", help="Validate a catalog repository")
    validate_parser.add_argument(
        "--local",
        type=str,
        default=None,
        metavar="PATH",
        help="Validate a local catalog directory instead of cloning",
    )
    validate_parser.add_argument(
        "--catalog-url",
        type=str,
        default=None,
        metavar="URL",
        help="Override the catalog repository URL (bypasses tag resolution and DEVCONTAINER_CATALOG_URL)",
    )
    validate_parser.set_defaults(func=handle_catalog_validate)


def handle_catalog_list(args):
    """Handle the 'catalog list' command."""
    catalog_url_override = getattr(args, "catalog_url", None)
    if catalog_url_override:
        catalog_url, source_label = catalog_url_override, catalog_url_override
    else:
        catalog_url, source_label = _get_catalog_url()

    temp_dir = clone_catalog_repo(catalog_url)
    try:
        # Validate common assets exist
        asset_errors = validate_common_assets(temp_dir)
        if asset_errors:
            log(
                "ERR",
                "Catalog repo is missing required directory: common/devcontainer-assets/",
            )
            sys.exit(1)

        # Discover entries (skip incomplete ones missing devcontainer.json)
        entries = discover_entries(temp_dir, skip_incomplete=True)

        if not entries:
            log("ERR", "No devcontainer entries found in the catalog.")
            sys.exit(1)

        # Filter by min_cli_version — warn and skip incompatible entries
        compatible_entries = []
        for entry_info in entries:
            min_ver = entry_info.entry.min_cli_version
            if min_ver and not check_min_cli_version(min_ver):
                log(
                    "WARN",
                    f"Skipping '{entry_info.entry.name}': requires CLI version >= {min_ver}",
                )
                continue
            compatible_entries.append(entry_info)

        # Filter by tags if specified
        if args.tags:
            filter_tags = {t.strip() for t in args.tags.split(",") if t.strip()}
            compatible_entries = [e for e in compatible_entries if filter_tags & set(e.entry.tags)]
            if not compatible_entries:
                tags_str = ", ".join(sorted(filter_tags))
                log("INFO", f"No entries found matching tags: {tags_str}")
                return

        if not compatible_entries:
            log("INFO", "No compatible entries found in the catalog.")
            return

        # Display header
        print(f"\nAvailable DevContainer Configurations ({source_label}):\n")

        # Calculate column width for alignment
        max_name_len = max(len(e.entry.name) for e in compatible_entries)
        col_width = max(max_name_len + 4, 20)

        # Display each entry
        for entry_info in compatible_entries:
            name = entry_info.entry.name.ljust(col_width)
            print(f"  {name}{entry_info.entry.description}")

        print()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def handle_catalog_validate(args):
    """Handle the 'catalog validate' command."""
    if args.local:
        catalog_path = os.path.abspath(args.local)
        if not os.path.isdir(catalog_path):
            log("ERR", f"Directory not found: {catalog_path}")
            sys.exit(1)
        _run_validation(catalog_path)
    else:
        catalog_url_override = getattr(args, "catalog_url", None)
        if catalog_url_override:
            catalog_url = catalog_url_override
        else:
            catalog_url, _source_label = _get_catalog_url()
        temp_dir = clone_catalog_repo(catalog_url)
        try:
            _run_validation(temp_dir)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def _run_validation(catalog_path):
    """Run catalog validation and print results.

    Args:
        catalog_path: Path to the catalog root directory.

    Raises:
        SystemExit: If validation fails (exit code 1).
    """
    errors = validate_catalog(catalog_path)

    if errors:
        log("ERR", "Catalog validation failed:")
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        log("ERR", f"Catalog validation failed. {len(errors)} issues found.")
        sys.exit(1)

    # Count entries for the success message
    entries = discover_entries(catalog_path)
    log("OK", f"Catalog validation passed. {len(entries)} entries found.")
