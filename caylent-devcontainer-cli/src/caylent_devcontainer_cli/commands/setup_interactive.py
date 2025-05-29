"""Interactive setup functionality for the Caylent Devcontainer CLI."""

import json
import os
import shutil
from typing import Any, Dict, List, Optional

import questionary
from questionary import ValidationError, Validator

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
        print(
            """{
  "default": {
    "region": "us-west-2",
    "sso_start_url": "https://example.awsapps.com/start",
    "sso_region": "us-west-2",
    "account_name": "example-dev-account",
    "account_id": "123456789012",
    "role_name": "DeveloperAccess"
  }
}"""
        )
        print(
            "\nFor more information, see: "
            "https://github.com/caylent-solutions/devcontainer#4-configure-aws-profile-map-optional"
        )
        aws_profile_map_json = questionary.text(
            "\nEnter AWS profile map JSON:",
            multiline=True,
            validate=JsonValidator(),
            instruction="(Finish with 'Esc then Enter')",
        ).ask()

        return json.loads(aws_profile_map_json)

    return {}


def create_template_interactive() -> Dict[str, Any]:
    """Create a template interactively."""
    template = {}

    # Environment values
    log("INFO", "Configuring environment variables...")
    template["env_values"] = prompt_env_values()

    # AWS profile map
    if template["env_values"]["AWS_CONFIG_ENABLED"] == "true":
        log("INFO", "Configuring AWS profiles...")
        template["aws_profile_map"] = prompt_aws_profile_map()
    else:
        template["aws_profile_map"] = {}

    return template


def save_template_to_file(template_data: Dict[str, Any], name: str) -> None:
    """Save template to file."""
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR, exist_ok=True)

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
        return json.load(f)


def apply_template(template_data: Dict[str, Any], target_path: str, source_dir: str) -> None:
    """Apply template to target path."""
    # Copy .devcontainer folder
    source_devcontainer = os.path.join(source_dir, ".devcontainer")
    target_devcontainer = os.path.join(target_path, ".devcontainer")

    if os.path.exists(target_devcontainer):
        shutil.rmtree(target_devcontainer)

    log("INFO", f"Copying .devcontainer folder to {target_path}...")
    shutil.copytree(source_devcontainer, target_devcontainer)

    # Create environment variables file
    env_file_path = os.path.join(target_path, "devcontainer-environment-variables.json")
    with open(env_file_path, "w") as f:
        json.dump(template_data["env_values"], f, indent=2)
        f.write("\n")  # Add newline at end of file

    log("OK", f"Environment variables saved to {env_file_path}")

    # Create AWS profile map if needed
    if template_data["env_values"]["AWS_CONFIG_ENABLED"] == "true" and template_data["aws_profile_map"]:
        aws_map_path = os.path.join(target_devcontainer, "aws-profile-map.json")
        with open(aws_map_path, "w") as f:
            json.dump(template_data["aws_profile_map"], f, indent=2)
            f.write("\n")  # Add newline at end of file

        log("OK", f"AWS profile map saved to {aws_map_path}")

    log("OK", "Template applied successfully")
