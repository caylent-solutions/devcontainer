"""Template command for the Caylent Devcontainer CLI."""

import os

import semver

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands.setup_interactive import upgrade_template
from caylent_devcontainer_cli.utils.constants import ENV_VARS_FILENAME
from caylent_devcontainer_cli.utils.env import get_missing_env_vars
from caylent_devcontainer_cli.utils.fs import (
    load_json_config,
    resolve_project_root,
    write_json_file,
    write_project_files,
)
from caylent_devcontainer_cli.utils.template import (
    ensure_templates_dir,
    get_template_names,
    get_template_path,
    validate_template,
)
from caylent_devcontainer_cli.utils.ui import COLORS, ask_or_exit, confirm_action, exit_cancelled, exit_with_error, log


def prompt_for_missing_vars(missing_vars):
    """Prompt user for missing environment variables."""
    import questionary

    updated_vars = {}
    for var_name, default_value in missing_vars.items():
        log("INFO", f"New environment variable '{var_name}' needs to be added to your template")

        use_default = ask_or_exit(
            questionary.confirm(f"Use default value '{default_value}' for {var_name}?", default=True)
        )

        if use_default:
            updated_vars[var_name] = default_value
        else:
            custom_value = ask_or_exit(
                questionary.text(f"Enter custom value for {var_name}:", default=str(default_value))
            )
            updated_vars[var_name] = custom_value

    return updated_vars


def register_command(subparsers):
    """Register the template command."""
    template_parser = subparsers.add_parser("template", help="Template management")
    template_subparsers = template_parser.add_subparsers(dest="template_command")

    # 'template save' command
    save_parser = template_subparsers.add_parser("save", help="Save current environment as a template")
    save_parser.add_argument("name", help="Template name")
    save_parser.add_argument("-p", "--project-root", help="Project root directory (default: current directory)")
    save_parser.set_defaults(func=handle_template_save)

    # 'template load' command
    load_template_parser = template_subparsers.add_parser("load", help="Load a template into current project")
    load_template_parser.add_argument("name", help="Template name")
    load_template_parser.add_argument(
        "-p", "--project-root", help="Project root directory (default: current directory)"
    )
    load_template_parser.set_defaults(func=handle_template_load)

    # 'template list' command
    list_parser = template_subparsers.add_parser("list", help="List available templates")
    list_parser.set_defaults(func=handle_template_list)

    # 'template delete' command
    delete_parser = template_subparsers.add_parser("delete", help="Delete one or more templates")
    delete_parser.add_argument("names", nargs="+", help="Template names to delete")
    delete_parser.set_defaults(func=handle_template_delete)

    # 'template create' command
    create_parser = template_subparsers.add_parser("create", help="Create a new template interactively")
    create_parser.add_argument("name", help="Template name")
    create_parser.set_defaults(func=handle_template_create)

    # 'template upgrade' command
    upgrade_parser = template_subparsers.add_parser("upgrade", help="Upgrade a template to the current CLI version")
    upgrade_parser.add_argument("name", help="Template name to upgrade")
    upgrade_parser.add_argument(
        "-f", "--force", action="store_true", help="Force full upgrade with interactive prompts for missing variables"
    )
    upgrade_parser.set_defaults(func=handle_template_upgrade)


def handle_template_save(args):
    """Handle the template save command."""
    project_root = resolve_project_root(args.project_root)
    save_template(project_root, args.name)


def handle_template_load(args):
    """Handle the template load command."""
    project_root = resolve_project_root(args.project_root)
    load_template(project_root, args.name)


def handle_template_list(args):
    """Handle the template list command."""
    list_templates()


def handle_template_delete(args):
    """Handle the template delete command."""
    for name in args.names:
        delete_template(name)


def handle_template_create(args):
    """Handle the template create command."""
    create_new_template(args.name)


def create_new_template(template_name):
    """Create a new template interactively.

    Runs the full 17-step interactive creation flow and saves the
    template with metadata (template_name, template_path, cli_version).
    """
    import questionary

    from caylent_devcontainer_cli.commands.setup_interactive import create_template_interactive, save_template_to_file

    ensure_templates_dir()

    template_path = get_template_path(template_name)

    # Check if template already exists
    if os.path.exists(template_path):
        overwrite = ask_or_exit(
            questionary.confirm(
                f"Template '{template_name}' already exists. Overwrite?",
                default=False,
            )
        )
        if not overwrite:
            exit_cancelled("Template creation cancelled")

    log("INFO", f"Creating new template '{template_name}'")

    # Run the full interactive creation flow
    template_data = create_template_interactive()

    # Save with metadata (template_name, template_path added by save_template_to_file)
    save_template_to_file(template_data, template_name)

    log("OK", f"Template '{template_name}' created successfully")


def handle_template_upgrade(args):
    """Handle the template upgrade command."""
    upgrade_template_file(args.name, force=args.force)


def save_template(project_root, template_name):
    """Save current environment as a template."""
    ensure_templates_dir()
    env_vars_json = os.path.join(project_root, ENV_VARS_FILENAME)

    if not os.path.exists(env_vars_json):
        exit_with_error(f"No {ENV_VARS_FILENAME} found in {project_root}")

    template_path = get_template_path(template_name)

    # Ask for confirmation before saving
    if os.path.exists(template_path):
        if not confirm_action(f"This will overwrite the existing template at:\n{template_path}"):
            exit_cancelled()
    else:
        if not confirm_action(f"This will create a new template at:\n{template_path}"):
            exit_cancelled()

    try:
        log("INFO", f"Saving template from {env_vars_json}")

        # Read the environment variables file
        env_data = load_json_config(env_vars_json)

        # Add CLI version information
        env_data["cli_version"] = __version__

        # Write to template file
        write_json_file(template_path, env_data)

        log("OK", f"Template saved as: {template_name} at {template_path}")
    except Exception as e:
        exit_with_error(f"Failed to save template: {e}")


def load_template(project_root, template_name):
    """Load a template into the current project.

    Reads the template from ~/.devcontainer-templates/<name>.json,
    validates it via validate_template(), and generates all project
    files via write_project_files().
    """
    import questionary

    template_path = get_template_path(template_name)

    if not os.path.exists(template_path):
        exit_with_error(f"Template '{template_name}' not found at {template_path}")

    env_vars_json = os.path.join(project_root, ENV_VARS_FILENAME)

    # Confirm overwrite if configuration already exists
    if os.path.exists(env_vars_json):
        overwrite = ask_or_exit(
            questionary.confirm(
                f"This will overwrite your existing configuration at:\n{env_vars_json}",
                default=False,
            )
        )
        if not overwrite:
            exit_cancelled("Template load cancelled")

    # Read the template file
    template_data = load_json_config(template_path)

    # Validate template — rejects v1.x, validates structure, checks base keys,
    # validates constraints, checks auth consistency
    template_data = validate_template(template_data)

    # Generate all project files (env vars JSON, shell.env, gitignore, etc.)
    write_project_files(project_root, template_data, template_name, template_path)

    log("OK", f"Template '{template_name}' loaded successfully")


def list_templates():
    """List available templates."""
    ensure_templates_dir()
    template_names = get_template_names()

    if not template_names:
        print(f"{COLORS['YELLOW']}No templates found. Create one with 'template save <n>'{COLORS['RESET']}")
        return

    templates = []
    for name in template_names:
        template_path = get_template_path(name)

        # Try to get version information
        version = "unknown"
        try:
            data = load_json_config(template_path)
            if "cli_version" in data:
                version = data["cli_version"]
        except SystemExit:
            pass

        templates.append((name, version))

    print(f"{COLORS['CYAN']}Available templates:{COLORS['RESET']}")
    for template_name, version in templates:
        print(f"  - {COLORS['GREEN']}{template_name}{COLORS['RESET']} (created with CLI version {version})")


def delete_template(template_name):
    """Delete a template."""
    template_path = get_template_path(template_name)

    if not os.path.exists(template_path):
        log("ERR", f"Template '{template_name}' not found at {template_path}")
        return

    if not confirm_action(f"Are you sure you want to delete template '{template_name}'?"):
        log("INFO", f"Template '{template_name}' not deleted")
        return

    try:
        os.remove(template_path)
        log("OK", f"Template '{template_name}' deleted successfully")
    except Exception as e:
        log("ERR", f"Failed to delete template: {e}")


def upgrade_template_with_missing_vars(template_data):
    """Upgrade template with interactive prompts for missing variables."""
    from caylent_devcontainer_cli.commands.setup_interactive import upgrade_template

    # First do the standard upgrade
    upgraded_template = upgrade_template(template_data)

    # Check for missing single-line environment variables
    container_env = upgraded_template.get("containerEnv", {})
    missing_vars = get_missing_env_vars(container_env)

    if missing_vars:
        log("INFO", f"Found {len(missing_vars)} missing environment variables")
        new_vars = prompt_for_missing_vars(missing_vars)

        # Add the new variables to the container environment
        container_env.update(new_vars)
        upgraded_template["containerEnv"] = container_env

        log("OK", f"Added {len(new_vars)} new environment variables to template")
    else:
        log("INFO", "No missing environment variables found")

    return upgraded_template


def upgrade_template_file(template_name, force=False):
    """Upgrade a template to the current CLI version."""
    template_path = get_template_path(template_name)

    if not os.path.exists(template_path):
        exit_with_error(f"Template '{template_name}' not found at {template_path}")

    try:
        # Read the template file
        template_data = load_json_config(template_path)

        # Check if force upgrade is requested
        if force:
            log("INFO", "Force upgrade requested - performing full upgrade with missing variable detection")
            upgraded_template = upgrade_template_with_missing_vars(template_data)
        else:
            # Check if upgrade is needed
            if "cli_version" in template_data:
                template_version = template_data["cli_version"]
                current_version = __version__

                try:
                    # Parse versions using semver
                    template_semver = semver.VersionInfo.parse(template_version)
                    current_semver = semver.VersionInfo.parse(current_version)

                    if template_semver.major == current_semver.major and template_semver.minor == current_semver.minor:
                        # Even if the major and minor versions match, ensure the cli_version is updated
                        template_data["cli_version"] = __version__
                        write_json_file(template_path, template_data)
                        log(
                            "INFO",
                            f"Template '{template_name}' version updated from {template_version} to {__version__}",
                        )
                        return
                except ValueError:
                    # If version parsing fails, proceed with upgrade
                    pass

            # Upgrade the template
            upgraded_template = upgrade_template(template_data)

        # Write back to the template file
        write_json_file(template_path, upgraded_template)

        log(
            "OK",
            f"Template '{template_name}' upgraded from version "
            f"{template_data.get('cli_version', 'unknown')} to {__version__}",
        )
    except Exception as e:
        exit_with_error(f"Failed to upgrade template: {e}")
