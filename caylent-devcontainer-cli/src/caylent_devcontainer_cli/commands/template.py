"""Template command for the Caylent Devcontainer CLI."""

import os
import shutil

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
        shutil.copy2(env_vars_json, template_path)
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
        log("INFO", f"Loading template {template_name} from {template_path}")
        shutil.copy2(template_path, env_vars_json)
        log("OK", f"Template '{template_name}' loaded to {env_vars_json}")
    except Exception as e:
        log("ERR", f"Failed to load template: {e}")
        import sys

        sys.exit(1)


def list_templates():
    """List available templates."""
    ensure_templates_dir()
    templates = [f.replace(".json", "") for f in os.listdir(TEMPLATES_DIR) if f.endswith(".json")]

    if not templates:
        from caylent_devcontainer_cli.utils.ui import COLORS

        print(f"{COLORS['YELLOW']}No templates found. Create one with 'template save <name>'{COLORS['RESET']}")
        return

    from caylent_devcontainer_cli.utils.ui import COLORS

    print(f"{COLORS['CYAN']}Available templates:{COLORS['RESET']}")
    for template in sorted(templates):
        print(f"  - {COLORS['GREEN']}{template}{COLORS['RESET']}")
