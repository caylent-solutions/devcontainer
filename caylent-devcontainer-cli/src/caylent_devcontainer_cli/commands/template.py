"""Template command for the Caylent Devcontainer CLI."""

import json
import os

import semver

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands.setup_interactive import upgrade_template
from caylent_devcontainer_cli.utils.constants import TEMPLATES_DIR
from caylent_devcontainer_cli.utils.ui import confirm_action, log


def register_command(subparsers):
    """Register the template command."""
    template_parser = subparsers.add_parser("template", help="Template management")
    template_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    template_subparsers = template_parser.add_subparsers(dest="template_command")

    # 'template save' command
    save_parser = template_subparsers.add_parser("save", help="Save current environment as a template")
    save_parser.add_argument("name", help="Template name")
    save_parser.add_argument("-p", "--project-root", help="Project root directory (default: current directory)")
    save_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    save_parser.set_defaults(func=handle_template_save)

    # 'template load' command
    load_template_parser = template_subparsers.add_parser("load", help="Load a template into current project")
    load_template_parser.add_argument("name", help="Template name")
    load_template_parser.add_argument(
        "-p", "--project-root", help="Project root directory (default: current directory)"
    )
    load_template_parser.add_argument(
        "-y", "--yes", action="store_true", help="Automatically answer yes to all prompts"
    )
    load_template_parser.set_defaults(func=handle_template_load)

    # 'template list' command
    list_parser = template_subparsers.add_parser("list", help="List available templates")
    list_parser.set_defaults(func=handle_template_list)

    # 'template delete' command
    delete_parser = template_subparsers.add_parser("delete", help="Delete one or more templates")
    delete_parser.add_argument("names", nargs="+", help="Template names to delete")
    delete_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    delete_parser.set_defaults(func=handle_template_delete)

    # 'template upgrade' command
    upgrade_parser = template_subparsers.add_parser("upgrade", help="Upgrade a template to the current CLI version")
    upgrade_parser.add_argument("name", help="Template name to upgrade")
    upgrade_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    upgrade_parser.set_defaults(func=handle_template_upgrade)


def ensure_templates_dir():
    """Ensure templates directory exists."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def handle_template_save(args):
    """Handle the template save command."""
    project_root = args.project_root or os.getcwd()
    save_template(project_root, args.name)


def handle_template_load(args):
    """Handle the template load command."""
    project_root = args.project_root or os.getcwd()
    load_template(project_root, args.name)


def handle_template_list(args):
    """Handle the template list command."""
    list_templates()


def handle_template_delete(args):
    """Handle the template delete command."""
    for name in args.names:
        delete_template(name)


def handle_template_upgrade(args):
    """Handle the template upgrade command."""
    upgrade_template_file(args.name)


def save_template(project_root, template_name):
    """Save current environment as a template."""
    ensure_templates_dir()
    env_vars_json = os.path.join(project_root, "devcontainer-environment-variables.json")

    if not os.path.exists(env_vars_json):
        log("ERR", f"No devcontainer-environment-variables.json found in {project_root}")
        import sys

        sys.exit(1)

    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")

    # Ask for confirmation before saving
    if os.path.exists(template_path):
        if not confirm_action(f"This will overwrite the existing template at:\n{template_path}"):
            import sys

            sys.exit(1)
    else:
        if not confirm_action(f"This will create a new template at:\n{template_path}"):
            import sys

            sys.exit(1)

    try:
        log("INFO", f"Saving template from {env_vars_json}")

        # Read the environment variables file
        with open(env_vars_json, "r") as f:
            env_data = json.load(f)

        # Add CLI version information
        env_data["cli_version"] = __version__

        # Write to template file
        with open(template_path, "w") as f:
            json.dump(env_data, f, indent=2)
            f.write("\n")  # Add newline at end of file

        log("OK", f"Template saved as: {template_name} at {template_path}")
    except Exception as e:
        log("ERR", f"Failed to save template: {e}")
        import sys

        sys.exit(1)


def load_template(project_root, template_name):
    """Load a template into the current project."""
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")

    if not os.path.exists(template_path):
        log("ERR", f"Template '{template_name}' not found at {template_path}")
        import sys

        sys.exit(1)

    env_vars_json = os.path.join(project_root, "devcontainer-environment-variables.json")

    # Ask for confirmation before loading
    if os.path.exists(env_vars_json):
        if not confirm_action(f"This will overwrite your existing configuration at:\n{env_vars_json}"):
            import sys

            sys.exit(1)
    else:
        if not confirm_action(f"This will create a new configuration at:\n{env_vars_json}"):
            import sys

            sys.exit(1)

    try:
        # Read the template file
        with open(template_path, "r") as f:
            template_data = json.load(f)

        # Check version compatibility
        if "cli_version" in template_data:
            template_version = template_data["cli_version"]
            current_version = __version__

            try:
                # Parse versions using semver
                template_semver = semver.VersionInfo.parse(template_version)
                current_semver = semver.VersionInfo.parse(current_version)

                # Check if major versions differ
                if template_semver.major < current_semver.major:
                    log(
                        "WARN",
                        f"Template was created with CLI version {template_version}, "
                        f"but you're using version {current_version}",
                    )
                    print("\nPlease choose one of the following options:")
                    print("1. Upgrade the profile to the current version")
                    print("2. Create a new profile from scratch")
                    print("3. Try to use the profile anyway (may fail)")
                    print("4. Exit and revert changes")

                    while True:
                        choice = input("\nEnter your choice (1-4): ").strip()
                        if choice == "1":
                            # Upgrade the template
                            template_data = upgrade_template(template_data)
                            log("OK", f"Template upgraded to version {current_version}")
                            break
                        elif choice == "2":
                            log("INFO", "Please use 'cdevcontainer template save' to create a new profile")
                            import sys

                            sys.exit(0)
                        elif choice == "3":
                            if not confirm_action("The template format may be incompatible. Continue anyway?"):
                                log("INFO", "Operation cancelled by user")
                                import sys

                                sys.exit(0)
                            break
                        elif choice == "4":
                            log("INFO", "Operation cancelled by user")
                            import sys

                            sys.exit(0)
                        else:
                            print("Invalid choice. Please enter a number between 1 and 4.")
            except ValueError:
                # If version parsing fails, just continue with the template as is
                log("WARN", f"Could not parse template version: {template_version}")

        # Write to environment variables file
        with open(env_vars_json, "w") as f:
            json.dump(template_data, f, indent=2)
            f.write("\n")  # Add newline at end of file

        log("OK", f"Template '{template_name}' loaded to {env_vars_json}")
    except Exception as e:
        log("ERR", f"Failed to load template: {e}")
        import sys

        sys.exit(1)


def list_templates():
    """List available templates."""
    ensure_templates_dir()
    templates = []

    for f in os.listdir(TEMPLATES_DIR):
        if f.endswith(".json"):
            template_name = f.replace(".json", "")
            template_path = os.path.join(TEMPLATES_DIR, f)

            # Try to get version information
            version = "unknown"
            try:
                with open(template_path, "r") as file:
                    data = json.load(file)
                    if "cli_version" in data:
                        version = data["cli_version"]
            except Exception:
                pass

            templates.append((template_name, version))

    if not templates:
        from caylent_devcontainer_cli.utils.ui import COLORS

        print(f"{COLORS['YELLOW']}No templates found. Create one with 'template save <n>'{COLORS['RESET']}")
        return

    from caylent_devcontainer_cli.utils.ui import COLORS

    print(f"{COLORS['CYAN']}Available templates:{COLORS['RESET']}")
    for template_name, version in sorted(templates):
        print(f"  - {COLORS['GREEN']}{template_name}{COLORS['RESET']} (created with CLI version {version})")


def delete_template(template_name):
    """Delete a template."""
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")

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
    """Upgrade a template to the current CLI version."""
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")

    if not os.path.exists(template_path):
        log("ERR", f"Template '{template_name}' not found at {template_path}")
        import sys

        sys.exit(1)

    try:
        # Read the template file
        with open(template_path, "r") as f:
            template_data = json.load(f)

        # Check if upgrade is needed
        if "cli_version" in template_data:
            template_version = template_data["cli_version"]
            current_version = __version__

            try:
                # Parse versions using semver
                template_semver = semver.VersionInfo.parse(template_version)
                current_semver = semver.VersionInfo.parse(current_version)

                if template_semver.major == current_semver.major and template_semver.minor == current_semver.minor:
                    log(
                        "INFO",
                        f"Template '{template_name}' is already at the latest format (version {template_version})",
                    )
                    return
            except ValueError:
                # If version parsing fails, proceed with upgrade
                pass

        # Upgrade the template
        upgraded_template = upgrade_template(template_data)

        # Write back to the template file
        with open(template_path, "w") as f:
            json.dump(upgraded_template, f, indent=2)
            f.write("\n")  # Add newline at end of file

        log(
            "OK",
            f"Template '{template_name}' upgraded from version "
            f"{template_data.get('cli_version', 'unknown')} to {__version__}",
        )
    except Exception as e:
        log("ERR", f"Failed to upgrade template: {e}")
        import sys

        sys.exit(1)
