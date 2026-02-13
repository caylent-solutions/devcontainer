"""Setup command for the Caylent Devcontainer CLI."""

import json
import os

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.constants import (
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
    "DEFAULT_PYTHON_VERSION": "3.12.9",
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
    parser = subparsers.add_parser("setup-devcontainer", help="Set up a devcontainer in a project directory")
    parser.add_argument("path", help="Path to the root of the repository to set up")
    parser.set_defaults(func=handle_setup)


def handle_setup(args):
    """Handle the setup-devcontainer command.

    Flow:
    1. Validate target path
    2. Ensure .tool-versions exists (empty file)
    3. Detect existing configuration → replace/no-replace decision
    4. Run informational validation (Steps 0-3) if project files exist
    5. Run interactive setup → write_project_files()
    """
    target_path = args.path

    if not os.path.isdir(target_path):
        exit_with_error(f"Target path does not exist or is not a directory: {target_path}")

    # Ensure .tool-versions exists as empty file
    _ensure_tool_versions(target_path)

    # Detect existing configuration
    target_devcontainer = os.path.join(target_path, ".devcontainer")
    user_wants_replace = False

    if os.path.exists(target_devcontainer):
        _show_existing_config(target_path)
        _show_python_notice(target_path)
        user_wants_replace = _prompt_replace_decision()

        if user_wants_replace:
            _show_replace_notification()
            # Catalog selection will be added in S1.5.1
        else:
            log("INFO", "Keeping existing .devcontainer/ files. Continuing with environment file setup only.")

    # Informational validation (if both project files exist)
    _run_informational_validation(target_path)

    # Interactive setup
    interactive_setup(target_path)


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
            collection_name = catalog_data.get("collection_name", "unknown")
            catalog_url = catalog_data.get("catalog_url", "unknown")
            log("INFO", f"Catalog collection: {collection_name}")
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
