"""Interactive setup functionality for the Caylent Devcontainer CLI."""

import json
import os
from typing import Any, Dict, List, Optional

import questionary
import semver
from questionary import ValidationError, Validator

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.constants import ENV_VARS_FILENAME, KNOWN_KEYS, SHELL_ENV_FILENAME
from caylent_devcontainer_cli.utils.fs import load_json_config, write_json_file, write_project_files
from caylent_devcontainer_cli.utils.template import ensure_templates_dir, get_template_names, get_template_path
from caylent_devcontainer_cli.utils.ui import (
    ask_or_exit,
    exit_cancelled,
    exit_with_error,
    log,
    mask_password,
    prompt_with_confirmation,
    validate_ssh_key_file,
)


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
    ensure_templates_dir()
    return get_template_names()


def prompt_use_template() -> bool:
    """Ask if the user wants to use a saved template."""
    templates = list_templates()

    if not templates:
        log("INFO", "No saved templates found.")
        return False

    print("\n⚠️  Do not press enter after your answer for this prompt. ⚠️")
    result = ask_or_exit(questionary.confirm("Do you want to use a saved template?", default=True))
    # Small delay to ensure proper terminal handling
    import time

    time.sleep(0.1)
    return result


def select_template() -> Optional[str]:
    """Prompt the user to select a template."""
    templates = list_templates()

    if not templates:
        return None

    templates.append("< Go back")

    selected = ask_or_exit(questionary.select("Select a template:", choices=templates))

    if selected == "< Go back":
        return None

    return selected


def prompt_save_template() -> bool:
    """Ask if the user wants to save the template."""
    return ask_or_exit(
        questionary.confirm(
            "Do you want to save this configuration as a reusable template?",
            default=False,
        )
    )


def prompt_template_name() -> str:
    """Prompt for template name."""
    return ask_or_exit(questionary.text("Enter a name for this template:", validate=lambda text: len(text) > 0))


def prompt_env_values() -> Dict[str, Any]:
    """Prompt for environment values."""
    env_values = {}

    # AWS Config Enabled
    aws_config = ask_or_exit(questionary.select("Enable AWS configuration?", choices=["true", "false"], default="true"))
    env_values["AWS_CONFIG_ENABLED"] = aws_config

    # CICD mode (always false for interactive setup)
    env_values["CICD"] = "false"

    # Git branch
    git_branch = ask_or_exit(
        questionary.text(
            "Default Git branch (e.g., main):",
            default="main",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a Git branch name",
        )
    )
    env_values["DEFAULT_GIT_BRANCH"] = git_branch

    # Developer name
    dev_name = ask_or_exit(
        questionary.text(
            "Developer name:",
            instruction="Your name will be used in the devcontainer",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a developer name",
        )
    )
    env_values["DEVELOPER_NAME"] = dev_name

    # Git credentials
    git_provider = ask_or_exit(
        questionary.text(
            "Git provider URL:",
            default="github.com",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a Git provider URL",
        )
    )
    env_values["GIT_PROVIDER_URL"] = git_provider

    git_user = ask_or_exit(
        questionary.text(
            "Git username:",
            instruction="Your username for authentication",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a Git username",
        )
    )
    env_values["GIT_USER"] = git_user

    git_email = ask_or_exit(
        questionary.text(
            "Git email:",
            instruction="Your email for Git commits",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a Git email",
        )
    )
    env_values["GIT_USER_EMAIL"] = git_email

    gitignore_header = (
        "\n\033[35mAll 3 files that contain secrets will automatically be added to your .gitignore; "
        "be sure to commit these changes for your protection:\033[0m"
    )
    print(gitignore_header)
    print(f"- {SHELL_ENV_FILENAME} \033[35m(contains Git token)\033[0m")
    print(f"- {ENV_VARS_FILENAME} \033[35m(contains Git token)\033[0m")
    aws_file_desc = (
        "- .devcontainer/aws-profile-map.json \033[35m(contains aws account id "
        "if you chose to create an AWS config)\033[0m"
    )
    print(aws_file_desc)
    print()

    git_token = ask_or_exit(
        questionary.password(
            "Git token:",
            instruction="Your personal access token (will be stored in the config)",
            validate=lambda text: len(text.strip()) > 0 or "You must provide a Git token",
        )
    )
    env_values["GIT_TOKEN"] = git_token

    # Extra packages
    extra_packages = ask_or_exit(questionary.text("Extra APT packages (space-separated):", default=""))
    env_values["EXTRA_APT_PACKAGES"] = extra_packages

    # Pager selection
    pager_choice = ask_or_exit(
        questionary.select(
            "Select default pager:",
            choices=["cat", "less", "more", "most"],
            default="cat",
        )
    )
    env_values["PAGER"] = pager_choice

    # AWS output format (only if AWS is enabled)
    if aws_config == "true":
        aws_output = ask_or_exit(
            questionary.select(
                "Select default AWS CLI output format:",
                choices=["json", "table", "text", "yaml"],
                default="json",
            )
        )
        env_values["AWS_DEFAULT_OUTPUT"] = aws_output

    return env_values


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
    required_fields = [
        "sso_start_url",
        "sso_region",
        "sso_account_name",
        "sso_account_id",
        "sso_role_name",
        "region",
    ]
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
    if not ask_or_exit(questionary.confirm("Do you want to configure AWS profiles?", default=True)):
        return {}

    # Present two options
    input_method = ask_or_exit(
        questionary.select(
            "How would you like to provide your AWS profiles?",
            choices=[
                "Standard format (enter profiles one by one)",
                "JSON format (paste complete configuration)",
            ],
        )
    )

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
            profile_name = ask_or_exit(
                questionary.text(
                    "Enter profile name (e.g., 'default'):",
                    validate=lambda text: len(text.strip()) > 0,
                )
            )

            while True:
                print(f"\nEnter configuration for profile '{profile_name}':")
                profile_text = ask_or_exit(questionary.text("Paste the profile configuration:", multiline=True))

                parsed_profile = parse_standard_profile(profile_text)
                error = validate_standard_profile(parsed_profile)

                if error:
                    print(f"\nError: {error}")
                    print("Please re-enter the profile configuration.")
                    continue

                profiles[profile_name] = parsed_profile
                break

            if not ask_or_exit(questionary.confirm("Would you like to add another AWS profile?", default=False)):
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
        aws_profile_map_json = ask_or_exit(
            questionary.text(
                "",
                multiline=True,
                validate=JsonValidator(),
            )
        )
        return json.loads(aws_profile_map_json)


def prompt_ssh_key() -> str:
    """Prompt for SSH private key file path, validate, and return key content.

    Implements the full SSH key input validation flow:
    1. Prompt for file path
    2. Validate file (exists, readable, format, ssh-keygen)
    3. Display fingerprint and ask for confirmation
    4. Read and normalize key content

    Returns:
        The normalized SSH private key content.

    Raises:
        SystemExit: If the user cancels at any point.
    """
    while True:
        key_path = ask_or_exit(
            questionary.text("Enter the absolute path to your SSH private key file (e.g. /Users/you/.ssh/id_rsa):")
        )
        key_path = os.path.expanduser(key_path)

        success, message = validate_ssh_key_file(key_path)
        if not success:
            log("ERR", message)
            continue

        # Display fingerprint and confirm
        log("INFO", f"SSH key fingerprint: {message}")
        confirmed = ask_or_exit(questionary.confirm("Is this correct?", default=True))
        if not confirmed:
            continue

        # Read and normalize key content
        with open(key_path, "r") as f:
            content = f.read()
        content = content.replace("\r", "")
        if not content.endswith("\n"):
            content += "\n"

        return content


def prompt_custom_env_vars(known_keys: set) -> Dict[str, str]:
    """Prompt for additional custom environment variables.

    Implements the free-form loop with conflict detection:
    1. Ask if user wants to add custom variables
    2. Prompt for key name (validate against known_keys and already-entered keys)
    3. Prompt for value
    4. Display and confirm
    5. Ask to add another

    Args:
        known_keys: Set of known/built-in key names to check for conflicts.

    Returns:
        Dict of custom variable name-value pairs.

    Raises:
        SystemExit: If the user cancels at any point.
    """
    if not ask_or_exit(questionary.confirm("Add custom environment variables?", default=False)):
        return {}

    custom_vars: Dict[str, str] = {}
    entered_keys: set = set()

    while True:
        # Prompt for key name with conflict detection
        while True:
            key = ask_or_exit(
                questionary.text(
                    "Enter variable name:",
                    validate=lambda t: len(t.strip()) > 0 or "Variable name must not be empty",
                )
            )

            if key in known_keys:
                log(
                    "WARN",
                    f"The key '{key}' already exists (built-in key). Please enter a different key name.",
                )
                continue
            if key in entered_keys:
                log(
                    "WARN",
                    f"The key '{key}' already exists (already entered). Please enter a different key name.",
                )
                continue
            break

        # Prompt for value (no constraints)
        value = ask_or_exit(questionary.text(f"Enter value for {key}:"))

        # Display and confirm
        log("INFO", f"Custom variable: {key} = {value}")
        confirmed = ask_or_exit(questionary.confirm("Is this correct?", default=True))
        if confirmed:
            custom_vars[key] = value
            entered_keys.add(key)

        # Add another?
        if not ask_or_exit(questionary.confirm("Add another custom variable?", default=False)):
            break

    return custom_vars


def create_template_interactive() -> Dict[str, Any]:
    """Create a template interactively using the full 17-step flow.

    All prompts use the universal input confirmation pattern
    (display value, "Is this correct?", re-prompt if no).

    Steps:
    1. AWS config enabled (select)
    2. Default Git branch (text)
    3. Default Python version (text)
    4. Developer name (text)
    5. Git provider URL (text, hostname only)
    6. Git authentication method (select)
    7. Git username (text)
    8. Git email (text)
    9. Git token (password) — only if token method
    10. SSH private key path — only if SSH method
    11. Extra APT packages (text)
    12. Pager (select)
    13. AWS output format (select) — only if AWS enabled
    14. Host proxy (select)
    15. Host proxy URL (text) — only if host proxy true
    16. Custom environment variables (loop)
    17. AWS profile map — only if AWS enabled

    Returns:
        Complete template dict with containerEnv, aws_profile_map,
        cli_version, and optionally ssh_private_key.
    """
    env_values: Dict[str, Any] = {}
    template: Dict[str, Any] = {}

    log("INFO", "Configuring environment variables...")

    # Step 1: AWS config enabled
    aws_config = prompt_with_confirmation(
        lambda: questionary.select(
            "Enable AWS configuration?",
            choices=["true", "false"],
            default="true",
        )
    )
    env_values["AWS_CONFIG_ENABLED"] = aws_config

    # Step 2: Default Git branch
    git_branch = prompt_with_confirmation(
        lambda: questionary.text(
            "Default Git branch:",
            default="main",
            validate=lambda t: len(t.strip()) > 0 or "Must be non-empty",
        )
    )
    env_values["DEFAULT_GIT_BRANCH"] = git_branch

    # Step 3: Developer name
    dev_name = prompt_with_confirmation(
        lambda: questionary.text(
            "Developer name:",
            validate=lambda t: len(t.strip()) > 0 or "Must be non-empty",
        )
    )
    env_values["DEVELOPER_NAME"] = dev_name

    # Step 4: Git provider URL (hostname only, no protocol, must contain dot)
    git_provider = prompt_with_confirmation(
        lambda: questionary.text(
            "Git provider URL (hostname only, e.g., github.com):",
            default="github.com",
            validate=lambda t: (
                (len(t.strip()) > 0 and "." in t and not t.startswith("http://") and not t.startswith("https://"))
                or "Must be hostname only (no protocol prefix) with at least one dot"
            ),
        )
    )
    env_values["GIT_PROVIDER_URL"] = git_provider

    # Step 5: Git authentication method
    auth_method = prompt_with_confirmation(
        lambda: questionary.select(
            "Git authentication method:",
            choices=["token", "ssh"],
            default="token",
        )
    )
    env_values["GIT_AUTH_METHOD"] = auth_method

    # Step 6: Git username
    git_user = prompt_with_confirmation(
        lambda: questionary.text(
            "Git username:",
            validate=lambda t: len(t.strip()) > 0 or "Must be non-empty",
        )
    )
    env_values["GIT_USER"] = git_user

    # Step 7: Git email
    git_email = prompt_with_confirmation(
        lambda: questionary.text(
            "Git email:",
            validate=lambda t: len(t.strip()) > 0 or "Must be non-empty",
        )
    )
    env_values["GIT_USER_EMAIL"] = git_email

    # Step 8: Git token (only if token method)
    if auth_method == "token":
        git_token = prompt_with_confirmation(
            lambda: questionary.password(
                "Git token (personal access token):",
                validate=lambda t: len(t.strip()) > 0 or "Must be non-empty",
            ),
            display_fn=mask_password,
        )
        env_values["GIT_TOKEN"] = git_token

    # Step 9: SSH private key (only if SSH method)
    if auth_method == "ssh":
        log("INFO", "Configuring SSH key authentication...")
        ssh_key_content = prompt_ssh_key()
        template["ssh_private_key"] = ssh_key_content

    # Step 10: Extra APT packages
    extra_packages = prompt_with_confirmation(
        lambda: questionary.text(
            "Extra APT packages (space-separated, leave empty for none):",
            default="",
        )
    )
    env_values["EXTRA_APT_PACKAGES"] = extra_packages

    # Step 11: Pager
    pager = prompt_with_confirmation(
        lambda: questionary.select(
            "Select default pager:",
            choices=["cat", "less", "more", "most"],
            default="cat",
        )
    )
    env_values["PAGER"] = pager

    # Step 12: AWS output format (only if AWS enabled)
    if aws_config == "true":
        aws_output = prompt_with_confirmation(
            lambda: questionary.select(
                "Select default AWS CLI output format:",
                choices=["json", "table", "text", "yaml"],
                default="json",
            )
        )
        env_values["AWS_DEFAULT_OUTPUT"] = aws_output

    # Step 13: Host proxy
    host_proxy = prompt_with_confirmation(
        lambda: questionary.select(
            "Enable host proxy?",
            choices=["true", "false"],
            default="false",
        )
    )
    env_values["HOST_PROXY"] = host_proxy

    # Step 14: Host proxy URL (only if host proxy true)
    if host_proxy == "true":
        proxy_url = prompt_with_confirmation(
            lambda: questionary.text(
                "Host proxy URL (e.g., http://host.docker.internal:3128):",
                validate=lambda t: (
                    (t.startswith("http://") or t.startswith("https://")) or "Must start with http:// or https://"
                ),
            )
        )
        env_values["HOST_PROXY_URL"] = proxy_url
    else:
        env_values["HOST_PROXY_URL"] = ""

    # Step 15: Custom environment variables
    log("INFO", "You can add additional custom environment variables.")
    custom_vars = prompt_custom_env_vars(KNOWN_KEYS)
    env_values.update(custom_vars)

    template["containerEnv"] = env_values

    # Step 16: AWS profile map (only if AWS enabled)
    if aws_config == "true":
        log("INFO", "Configuring AWS profiles...")
        template["aws_profile_map"] = prompt_aws_profile_map()
    else:
        template["aws_profile_map"] = {}

    # Add CLI version
    template["cli_version"] = __version__

    return template


def _prompt_edit(key, current_value, prompt_fn, display_fn=None):
    """Prompt to edit a single template setting.

    Shows the current value and asks whether to change it.  When the user
    declines, the original value is returned unchanged.

    Args:
        key: The setting name (shown to the user).
        current_value: The current value for this setting.
        prompt_fn: Callable returning a questionary question for the new value.
        display_fn: Optional display formatter (e.g. ``mask_password``).

    Returns:
        The new value (or the original if the user declined).
    """
    if display_fn is not None:
        char_count = len(str(current_value))
        display = f"****** ({char_count} characters)"
    else:
        display = current_value
    log("INFO", f"{key}: {display}")
    if ask_or_exit(questionary.confirm(f"Change {key}?", default=False)):
        return prompt_with_confirmation(prompt_fn, display_fn=display_fn)
    return current_value


def edit_template_interactive(template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Edit an existing template interactively.

    Walks through every template setting in the same order as
    ``create_template_interactive()``.  For each setting the current value
    is displayed and the user is asked whether to change it (default: No).

    Args:
        template_data: Existing template dict (must contain ``containerEnv``).

    Returns:
        Updated template dict.
    """
    env = template_data.get("containerEnv", {})
    template: Dict[str, Any] = {}

    log("INFO", "Editing template settings...")

    # Step 1: AWS config enabled
    aws_config = _prompt_edit(
        "AWS_CONFIG_ENABLED",
        env.get("AWS_CONFIG_ENABLED", "false"),
        lambda: questionary.select(
            "Enable AWS configuration?",
            choices=["true", "false"],
            default=env.get("AWS_CONFIG_ENABLED", "false"),
        ),
    )
    env["AWS_CONFIG_ENABLED"] = aws_config

    # Step 2: Default Git branch
    env["DEFAULT_GIT_BRANCH"] = _prompt_edit(
        "DEFAULT_GIT_BRANCH",
        env.get("DEFAULT_GIT_BRANCH", "main"),
        lambda: questionary.text(
            "Default Git branch:",
            default=env.get("DEFAULT_GIT_BRANCH", "main"),
            validate=lambda t: len(t.strip()) > 0 or "Must be non-empty",
        ),
    )

    # Step 3: Developer name
    env["DEVELOPER_NAME"] = _prompt_edit(
        "DEVELOPER_NAME",
        env.get("DEVELOPER_NAME", ""),
        lambda: questionary.text(
            "Developer name:",
            default=env.get("DEVELOPER_NAME", ""),
            validate=lambda t: len(t.strip()) > 0 or "Must be non-empty",
        ),
    )

    # Step 4: Git provider URL
    env["GIT_PROVIDER_URL"] = _prompt_edit(
        "GIT_PROVIDER_URL",
        env.get("GIT_PROVIDER_URL", "github.com"),
        lambda: questionary.text(
            "Git provider URL (hostname only, e.g., github.com):",
            default=env.get("GIT_PROVIDER_URL", "github.com"),
            validate=lambda t: (
                (len(t.strip()) > 0 and "." in t and not t.startswith("http://") and not t.startswith("https://"))
                or "Must be hostname only (no protocol prefix) with at least one dot"
            ),
        ),
    )

    # Step 5: Git authentication method
    auth_method = _prompt_edit(
        "GIT_AUTH_METHOD",
        env.get("GIT_AUTH_METHOD", "token"),
        lambda: questionary.select(
            "Git authentication method:",
            choices=["token", "ssh"],
            default=env.get("GIT_AUTH_METHOD", "token"),
        ),
    )
    env["GIT_AUTH_METHOD"] = auth_method

    # Step 6: Git username
    env["GIT_USER"] = _prompt_edit(
        "GIT_USER",
        env.get("GIT_USER", ""),
        lambda: questionary.text(
            "Git username:",
            default=env.get("GIT_USER", ""),
            validate=lambda t: len(t.strip()) > 0 or "Must be non-empty",
        ),
    )

    # Step 7: Git email
    env["GIT_USER_EMAIL"] = _prompt_edit(
        "GIT_USER_EMAIL",
        env.get("GIT_USER_EMAIL", ""),
        lambda: questionary.text(
            "Git email:",
            default=env.get("GIT_USER_EMAIL", ""),
            validate=lambda t: len(t.strip()) > 0 or "Must be non-empty",
        ),
    )

    # Step 8: Git token (only if token method)
    if auth_method == "token":
        env["GIT_TOKEN"] = _prompt_edit(
            "GIT_TOKEN",
            env.get("GIT_TOKEN", ""),
            lambda: questionary.password(
                "Git token (personal access token):",
                validate=lambda t: len(t.strip()) > 0 or "Must be non-empty",
            ),
            display_fn=mask_password,
        )
        # Remove SSH key if switching from ssh to token
        template_data.pop("ssh_private_key", None)
    else:
        # Remove token if switching from token to ssh
        env.pop("GIT_TOKEN", None)

    # Step 9: SSH private key (only if SSH method)
    if auth_method == "ssh":
        log("INFO", "Configuring SSH key authentication...")
        has_existing = "ssh_private_key" in template_data and template_data["ssh_private_key"]
        if has_existing:
            log("INFO", "SSH private key: (already configured)")
            if ask_or_exit(questionary.confirm("Replace SSH private key?", default=False)):
                template["ssh_private_key"] = prompt_ssh_key()
            else:
                template["ssh_private_key"] = template_data["ssh_private_key"]
        else:
            template["ssh_private_key"] = prompt_ssh_key()

    # Step 10: Extra APT packages
    env["EXTRA_APT_PACKAGES"] = _prompt_edit(
        "EXTRA_APT_PACKAGES",
        env.get("EXTRA_APT_PACKAGES", ""),
        lambda: questionary.text(
            "Extra APT packages (space-separated, leave empty for none):",
            default=env.get("EXTRA_APT_PACKAGES", ""),
        ),
    )

    # Step 11: Pager
    env["PAGER"] = _prompt_edit(
        "PAGER",
        env.get("PAGER", "cat"),
        lambda: questionary.select(
            "Select default pager:",
            choices=["cat", "less", "more", "most"],
            default=env.get("PAGER", "cat"),
        ),
    )

    # Step 12: AWS output format (only if AWS enabled)
    if aws_config == "true":
        env["AWS_DEFAULT_OUTPUT"] = _prompt_edit(
            "AWS_DEFAULT_OUTPUT",
            env.get("AWS_DEFAULT_OUTPUT", "json"),
            lambda: questionary.select(
                "Select default AWS CLI output format:",
                choices=["json", "table", "text", "yaml"],
                default=env.get("AWS_DEFAULT_OUTPUT", "json"),
            ),
        )
    else:
        env.pop("AWS_DEFAULT_OUTPUT", None)

    # Step 13: Host proxy
    host_proxy = _prompt_edit(
        "HOST_PROXY",
        env.get("HOST_PROXY", "false"),
        lambda: questionary.select(
            "Enable host proxy?",
            choices=["true", "false"],
            default=env.get("HOST_PROXY", "false"),
        ),
    )
    env["HOST_PROXY"] = host_proxy

    # Step 14: Host proxy URL (only if host proxy true)
    if host_proxy == "true":
        env["HOST_PROXY_URL"] = _prompt_edit(
            "HOST_PROXY_URL",
            env.get("HOST_PROXY_URL", ""),
            lambda: questionary.text(
                "Host proxy URL (e.g., http://host.docker.internal:3128):",
                default=env.get("HOST_PROXY_URL", ""),
                validate=lambda t: (
                    (t.startswith("http://") or t.startswith("https://")) or "Must start with http:// or https://"
                ),
            ),
        )
    else:
        env["HOST_PROXY_URL"] = ""

    # Step 15: Custom environment variables
    custom_keys = sorted(k for k in env if k not in KNOWN_KEYS)
    if custom_keys:
        log("INFO", "Custom environment variables:")
        for key in custom_keys:
            env[key] = _prompt_edit(
                key,
                env[key],
                lambda k=key: questionary.text(f"Enter new value for {k}:", default=env[k]),
            )
        # Offer to remove custom vars
        for key in list(custom_keys):
            if ask_or_exit(questionary.confirm(f"Remove custom variable '{key}'?", default=False)):
                del env[key]

    # Offer to add new custom vars
    log("INFO", "You can add additional custom environment variables.")
    new_custom = prompt_custom_env_vars(KNOWN_KEYS | set(env.keys()))
    env.update(new_custom)

    template["containerEnv"] = env

    # Step 16: AWS profile map (only if AWS enabled)
    if aws_config == "true":
        existing_profiles = template_data.get("aws_profile_map", {})
        if existing_profiles:
            log(
                "INFO",
                f"AWS profiles configured: {', '.join(sorted(existing_profiles.keys()))}",
            )
            if ask_or_exit(questionary.confirm("Reconfigure AWS profiles?", default=False)):
                template["aws_profile_map"] = prompt_aws_profile_map()
            else:
                template["aws_profile_map"] = existing_profiles
        else:
            log("INFO", "Configuring AWS profiles...")
            template["aws_profile_map"] = prompt_aws_profile_map()
    else:
        template["aws_profile_map"] = {}

    # Preserve CLI version (will be updated by caller)
    template["cli_version"] = template_data.get("cli_version", __version__)

    return template


def save_template_to_file(template_data: Dict[str, Any], name: str) -> None:
    """Save template to file with metadata.

    Adds template_name, template_path, and cli_version metadata
    before writing the template JSON file.

    Args:
        template_data: The template data dict to save.
        name: The template name.
    """
    ensure_templates_dir()

    template_path = get_template_path(name)

    # Add metadata
    template_data["template_name"] = name
    template_data["template_path"] = template_path

    # Only update version information if no git_ref is present
    # When git_ref is present, cli_version should match the git reference
    if "git_ref" not in template_data:
        template_data["cli_version"] = __version__

    write_json_file(template_path, template_data)

    log("OK", f"Template saved to {template_path}")


def load_template_from_file(name: str) -> Dict[str, Any]:
    """Load template from file."""
    template_path = get_template_path(name)

    if not os.path.exists(template_path):
        exit_with_error(f"Template {name} not found")

    template_data = load_json_config(template_path)

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

                choice = ask_or_exit(
                    questionary.select(
                        "The template format may be incompatible. What would you like to do?",
                        choices=choices,
                    )
                )

                if choice == choices[0]:  # Upgrade
                    template_data = upgrade_template(template_data)
                    log("OK", f"Template '{name}' upgraded to version {current_version}")
                elif choice == choices[1]:  # Create new
                    log("INFO", "Creating a new template instead...")
                    return create_template_interactive()
                elif choice == choices[3]:  # Exit
                    exit_cancelled()
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
            log(
                "INFO",
                "AWS is enabled but no profile map found, prompting for AWS configuration",
            )
            new_template["aws_profile_map"] = prompt_aws_profile_map()
        else:
            new_template["aws_profile_map"] = {}

    # Preserve git reference information if it exists, but mark as upgraded
    if "git_ref" in template_data:
        new_template["git_ref"] = template_data["git_ref"]
        new_template["original_git_ref"] = template_data["cli_version"]  # Preserve original git ref

    # Always set cli_version to current version (this is an upgrade)
    new_template["cli_version"] = __version__

    return new_template


def apply_template(template_data: Dict[str, Any], target_path: str) -> None:
    """Apply template to target path.

    Generates all project configuration files (environment variables JSON,
    shell.env, AWS profile map, SSH key, .gitignore entries) via write_project_files().
    Does NOT copy .devcontainer/ files — that responsibility belongs to the
    catalog pipeline's copy_entry_to_project().
    """
    # Resolve template name from data or use "unknown"
    template_name = template_data.get("template_name", "unknown")
    template_path_str = template_data.get("template_path", "")

    # Generate all project files (env vars JSON, shell.env, aws map, ssh key, gitignore)
    write_project_files(target_path, template_data, template_name, template_path_str)

    log("OK", "Template applied successfully")
