"""Code command for the Caylent Devcontainer CLI."""

import json
import os
import shutil
import subprocess

import questionary

from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ASSETS_DIR,
    CATALOG_COMMON_DIR,
    CATALOG_ENTRY_FILENAME,
    ENV_VARS_FILENAME,
    SHELL_ENV_FILENAME,
)
from caylent_devcontainer_cli.utils.fs import (
    load_json_config,
    resolve_project_root,
    write_project_files,
    write_shell_env,
)
from caylent_devcontainer_cli.utils.ui import COLORS, ask_or_exit, exit_with_error, log
from caylent_devcontainer_cli.utils.validation import detect_validation_issues

_GENERATE_HINT = (
    "Run `cdevcontainer setup-devcontainer <path>` or "
    "`cdevcontainer template load <name> -p <path>` to generate project files"
)

# IDE configuration
IDE_CONFIG = {
    "vscode": {
        "command": "code",
        "name": "VS Code",
        "install_instructions": (
            "Please install VS Code and ensure the 'code' command is available in your PATH. "
            "Visit: https://code.visualstudio.com/"
        ),
    },
    "cursor": {
        "command": "cursor",
        "name": "Cursor",
        "install_instructions": (
            "Please install Cursor and ensure the 'cursor' command is available in your PATH. "
            "Visit: https://cursor.sh/"
        ),
    },
}


def register_command(subparsers):
    """Register the code command."""
    code_parser = subparsers.add_parser("code", help="Launch IDE (VS Code, Cursor) with the devcontainer environment")
    code_parser.add_argument(
        "project_root",
        nargs="?",
        default=None,
        help="Project root directory (default: current directory)",
    )
    code_parser.add_argument(
        "--ide", choices=["vscode", "cursor"], default="vscode", help="IDE to launch (default: vscode)"
    )
    code_parser.add_argument(
        "--regenerate-shell-env",
        action="store_true",
        help="Regenerate shell.env from existing JSON configuration without full setup",
    )
    code_parser.set_defaults(func=handle_code)


def handle_code(args):
    """Handle the code command.

    Environment variables are sourced inside the devcontainer by the
    postCreateCommand — not before IDE launch.  The launch command is
    simply ``<ide_command> <project_root>``.

    After file existence checks, runs two-stage validation (Steps 0-5)
    to detect and resolve missing environment variables.
    """
    project_root = resolve_project_root(args.project_root)

    env_json = os.path.join(project_root, ENV_VARS_FILENAME)
    shell_env = os.path.join(project_root, SHELL_ENV_FILENAME)

    # --regenerate-shell-env: read JSON, regenerate shell.env only
    if args.regenerate_shell_env:
        if not os.path.isfile(env_json):
            exit_with_error(f"{ENV_VARS_FILENAME} not found at {env_json}. {_GENERATE_HINT}")

        config_data = load_json_config(env_json)
        write_shell_env(
            project_root,
            config_data.get("containerEnv", {}),
            config_data.get("cli_version", ""),
            config_data.get("template_name", "unknown"),
            config_data.get("template_path", ""),
        )
        log("OK", "Regenerated shell.env from existing JSON configuration")
    else:
        # Both files must already exist
        if not os.path.isfile(env_json):
            exit_with_error(f"{ENV_VARS_FILENAME} not found at {env_json}. {_GENERATE_HINT}")
        if not os.path.isfile(shell_env):
            exit_with_error(f"{SHELL_ENV_FILENAME} not found at {shell_env}. {_GENERATE_HINT}")

        config_data = load_json_config(env_json)

    # --- Validation Steps 0-5 ---
    result = detect_validation_issues(project_root, config_data)

    # Step 1 response: metadata missing
    if not result.metadata_present:
        skip_validation = _handle_missing_metadata(project_root)
        if skip_validation:
            # User chose "No" — launch IDE without changes
            _launch_ide(args.ide, project_root)
            return

    # Step 2 response: template not found
    if result.metadata_present and not result.template_found:
        exit_with_error(
            f"Developer template '{result.template_name}' not found at "
            f"'{result.template_path}'. To fix this, either recreate the template with "
            "`cdevcontainer template create <name>` or regenerate project files with "
            "`cdevcontainer setup-devcontainer <path>`"
        )

    # Steps 4-5: handle missing variables
    if result.all_missing_keys:
        _handle_missing_variables(project_root, config_data, result)

    # Launch IDE
    _launch_ide(args.ide, project_root)


def _handle_missing_metadata(project_root):
    """Handle Step 1: missing metadata response.

    If the user chooses "Yes", runs interactive setup to regenerate
    project files with proper metadata.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True — always launches IDE after handling (either skipped or regenerated).
    """
    log("WARN", "Project files are missing required metadata and must be regenerated.")

    choice = ask_or_exit(
        questionary.select(
            "Would you like to select a template to regenerate project files?",
            choices=[
                "Yes — select or create a template to regenerate files",
                "No — launch IDE without changes (may cause issues)",
            ],
            default="Yes — select or create a template to regenerate files",
        )
    )

    if "No" in choice:
        log("WARN", "Continuing without regeneration — the environment may not work correctly")
        return True

    # User chose Yes — run interactive setup to regenerate project files
    from caylent_devcontainer_cli.commands.setup import interactive_setup

    interactive_setup(project_root)
    return True


def _handle_missing_variables(project_root, config_data, result):
    """Handle Steps 4-5: display and resolve missing variables.

    Args:
        project_root: Path to the project root directory.
        config_data: Loaded JSON config data.
        result: ValidationResult with detected issues.
    """
    all_missing = result.all_missing_keys

    # Step 4: Display missing variables
    log("WARN", "Missing environment variables detected")
    print(f"\n{COLORS['RED']}Missing variables may cause the environment to be improperly built.{COLORS['RESET']}")
    print(f"{COLORS['RED']}The devcontainer may not function correctly.{COLORS['RESET']}\n")

    for key, value in sorted(all_missing.items()):
        source = "base keys" if key in result.missing_base_keys else "template"
        print(f"  {COLORS['CYAN']}{key}{COLORS['RESET']} = {COLORS['GREEN']}{value}{COLORS['RESET']}  ({source})")

    print()

    # Step 5: User confirmation
    log("INFO", "Missing variables indicate the devcontainer configuration may need to be upgraded.")

    choice = ask_or_exit(
        questionary.select(
            "What would you like to do?",
            choices=[
                "Update devcontainer configuration and add missing variables",
                "Only add the missing variables to existing files",
                "Open without changes",
            ],
            default="Update devcontainer configuration and add missing variables",
        )
    )

    if "Open without changes" in choice:
        log("WARN", "Continuing without changes — the environment may not work correctly")
        return

    # Merge missing variables into the template data for write_project_files
    template_data = result.validated_template
    if template_data is None:
        # Fallback: use config_data with missing keys merged in
        template_data = dict(config_data)
        container_env = dict(template_data.get("containerEnv", {}))
        container_env.update(all_missing)
        template_data["containerEnv"] = container_env

    template_name = result.template_name or config_data.get("template_name", "unknown")
    template_path = result.template_path or config_data.get("template_path", "")

    if "Update devcontainer" in choice:
        # Option 1: Add missing vars + replace .devcontainer/ via catalog
        write_project_files(project_root, template_data, template_name, template_path)
        log("OK", "Project files updated with missing variables")
        _replace_devcontainer_files(project_root)
    else:
        # Option 2: Add missing vars only, do not modify .devcontainer/
        write_project_files(project_root, template_data, template_name, template_path)
        log("OK", "Missing variables added to project files")


def _replace_devcontainer_files(project_root):
    """Replace .devcontainer/ files via the catalog pipeline.

    Reads ``.devcontainer/catalog-entry.json`` to determine the catalog
    source.  If the file exists, clones the same catalog and copies the
    collection.  If missing (pre-catalog project), prompts the user to
    select a catalog source using the same flow as setup-devcontainer.

    Args:
        project_root: Path to the project root directory.
    """
    from caylent_devcontainer_cli.commands.setup import (
        _select_and_copy_catalog,
        _show_replace_notification,
    )

    _show_replace_notification()

    catalog_entry_path = os.path.join(project_root, ".devcontainer", CATALOG_ENTRY_FILENAME)

    if os.path.isfile(catalog_entry_path):
        _replace_from_catalog_entry(project_root, catalog_entry_path)
    else:
        # Pre-catalog project — use the same selection flow as setup-devcontainer
        _select_and_copy_catalog(project_root)


def _replace_from_catalog_entry(project_root, catalog_entry_path):
    """Replace .devcontainer/ files using catalog-entry.json metadata.

    Reads the catalog URL and collection name from the existing
    catalog-entry.json, clones the catalog, finds the matching
    collection, and copies it to the project.

    Args:
        project_root: Path to the project root directory.
        catalog_entry_path: Path to the catalog-entry.json file.
    """
    from caylent_devcontainer_cli.utils.catalog import (
        clone_catalog_repo,
        copy_collection_to_project,
        discover_collection_entries,
        find_collection_by_name,
    )

    try:
        with open(catalog_entry_path) as f:
            entry_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        exit_with_error(
            f"Failed to read {CATALOG_ENTRY_FILENAME}: {e}. "
            "Run 'cdevcontainer setup-devcontainer <path>' to reconfigure."
        )

    catalog_url = entry_data.get("catalog_url")
    collection_name = entry_data.get("name")

    if not catalog_url or not collection_name:
        exit_with_error(
            f"{CATALOG_ENTRY_FILENAME} is missing 'catalog_url' or 'name'. "
            "Run 'cdevcontainer setup-devcontainer <path>' to reconfigure."
        )

    target_devcontainer = os.path.join(project_root, ".devcontainer")

    temp_dir = clone_catalog_repo(catalog_url)
    try:
        entries = discover_collection_entries(temp_dir, skip_incomplete=True)
        selected = find_collection_by_name(entries, collection_name)
        common_assets = os.path.join(temp_dir, CATALOG_COMMON_DIR, CATALOG_ASSETS_DIR)
        copy_collection_to_project(selected.path, common_assets, target_devcontainer, catalog_url)
        log("OK", f"Collection '{collection_name}' files replaced in .devcontainer/")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _launch_ide(ide_key, project_root):
    """Check for IDE command and launch it.

    Args:
        ide_key: Key into IDE_CONFIG (e.g., "vscode", "cursor").
        project_root: Path to the project root directory.
    """
    ide_config = IDE_CONFIG[ide_key]
    ide_command = ide_config["command"]
    ide_name = ide_config["name"]

    # Check if IDE command exists
    if not shutil.which(ide_command):
        log("INFO", ide_config["install_instructions"])
        exit_with_error(f"{ide_name} command '{ide_command}' not found in PATH")

    # Launch IDE
    log("INFO", f"Launching {ide_name}...")

    try:
        process = subprocess.Popen([ide_command, project_root])
        process.wait()
        log("OK", f"{ide_name} launched. Accept the prompt to reopen in container when it appears.")
    except Exception as e:
        exit_with_error(f"Failed to launch {ide_name}: {e}")
