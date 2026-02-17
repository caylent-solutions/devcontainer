"""Template command for the Caylent Devcontainer CLI."""

import os

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.constants import ENV_VARS_FILENAME, KNOWN_KEYS
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


def register_command(subparsers):
    """Register the template command."""
    from caylent_devcontainer_cli.cli import _HelpFormatter, build_env_epilog

    template_parser = subparsers.add_parser(
        "template",
        help="Template management",
        formatter_class=_HelpFormatter,
        epilog=build_env_epilog("template"),
    )
    template_subparsers = template_parser.add_subparsers(dest="template_command")

    # Custom completer for existing template names (used by shtab)
    _template_complete = {
        "bash": "_cdevcontainer_template_names",
        "zsh": "_cdevcontainer_template_names",
    }

    import shtab

    # 'template save' command (new name — no dynamic completion)
    save_parser = template_subparsers.add_parser("save", help="Save current environment as a template")
    save_parser.add_argument("name", help="Template name")
    save_project_root = save_parser.add_argument(
        "-p", "--project-root", help="Project root directory (default: current directory)"
    )
    save_project_root.complete = shtab.DIRECTORY
    save_parser.set_defaults(func=handle_template_save)

    # 'template load' command
    load_template_parser = template_subparsers.add_parser("load", help="Load a template into current project")
    load_name = load_template_parser.add_argument("name", help="Template name")
    load_name.complete = _template_complete
    load_project_root = load_template_parser.add_argument(
        "-p", "--project-root", help="Project root directory (default: current directory)"
    )
    load_project_root.complete = shtab.DIRECTORY
    load_template_parser.set_defaults(func=handle_template_load)

    # 'template list' command
    list_parser = template_subparsers.add_parser("list", help="List available templates")
    list_parser.set_defaults(func=handle_template_list)

    # 'template view' command
    view_parser = template_subparsers.add_parser("view", help="View a template's configuration values")
    view_name = view_parser.add_argument("name", help="Template name")
    view_name.complete = _template_complete
    view_parser.set_defaults(func=handle_template_view)

    # 'template edit' command
    edit_parser = template_subparsers.add_parser("edit", help="Edit an existing template interactively")
    edit_name = edit_parser.add_argument("name", help="Template name")
    edit_name.complete = _template_complete
    edit_parser.set_defaults(func=handle_template_edit)

    # 'template delete' command
    delete_parser = template_subparsers.add_parser("delete", help="Delete one or more templates")
    delete_names = delete_parser.add_argument("names", nargs="+", help="Template names to delete")
    delete_names.complete = _template_complete
    delete_parser.set_defaults(func=handle_template_delete)

    # 'template create' command (new name — no dynamic completion)
    create_parser = template_subparsers.add_parser("create", help="Create a new template interactively")
    create_parser.add_argument("name", help="Template name")
    create_parser.set_defaults(func=handle_template_create)

    # 'template upgrade' command
    upgrade_parser = template_subparsers.add_parser("upgrade", help="Upgrade a template to the current CLI version")
    upgrade_name = upgrade_parser.add_argument("name", help="Template name to upgrade")
    upgrade_name.complete = _template_complete
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


def handle_template_view(args):
    """Handle the template view command."""
    view_template(args.name)


def handle_template_delete(args):
    """Handle the template delete command."""
    for name in args.names:
        delete_template(name)


def handle_template_edit(args):
    """Handle the template edit command."""
    edit_template(args.name)


def edit_template(template_name):
    """Edit an existing template interactively.

    Loads the template, validates it, runs the interactive edit flow,
    updates metadata, and saves.
    """
    from caylent_devcontainer_cli.commands.setup_interactive import edit_template_interactive, save_template_to_file

    template_path = get_template_path(template_name)

    if not os.path.exists(template_path):
        exit_with_error(f"Template '{template_name}' not found at {template_path}")

    template_data = load_json_config(template_path)
    template_data = validate_template(template_data)

    updated = edit_template_interactive(template_data)

    save_template_to_file(updated, template_name)

    log("OK", f"Template '{template_name}' updated successfully")


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
    upgrade_template_file(args.name)


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


def view_template(template_name):
    """Display a template's configuration values.

    Reads the template JSON and prints metadata (name, CLI version)
    followed by environment variables grouped into known and custom.
    """
    template_path = get_template_path(template_name)

    if not os.path.exists(template_path):
        exit_with_error(f"Template '{template_name}' not found at {template_path}")

    data = load_json_config(template_path)
    container_env = data.get("containerEnv", {})

    # Separate known vs custom keys
    known = {k: v for k, v in sorted(container_env.items()) if k in KNOWN_KEYS}
    custom = {k: v for k, v in sorted(container_env.items()) if k not in KNOWN_KEYS}

    # Compute column width from all keys
    all_keys = list(known.keys()) + list(custom.keys())
    max_key_len = max((len(k) for k in all_keys), default=0)

    print(f"{COLORS['CYAN']}Template:{COLORS['RESET']} {template_name}")
    print(f"{COLORS['CYAN']}Path:{COLORS['RESET']} {template_path}")
    print(f"{COLORS['CYAN']}CLI Version:{COLORS['RESET']} {data.get('cli_version', 'unknown')}")

    if known:
        print(f"\n{COLORS['CYAN']}Environment Variables:{COLORS['RESET']}")
        for key, value in known.items():
            padding = " " * (max_key_len - len(key) + 2)
            print(f"  {key}{padding}{value}")

    if custom:
        print(f"\n{COLORS['CYAN']}Custom Variables:{COLORS['RESET']}")
        for key, value in custom.items():
            padding = " " * (max_key_len - len(key) + 2)
            print(f"  {key}{padding}{value}")

    if not known and not custom:
        print(f"\n{COLORS['YELLOW']}No environment variables defined.{COLORS['RESET']}")

    # Display SSH key path if SSH auth is configured
    ssh_key = data.get("ssh_private_key", "")
    if container_env.get("GIT_AUTH_METHOD") == "ssh" and ssh_key:
        print(f"\n{COLORS['CYAN']}SSH Private Key:{COLORS['RESET']} {ssh_key}")

    # Display AWS profiles if present
    aws_profiles = data.get("aws_profile_map", {})
    if aws_profiles:
        print(f"\n{COLORS['CYAN']}AWS Profiles:{COLORS['RESET']}")
        for profile_name, profile_config in sorted(aws_profiles.items()):
            print(f"\n  [{COLORS['GREEN']}{profile_name}{COLORS['RESET']}]")
            if isinstance(profile_config, dict):
                profile_key_len = max((len(k) for k in profile_config), default=0)
                for key, value in sorted(profile_config.items()):
                    padding = " " * (profile_key_len - len(key) + 2)
                    print(f"    {key}{padding}{value}")


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


def upgrade_template_file(template_name):
    """Upgrade a template to the current CLI version.

    Reads the template, runs validate_template() to detect and fix all
    issues (missing keys, invalid values, auth inconsistencies), updates
    cli_version, and saves. Modifies ONLY the template file — no project
    files are touched.
    """
    template_path = get_template_path(template_name)

    if not os.path.exists(template_path):
        exit_with_error(f"Template '{template_name}' not found at {template_path}")

    template_data = load_json_config(template_path)

    # Already at current version — no changes needed
    if template_data.get("cli_version") == __version__:
        log("INFO", f"Template '{template_name}' is already at CLI v{__version__}. No changes needed.")
        return

    # validate_template() handles all issues:
    # - Rejects v1.x templates with migration error
    # - Prompts for missing base keys
    # - Validates constraint values
    # - Checks auth consistency
    # - Detects conflicts
    template_data = validate_template(template_data)

    # Update cli_version to current
    template_data["cli_version"] = __version__

    # Save updated template
    write_json_file(template_path, template_data)

    log(
        "OK",
        f"Template '{template_name}' upgraded to CLI v{__version__}. "
        "Projects using this template will be updated on next `cdevcontainer code` run.",
    )
