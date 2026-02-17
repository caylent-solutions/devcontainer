"""Setup command for the Caylent Devcontainer CLI."""

import json
import os
import shutil

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ASSETS_DIR,
    CATALOG_COMMON_DIR,
    CATALOG_ENTRY_FILENAME,
    ENV_VARS_FILENAME,
    SHELL_ENV_FILENAME,
)
from caylent_devcontainer_cli.utils.ui import ask_or_exit, exit_cancelled, exit_with_error, log

# Constants — base environment variable keys and their defaults.
# Imported by validation.py, template.py, and tests.
EXAMPLE_ENV_VALUES = {
    "AWS_CONFIG_ENABLED": "true",
    "AWS_DEFAULT_OUTPUT": "json",
    "DEFAULT_GIT_BRANCH": "main",
    "DEVELOPER_NAME": "Your Name",
    "EXTRA_APT_PACKAGES": "",
    "GIT_AUTH_METHOD": "token",
    "GIT_PROVIDER_URL": "github.com",
    "GIT_TOKEN": "your-git-token",
    "GIT_USER": "your-username",
    "GIT_USER_EMAIL": "your-email@example.com",
    "HOST_PROXY": "false",
    "HOST_PROXY_URL": "",
    "PAGER": "cat",
}


def register_command(subparsers):
    """Register the setup-devcontainer command with the CLI."""
    from caylent_devcontainer_cli.cli import _HelpFormatter, build_env_epilog

    parser = subparsers.add_parser(
        "setup-devcontainer",
        help="Set up a devcontainer in a project directory",
        formatter_class=_HelpFormatter,
        epilog=build_env_epilog("setup-devcontainer"),
    )
    import shtab

    path_action = parser.add_argument("path", help="Path to the root of the repository to set up")
    path_action.complete = shtab.DIRECTORY
    parser.add_argument(
        "--catalog-entry",
        type=str,
        default=None,
        metavar="NAME",
        help="Select a specific entry by name from a specialized catalog (requires DEVCONTAINER_CATALOG_URL)",
    )
    parser.add_argument(
        "--catalog-url",
        type=str,
        default=None,
        metavar="URL",
        help="Override the catalog repository URL (bypasses tag resolution and DEVCONTAINER_CATALOG_URL)",
    )
    parser.set_defaults(func=handle_setup)


def handle_setup(args):
    """Handle the setup-devcontainer command.

    Flow:
    1. Validate target path
    2. Ensure .tool-versions exists (empty file)
    3. Detect existing configuration → replace/no-replace decision
    4. If replace or no existing config: run catalog selection + copy
    5. Run informational validation (Steps 0-3) if project files exist
    6. Run interactive setup → write_project_files()
    """
    target_path = args.path
    catalog_entry = getattr(args, "catalog_entry", None)
    catalog_url_override = getattr(args, "catalog_url", None)

    if not os.path.isdir(target_path):
        exit_with_error(f"Target path does not exist or is not a directory: {target_path}")

    # Ensure .tool-versions exists as empty file
    _ensure_tool_versions(target_path)

    # Detect existing configuration
    target_devcontainer = os.path.join(target_path, ".devcontainer")
    should_copy_catalog = True

    if os.path.exists(target_devcontainer):
        _show_existing_config(target_path)
        _show_python_notice(target_path)
        user_wants_replace = _prompt_replace_decision()

        if user_wants_replace:
            _show_replace_notification()
        else:
            should_copy_catalog = False
            log("INFO", "Keeping existing .devcontainer/ files. Continuing with environment file setup only.")

    # Catalog selection and file copy (when setting up or replacing .devcontainer/)
    if should_copy_catalog:
        _select_and_copy_catalog(target_path, catalog_entry=catalog_entry, catalog_url_override=catalog_url_override)

    # Informational validation (if both project files exist)
    _run_informational_validation(target_path)

    # Interactive setup
    interactive_setup(target_path)


def _select_and_copy_catalog(target_path, catalog_entry=None, catalog_url_override=None):
    """Select a catalog entry and copy its files to the project.

    Handles catalog URL resolution with the following precedence:
    1. ``--catalog-url`` override (used as-is, bypasses tag resolution and env var)
    2. ``--catalog-entry`` flag: validate env, clone specialized, find by name, confirm, copy
    3. ``DEVCONTAINER_CATALOG_URL`` set: prompt source selection, then clone/browse/copy
    4. No env var: resolve default catalog via semver tag, auto-select, copy

    Args:
        target_path: Path to the project root directory.
        catalog_entry: Optional entry name from ``--catalog-entry`` flag.
        catalog_url_override: Optional catalog URL from ``--catalog-url`` flag.
    """
    from caylent_devcontainer_cli.utils.catalog import (
        check_min_cli_version,
        clone_catalog_repo,
        copy_entry_to_project,
        discover_entries,
        find_entry_by_name,
        resolve_default_catalog_url,
        validate_catalog_entry_env,
    )

    target_devcontainer = os.path.join(target_path, ".devcontainer")
    env_url = os.environ.get("DEVCONTAINER_CATALOG_URL")

    # Determine which catalog URL to use
    user_chose_default = False
    user_chose_browse = False
    if catalog_url_override:
        catalog_url = catalog_url_override
        log("INFO", f"Using catalog URL override: {catalog_url}")
    elif catalog_entry:
        catalog_url = validate_catalog_entry_env(catalog_entry)
    elif env_url:
        source = _prompt_source_selection()
        if source == "default":
            catalog_url = resolve_default_catalog_url()
            user_chose_default = True
        else:
            catalog_url = env_url
            user_chose_browse = True
    else:
        catalog_url = resolve_default_catalog_url()
        user_chose_default = True

    # Clone, discover, select, copy
    temp_dir = clone_catalog_repo(catalog_url)
    try:
        entries = discover_entries(temp_dir, skip_incomplete=True)

        # Filter by min_cli_version — warn and skip incompatible entries
        compatible = []
        for entry_info in entries:
            min_ver = entry_info.entry.min_cli_version
            if min_ver and not check_min_cli_version(min_ver):
                log("WARN", f"Skipping '{entry_info.entry.name}': requires CLI version >= {min_ver}")
                continue
            compatible.append(entry_info)

        if not compatible:
            exit_with_error("No compatible devcontainer entries found in the catalog.")

        # Select entry
        if catalog_entry:
            selected = find_entry_by_name(compatible, catalog_entry)
            _display_and_confirm_entry(selected)
        elif user_chose_browse:
            # User explicitly chose "Browse" — always show selection UI
            # _browse_entries already displays metadata and confirms
            selected = _browse_entries(compatible)
        elif len(compatible) == 1:
            selected = compatible[0]
            log("INFO", f"Auto-selected entry: {selected.entry.name}")
        elif env_url and user_chose_default:
            # User picked "Default" from source selection
            selected = find_entry_by_name(compatible, "default")
            log("INFO", f"Selected default entry: {selected.entry.name}")
        else:
            # _browse_entries already displays metadata and confirms
            selected = _browse_entries(compatible)

        # Copy files
        common_assets = os.path.join(temp_dir, CATALOG_COMMON_DIR, CATALOG_ASSETS_DIR)
        copy_entry_to_project(selected.path, common_assets, target_devcontainer, catalog_url)
        log("OK", f"Entry '{selected.entry.name}' files copied to .devcontainer/")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _prompt_source_selection():
    """Prompt the user to select a devcontainer configuration source.

    Shown only when DEVCONTAINER_CATALOG_URL is set, giving the user
    a choice between the default Caylent devcontainer and browsing
    the specialized catalog.

    Returns:
        ``"default"`` or ``"browse"``.
    """
    import questionary

    choices = [
        questionary.Choice("Default Caylent General DevContainer", value="default"),
        questionary.Choice("Browse specialized configurations from catalog", value="browse"),
    ]

    log("INFO", "DevContainer configuration sources available:")

    return ask_or_exit(
        questionary.select(
            "Select a configuration source:",
            choices=choices,
        )
    )


def _browse_entries(entries):
    """Present a searchable selection list of catalog entries.

    Loops until the user confirms their selection with "Is this correct?".

    Args:
        entries: List of :class:`EntryInfo` objects to choose from.

    Returns:
        The selected :class:`EntryInfo`.
    """
    import questionary

    while True:
        choices = [questionary.Choice(f"{e.entry.name} — {e.entry.description}", value=e) for e in entries]

        selected = ask_or_exit(
            questionary.select(
                "Select a devcontainer entry:",
                choices=choices,
            )
        )

        _display_entry_metadata(selected)

        confirmed = ask_or_exit(questionary.confirm("Is this correct?", default=True))
        if confirmed:
            return selected


def _display_entry_metadata(entry_info):
    """Display the full metadata for a selected catalog entry.

    Args:
        entry_info: The :class:`EntryInfo` to display.
    """
    entry = entry_info.entry
    print(f"\n  Name:        {entry.name}")
    print(f"  Description: {entry.description}")
    if entry.tags:
        print(f"  Tags:        {', '.join(entry.tags)}")
    if entry.maintainer:
        print(f"  Maintainer:  {entry.maintainer}")
    if entry.min_cli_version:
        print(f"  Min CLI:     {entry.min_cli_version}")
    print()


def _display_and_confirm_entry(entry_info):
    """Display entry metadata and ask the user to confirm.

    If the user does not confirm, exits with a cancellation message.

    Args:
        entry_info: The :class:`EntryInfo` to confirm.
    """
    import questionary

    _display_entry_metadata(entry_info)
    confirmed = ask_or_exit(questionary.confirm("Is this correct?", default=True))
    if not confirmed:
        exit_cancelled("Entry selection cancelled by user.")


def _ensure_tool_versions(target_path: str) -> None:
    """Create .tool-versions as an empty file if it does not exist.

    Args:
        target_path: Path to the project root directory.
    """
    tool_versions_path = os.path.join(target_path, ".tool-versions")

    if os.path.exists(tool_versions_path):
        return

    with open(tool_versions_path, "w") as f:
        f.write("")
    log("OK", f"Created empty .tool-versions at {tool_versions_path}")


def _show_existing_config(target_path: str) -> None:
    """Display information about existing devcontainer configuration.

    Shows VERSION file content and catalog-entry.json info if present.

    Args:
        target_path: Path to the project root directory.
    """
    devcontainer_dir = os.path.join(target_path, ".devcontainer")

    log("INFO", "Devcontainer configuration files already exist in this project.")

    # Show version from VERSION file
    version_file = os.path.join(devcontainer_dir, "VERSION")
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            version = f.read().strip()
        log("INFO", f"Current version: {version}")
    else:
        log("INFO", "Current version: unknown")

    # Show catalog entry info if present
    catalog_entry_path = os.path.join(devcontainer_dir, CATALOG_ENTRY_FILENAME)
    if os.path.exists(catalog_entry_path):
        try:
            with open(catalog_entry_path, "r") as f:
                catalog_data = json.load(f)
            entry_name = catalog_data.get("name", "unknown")
            catalog_url = catalog_data.get("catalog_url", "unknown")
            log("INFO", f"Catalog entry: {entry_name}")
            log("INFO", f"Catalog URL: {catalog_url}")
        except (json.JSONDecodeError, OSError):
            log("WARN", "Could not read catalog-entry.json")

    log("INFO", "You will be asked whether to replace the existing configuration.")


def _show_python_notice(target_path: str) -> None:
    """Display Python management notice if .tool-versions contains a Python entry.

    Args:
        target_path: Path to the project root directory.
    """
    tool_versions_path = os.path.join(target_path, ".tool-versions")

    if not os.path.exists(tool_versions_path):
        return

    with open(tool_versions_path, "r") as f:
        content = f.read()

    if _has_python_entry(content):
        log(
            "INFO",
            "Your .tool-versions file contains a Python entry. The recommended "
            "configuration manages Python through features in devcontainer.json, "
            ".devcontainer/.devcontainer.postcreate.sh, and devcontainer-functions.sh. "
            "If you want to follow this recommendation, choose yes when prompted to replace.",
        )


def _has_python_entry(content: str) -> bool:
    """Check if tool-versions content contains a Python entry.

    Args:
        content: The raw text content of .tool-versions.

    Returns:
        True if a line starting with 'python' is found.
    """
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("python"):
            return True
    return False


def _prompt_replace_decision() -> bool:
    """Ask the user whether to replace existing .devcontainer/ files.

    Returns:
        True if user wants to replace, False otherwise.
    """
    import questionary

    return ask_or_exit(
        questionary.confirm(
            "Do you want to replace the existing .devcontainer/ files?",
            default=False,
        )
    )


def _show_replace_notification() -> None:
    """Display notification about what replacing .devcontainer/ files entails.

    Requires explicit keypress acknowledgement before proceeding.
    """
    import questionary

    log("INFO", "Replacing .devcontainer/ files will:")
    print("  - Overwrite existing devcontainer configuration files")
    print("  - You should review git changes before building the devcontainer")
    print("  - Close any remote connection if the project auto-starts a devcontainer")
    print("  - Open the project from the OS file explorer, not recent folders")
    print("  - Merge back any customizations you made to the previous configuration")
    print("  - Test the new configuration before pushing")
    print("  - Rebuild the devcontainer (possibly without cache)")

    acknowledged = ask_or_exit(
        questionary.confirm(
            "I understand the above. Proceed with replacement?",
            default=False,
        )
    )

    if not acknowledged:
        exit_cancelled("Replacement cancelled by user.")


def _run_informational_validation(target_path: str) -> None:
    """Run shared validation (Steps 0-3) in informational-only mode.

    Unlike the code command, setup-devcontainer does NOT prompt the user
    to fix issues. It displays detected issues as informational messages.

    Args:
        target_path: Path to the project root directory.
    """
    env_json_path = os.path.join(target_path, ENV_VARS_FILENAME)
    shell_env_path = os.path.join(target_path, SHELL_ENV_FILENAME)

    # Only run if both project files exist
    if not os.path.isfile(env_json_path) or not os.path.isfile(shell_env_path):
        return

    from caylent_devcontainer_cli.utils.fs import load_json_config
    from caylent_devcontainer_cli.utils.validation import detect_validation_issues

    config_data = load_json_config(env_json_path)
    result = detect_validation_issues(target_path, config_data)

    if not result.has_issues:
        return

    log(
        "INFO",
        "The following configuration issues were detected. Completing this setup "
        "will regenerate your project configuration from the selected template "
        "and resolve these issues:",
    )

    if result.missing_base_keys:
        log("INFO", f"  Missing base keys: {', '.join(sorted(result.missing_base_keys.keys()))}")

    if not result.metadata_present:
        log("INFO", "  Missing metadata (template_name, template_path, cli_version)")

    if result.metadata_present and not result.template_found:
        log("INFO", f"  Template '{result.template_name}' not found on disk")

    if result.missing_template_keys:
        log("INFO", f"  Missing template keys: {', '.join(sorted(result.missing_template_keys.keys()))}")


def create_version_file(target_path: str) -> None:
    """Create a VERSION file in the .devcontainer directory.

    Args:
        target_path: Path to the project root directory.
    """
    version_file = os.path.join(target_path, ".devcontainer", "VERSION")
    with open(version_file, "w") as f:
        f.write(__version__ + "\n")
    log("INFO", f"Created VERSION file with version {__version__}")


def interactive_setup(target_path: str) -> None:
    """Run interactive setup process.

    Handles template selection/creation flow and calls apply_template()
    for environment file generation. Does NOT copy .devcontainer/ files —
    that responsibility belongs to the catalog pipeline.
    """
    from caylent_devcontainer_cli.commands.setup_interactive import (
        apply_template,
        create_template_interactive,
        load_template_from_file,
        prompt_save_template,
        prompt_template_name,
        prompt_use_template,
        save_template_to_file,
        select_template,
    )
    from caylent_devcontainer_cli.utils.template import validate_template

    try:
        # Ask if they want to use a saved template
        if prompt_use_template():
            template_name = select_template()
            if template_name:
                template_data = load_template_from_file(template_name)
                template_data = validate_template(template_data)
                apply_template(template_data, target_path)
                log("OK", f"Template '{template_name}' applied successfully.")
                return

        # Create new template
        log("INFO", "Creating a new configuration...")
        template_data = create_template_interactive()

        # Ask if they want to save the template
        if prompt_save_template():
            template_name = prompt_template_name()
            save_template_to_file(template_data, template_name)

        # Apply the template
        apply_template(template_data, target_path)
        log("OK", "Setup completed successfully.")
    except KeyboardInterrupt:
        exit_cancelled("Setup cancelled by user.")
