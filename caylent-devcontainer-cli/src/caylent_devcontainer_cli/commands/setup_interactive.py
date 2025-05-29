"""Interactive setup functionality for the Caylent Devcontainer CLI."""

import json
import os
import shutil
from typing import Any, Dict, List, Optional

import questionary
import semver
from questionary import ValidationError, Validator

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.constants import TEMPLATES_DIR
from caylent_devcontainer_cli.utils.ui import log


class JsonValidator(Validator):
    """Validator for JSON input."""

    def validate(self, document):
        """Validate JSON input."""
        text = document.text
        if not text.strip():
            return

        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            raise ValidationError(message=f"Invalid JSON: {str(e)}", cursor_position=e.pos)


def list_templates() -> List[str]:
    """List available templates."""
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR, exist_ok=True)
        return []

    templates = []
    for file in os.listdir(TEMPLATES_DIR):
        if file.endswith(".json"):
            templates.append(file.replace(".json", ""))

    return templates


def prompt_use_template() -> bool:
    """Ask if the user wants to use a saved template."""
    templates = list_templates()

    if not templates:
        log("INFO", "No saved templates found.")
        return False

    return questionary.confirm("Do you want to use a saved template?", default=True).ask()


def select_template() -> Optional[str]:
    """Prompt the user to select a template."""
    templates = list_templates()

    if not templates:
        return None

    templates.append("< Go back")

    selected = questionary.select("Select a template:", choices=templates).ask()

    if selected == "< Go back":
        return None

    return selected


def prompt_save_template() -> bool:
    """Ask if the user wants to save the template."""
    return questionary.confirm("Do you want to save this configuration as a reusable template?", default=False).ask()


def prompt_template_name() -> str:
    """Prompt for template name."""
    return questionary.text("Enter a name for this template:", validate=lambda text: len(text) > 0).ask()


def prompt_env_values() -> Dict[str, Any]:
    """Prompt for environment values."""
    env_values = {}

    # AWS Config Enabled
    env_values["AWS_CONFIG_ENABLED"] = questionary.select(
        "Enable AWS configuration?", choices=["true", "false"], default="true"
    ).ask()

    # Git branch
    env_values["DEFAULT_GIT_BRANCH"] = questionary.text("Default Git branch (e.g., main):", default="main").ask()

    # Python version
    env_values["DEFAULT_PYTHON_VERSION"] = questionary.text(
        "Default Python version (e.g., 3.12.9):", default="3.12.9"
    ).ask()

    # Developer name
    env_values["DEVELOPER_NAME"] = questionary.text(
        "Developer name:", instruction="Your name will be used in the devcontainer"
    ).ask()

    # Git credentials
    env_values["GIT_PROVIDER_URL"] = questionary.text("Git provider URL:", default="github.com").ask()

    env_values["GIT_USER"] = questionary.text("Git username:", instruction="Your username for authentication").ask()

    env_values["GIT_USER_EMAIL"] = questionary.text("Git email:", instruction="Your email for Git commits").ask()

    env_values["GIT_TOKEN"] = questionary.password(
        "Git token:", instruction="Your personal access token (will be stored in the config)"
    ).ask()

    # Extra packages
    env_values["EXTRA_APT_PACKAGES"] = questionary.text("Extra APT packages (space-separated):", default="").ask()

    return env_values


def prompt_aws_profile_map() -> Dict[str, Any]:
    """Prompt for AWS profile map."""
    if questionary.confirm("Do you want to configure AWS profiles?", default=True).ask():
        print("\nEnter your AWS profile configuration in JSON format.")
        print("Example:")
        # Split the example into multiple lines to avoid linting issues
        print("{")
        print('  "default": {')
        print('    "region": "us-west-2",')
        print('    "sso_start_url": "https://example.awsapps.com/start",')
        print('    "sso_region": "us-west-2",')
        print('    "account_name": "example-dev-account",')
        print('    "account_id": "123456789012",')
        print('    "role_name": "DeveloperAccess"')
        print("  }")
        print("}")

        print(
            "\nFor more information, see: "
            "https://github.com/caylent-solutions/devcontainer#4-configure-aws-profile-map-optional"
        )

        # Add a newline before the prompt to make it clearer where to start typing
        print("\nEnter AWS profile map JSON: (Finish with 'Esc then Enter')")
        aws_profile_map_json = questionary.text(
            "",  # Empty prompt since we already printed the instruction
            multiline=True,
            validate=JsonValidator(),
        ).ask()

        return json.loads(aws_profile_map_json)

    return {}


def create_template_interactive() -> Dict[str, Any]:
    """Create a template interactively."""
    template = {}

    # Environment values
    log("INFO", "Configuring environment variables...")
    env_values = prompt_env_values()
    template["containerEnv"] = env_values

    # AWS profile map
    if env_values["AWS_CONFIG_ENABLED"] == "true":
        log("INFO", "Configuring AWS profiles...")
        template["aws_profile_map"] = prompt_aws_profile_map()
    else:
        template["aws_profile_map"] = {}

    # Add version information
    template["cli_version"] = __version__

    return template


def save_template_to_file(template_data: Dict[str, Any], name: str) -> None:
    """Save template to file."""
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR, exist_ok=True)

    # Ensure version information is included
    if "cli_version" not in template_data:
        template_data["cli_version"] = __version__

    template_path = os.path.join(TEMPLATES_DIR, f"{name}.json")

    with open(template_path, "w") as f:
        json.dump(template_data, f, indent=2)
        f.write("\n")  # Add newline at end of file

    log("OK", f"Template saved to {template_path}")


def load_template_from_file(name: str) -> Dict[str, Any]:
    """Load template from file."""
    template_path = os.path.join(TEMPLATES_DIR, f"{name}.json")

    if not os.path.exists(template_path):
        log("ERR", f"Template {name} not found")
        import sys

        sys.exit(1)

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
                # Warn about version mismatch
                msg = f"Template created with CLI v{template_version}, but you're using v{current_version}"
                log("WARN", msg)

                choices = [
                    "Upgrade the template to the current format",
                    "Create a new template from scratch",
                    "Use the template anyway (may cause issues)",
                    "Exit without making changes",
                ]

                choice = questionary.select(
                    "The template format may be incompatible. What would you like to do?", choices=choices
                ).ask()

                if choice == choices[0]:  # Upgrade
                    template_data = upgrade_template(template_data)
                    log("OK", f"Template '{name}' upgraded to version {current_version}")
                elif choice == choices[1]:  # Create new
                    log("INFO", "Creating a new template instead...")
                    return create_template_interactive()
                elif choice == choices[3]:  # Exit
                    log("INFO", "Operation cancelled by user")
                    import sys

                    sys.exit(0)
                # For choice[2], we continue with the existing template
        except ValueError:
            # If version parsing fails, just continue with the template as is
            log("WARN", f"Could not parse template version: {template_version}")
    else:
        # Add version information for older templates
        template_data["cli_version"] = __version__
        log("INFO", f"Added version information ({__version__}) to template")

    return template_data


def upgrade_template(template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Upgrade a template to the current format."""
    new_template = {"cli_version": __version__}

    # Handle containerEnv or env_values
    if "containerEnv" in template_data:
        new_template["containerEnv"] = template_data["containerEnv"]
    elif "env_values" in template_data:
        new_template["containerEnv"] = template_data["env_values"]
    else:
        # If neither exists, create a new containerEnv
        log("INFO", "No environment values found in template, prompting for new values")
        new_template["containerEnv"] = prompt_env_values()

    # Handle AWS profile map
    if "aws_profile_map" in template_data:
        new_template["aws_profile_map"] = template_data["aws_profile_map"]
    else:
        # If AWS is enabled, prompt for profile map
        if new_template["containerEnv"].get("AWS_CONFIG_ENABLED") == "true":
            log("INFO", "AWS is enabled but no profile map found, prompting for AWS configuration")
            new_template["aws_profile_map"] = prompt_aws_profile_map()
        else:
            new_template["aws_profile_map"] = {}

    return new_template


def apply_template(template_data: Dict[str, Any], target_path: str, source_dir: str) -> None:
    """Apply template to target path."""
    # Copy .devcontainer folder
    source_devcontainer = os.path.join(source_dir, ".devcontainer")
    target_devcontainer = os.path.join(target_path, ".devcontainer")

    if os.path.exists(target_devcontainer):
        shutil.rmtree(target_devcontainer)

    log("INFO", f"Copying .devcontainer folder to {target_path}...")
    shutil.copytree(source_devcontainer, target_devcontainer)

    # Remove example files if not in manual mode
    example_files = [
        os.path.join(target_devcontainer, "example-container-env-values.json"),
        os.path.join(target_devcontainer, "example-aws-profile-map.json"),
    ]

    for file_path in example_files:
        if os.path.exists(file_path):
            os.remove(file_path)

    # Create environment variables file
    env_file_path = os.path.join(target_path, "devcontainer-environment-variables.json")
    with open(env_file_path, "w") as f:
        # Use containerEnv directly from template or create it if using old format
        if "containerEnv" in template_data:
            env_data = template_data
        else:
            # Handle old format templates for backward compatibility
            env_data = {"containerEnv": template_data.get("env_values", {})}

        json.dump(env_data, f, indent=2)
        f.write("\n")  # Add newline at end of file

    log("OK", f"Environment variables saved to {env_file_path}")

    # Create AWS profile map if needed
    # Check both containerEnv and env_values for backward compatibility
    container_env = template_data.get("containerEnv", {})
    env_values = template_data.get("env_values", {})
    aws_config_enabled = container_env.get("AWS_CONFIG_ENABLED", env_values.get("AWS_CONFIG_ENABLED", "false"))

    if aws_config_enabled == "true" and template_data.get("aws_profile_map"):
        aws_map_path = os.path.join(target_devcontainer, "aws-profile-map.json")
        with open(aws_map_path, "w") as f:
            json.dump(template_data["aws_profile_map"], f, indent=2)
            f.write("\n")  # Add newline at end of file

        log("OK", f"AWS profile map saved to {aws_map_path}")

    log("OK", "Template applied successfully")
