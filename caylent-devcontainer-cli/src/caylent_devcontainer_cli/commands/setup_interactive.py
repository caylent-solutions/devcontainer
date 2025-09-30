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

    try:
        print("\n⚠️  Do not press enter after your answer for this prompt. ⚠️")
        result = questionary.confirm("Do you want to use a saved template?", default=True).ask()
        if result is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        # Small delay to ensure proper terminal handling
        import time

        time.sleep(0.1)
        return result
    except KeyboardInterrupt:
        log("INFO", "Setup cancelled by user.")
        import sys

        sys.exit(0)


def select_template() -> Optional[str]:
    """Prompt the user to select a template."""
    templates = list_templates()

    if not templates:
        return None

    templates.append("< Go back")

    try:
        selected = questionary.select("Select a template:", choices=templates).ask()
        if selected is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)

        if selected == "< Go back":
            return None

        return selected
    except KeyboardInterrupt:
        log("INFO", "Setup cancelled by user.")
        import sys

        sys.exit(0)


def prompt_save_template() -> bool:
    """Ask if the user wants to save the template."""
    try:
        result = questionary.confirm(
            "Do you want to save this configuration as a reusable template?", default=False
        ).ask()
        if result is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        return result
    except KeyboardInterrupt:
        log("INFO", "Setup cancelled by user.")
        import sys

        sys.exit(0)


def prompt_template_name() -> str:
    """Prompt for template name."""
    try:
        result = questionary.text("Enter a name for this template:", validate=lambda text: len(text) > 0).ask()
        if result is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        return result
    except KeyboardInterrupt:
        log("INFO", "Setup cancelled by user.")
        import sys

        sys.exit(0)


def prompt_env_values() -> Dict[str, Any]:
    """Prompt for environment values."""
    env_values = {}

    try:
        # AWS Config Enabled
        aws_config = questionary.select("Enable AWS configuration?", choices=["true", "false"], default="true").ask()
        if aws_config is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        env_values["AWS_CONFIG_ENABLED"] = aws_config

        # Git branch
        git_branch = questionary.text(
            "Default Git branch (e.g., main):",
            default="main",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a Git branch name",
        ).ask()
        if git_branch is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        env_values["DEFAULT_GIT_BRANCH"] = git_branch

        # Python version
        python_version = questionary.text(
            "Default Python version (e.g., 3.12.9):",
            default="3.12.9",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a Python version",
        ).ask()
        if python_version is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        env_values["DEFAULT_PYTHON_VERSION"] = python_version

        # Developer name
        dev_name = questionary.text(
            "Developer name:",
            instruction="Your name will be used in the devcontainer",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a developer name",
        ).ask()
        if dev_name is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        env_values["DEVELOPER_NAME"] = dev_name

        # Git credentials
        git_provider = questionary.text(
            "Git provider URL:",
            default="github.com",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a Git provider URL",
        ).ask()
        if git_provider is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        env_values["GIT_PROVIDER_URL"] = git_provider

        git_user = questionary.text(
            "Git username:",
            instruction="Your username for authentication",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a Git username",
        ).ask()
        if git_user is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        env_values["GIT_USER"] = git_user

        git_email = questionary.text(
            "Git email:",
            instruction="Your email for Git commits",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a Git email",
        ).ask()
        if git_email is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        env_values["GIT_USER_EMAIL"] = git_email

        gitignore_header = (
            "\n\033[35mAll 3 files that contain secrets will automatically be added to your .gitignore; "
            "be sure to commit these changes for your protection:\033[0m"
        )
        print(gitignore_header)
        print("- shell.env \033[35m(contains Git token)\033[0m")
        print("- devcontainer-environment-variables.json \033[35m(contains Git token)\033[0m")
        aws_file_desc = (
            "- .devcontainer/aws-profile-map.json \033[35m(contains aws account id "
            "if you chose to create an AWS config)\033[0m"
        )
        print(aws_file_desc)
        print()

        git_token = questionary.password(
            "Git token:",
            instruction="Your personal access token (will be stored in the config)",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a Git token",
        ).ask()
        if git_token is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        env_values["GIT_TOKEN"] = git_token

        # Extra packages
        extra_packages = questionary.text("Extra APT packages (space-separated):", default="").ask()
        if extra_packages is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        env_values["EXTRA_APT_PACKAGES"] = extra_packages

        # Pager selection
        pager_choice = questionary.select(
            "Select default pager:", choices=["cat", "less", "more", "most"], default="cat"
        ).ask()
        if pager_choice is None:
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
        env_values["PAGER"] = pager_choice

        # AWS output format (only if AWS is enabled)
        if aws_config == "true":
            aws_output = questionary.select(
                "Select default AWS CLI output format:", choices=["json", "table", "text", "yaml"], default="json"
            ).ask()
            if aws_output is None:
                log("INFO", "Setup cancelled by user.")
                import sys

                sys.exit(0)
            env_values["AWS_DEFAULT_OUTPUT"] = aws_output

        return env_values
    except KeyboardInterrupt:
        log("INFO", "Setup cancelled by user.")
        import sys

        sys.exit(0)


def parse_standard_profile(profile_text: str) -> Dict[str, str]:
    """Parse standard AWS profile format into dictionary."""
    profile = {}
    for line in profile_text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("[") or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            profile[key] = value
    return profile


def validate_standard_profile(profile: Dict[str, str]) -> Optional[str]:
    """Validate standard profile has required fields."""
    required_fields = ["sso_start_url", "sso_region", "sso_account_name", "sso_account_id", "sso_role_name", "region"]
    missing = [field for field in required_fields if field not in profile]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"

    empty = [field for field in required_fields if field in profile and not profile[field].strip()]
    if empty:
        return f"Empty values for required fields: {', '.join(empty)}"

    return None


def convert_standard_to_json(profiles: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    """Convert standard format profiles to JSON format."""
    json_profiles = {}
    for name, profile in profiles.items():
        json_profiles[name] = {
            "region": profile["region"],
            "sso_start_url": profile["sso_start_url"],
            "sso_region": profile["sso_region"],
            "account_name": profile["sso_account_name"],
            "account_id": profile["sso_account_id"],
            "role_name": profile["sso_role_name"],
        }
    return json_profiles


def prompt_aws_profile_map() -> Dict[str, Any]:
    """Prompt for AWS profile map."""
    if not questionary.confirm("Do you want to configure AWS profiles?", default=True).ask():
        return {}

    # Present two options
    input_method = questionary.select(
        "How would you like to provide your AWS profiles?",
        choices=["Standard format (enter profiles one by one)", "JSON format (paste complete configuration)"],
    ).ask()

    if input_method == "Standard format (enter profiles one by one)":
        print("\nEnter AWS profiles in standard format. Example:")
        print("[default]")
        print("sso_start_url       = https://example.awsapps.com/start")
        print("sso_region          = us-west-2")
        print("sso_account_name    = example-dev-account")
        print("sso_account_id      = 123456789012")
        print("sso_role_name       = DeveloperAccess")
        print("region              = us-west-2")

        profiles = {}

        while True:
            profile_name = questionary.text(
                "Enter profile name (e.g., 'default'):", validate=lambda text: len(text.strip()) > 0
            ).ask()

            while True:
                print(f"\nEnter configuration for profile '{profile_name}':")
                profile_text = questionary.text("Paste the profile configuration:", multiline=True).ask()

                parsed_profile = parse_standard_profile(profile_text)
                error = validate_standard_profile(parsed_profile)

                if error:
                    print(f"\nError: {error}")
                    print("Please re-enter the profile configuration.")
                    continue

                profiles[profile_name] = parsed_profile
                break

            if not questionary.confirm("Would you like to add another AWS profile?", default=False).ask():
                break

        return convert_standard_to_json(profiles)

    else:  # JSON format
        print("\nEnter your AWS profile configuration in JSON format.")
        print("Example:")
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
        print("\nEnter AWS profile map JSON: (Finish with 'Esc then Enter')")
        aws_profile_map_json = questionary.text(
            "",
            multiline=True,
            validate=JsonValidator(),
        ).ask()
        return json.loads(aws_profile_map_json)


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

    # Always update version information to current version
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

    # Ensure the cli_version is updated to the current version
    new_template["cli_version"] = __version__

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

    # Check and create .tool-versions file
    container_env = template_data.get("containerEnv", {})
    env_values = template_data.get("env_values", {})
    python_version = container_env.get("DEFAULT_PYTHON_VERSION") or env_values.get("DEFAULT_PYTHON_VERSION")

    if python_version:
        from caylent_devcontainer_cli.commands.setup import check_and_create_tool_versions

        check_and_create_tool_versions(target_path, python_version)

    # Create AWS profile map if needed
    # Check both containerEnv and env_values for backward compatibility
    aws_config_enabled = container_env.get("AWS_CONFIG_ENABLED", env_values.get("AWS_CONFIG_ENABLED", "false"))

    if aws_config_enabled == "true" and template_data.get("aws_profile_map"):
        aws_map_path = os.path.join(target_devcontainer, "aws-profile-map.json")
        with open(aws_map_path, "w") as f:
            json.dump(template_data["aws_profile_map"], f, indent=2)
            f.write("\n")  # Add newline at end of file

        log("OK", f"AWS profile map saved to {aws_map_path}")

    log("OK", "Template applied successfully")


def apply_template_without_clone(template_data: Dict[str, Any], target_path: str) -> None:
    """Apply template to target path without overwriting .devcontainer directory."""
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

    # Check and create .tool-versions file
    container_env = template_data.get("containerEnv", {})
    env_values = template_data.get("env_values", {})
    python_version = container_env.get("DEFAULT_PYTHON_VERSION") or env_values.get("DEFAULT_PYTHON_VERSION")

    if python_version:
        from caylent_devcontainer_cli.commands.setup import check_and_create_tool_versions

        check_and_create_tool_versions(target_path, python_version)

    # Create AWS profile map if needed
    # Check both containerEnv and env_values for backward compatibility
    aws_config_enabled = container_env.get("AWS_CONFIG_ENABLED", env_values.get("AWS_CONFIG_ENABLED", "false"))

    if aws_config_enabled == "true" and template_data.get("aws_profile_map"):
        target_devcontainer = os.path.join(target_path, ".devcontainer")
        aws_map_path = os.path.join(target_devcontainer, "aws-profile-map.json")
        with open(aws_map_path, "w") as f:
            json.dump(template_data["aws_profile_map"], f, indent=2)
            f.write("\n")  # Add newline at end of file

        log("OK", f"AWS profile map saved to {aws_map_path}")

    log("OK", "Template applied successfully (existing .devcontainer preserved)")
