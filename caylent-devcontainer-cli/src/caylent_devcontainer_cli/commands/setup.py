"""Setup command for the Caylent Devcontainer CLI."""

import os
import shutil
import subprocess
import tempfile

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.utils.ui import log

# Constants
REPO_URL = "https://github.com/caylent-solutions/devcontainer.git"
EXAMPLE_ENV_VALUES = {
    "AWS_CONFIG_ENABLED": "true",
    "DEFAULT_GIT_BRANCH": "main",
    "DEFAULT_PYTHON_VERSION": "3.12.9",
    "DEVELOPER_NAME": "Your Name",
    "EXTRA_APT_PACKAGES": "",
    "GIT_PROVIDER_URL": "github.com",
    "GIT_TOKEN": "your-git-token",
    "GIT_USER": "your-username",
    "GIT_USER_EMAIL": "your-email@example.com",
}


def confirm_overwrite(message):
    """Ask for user confirmation without logging error on decline."""
    from caylent_devcontainer_cli.utils.ui import COLORS

    print(f"{COLORS['YELLOW']}⚠️  {message}{COLORS['RESET']}")
    response = input(f"{COLORS['BOLD']}Do you want to overwrite? [y/N]{COLORS['RESET']} ")
    return response.lower().startswith("y")


def register_command(subparsers):
    """Register the setup command with the CLI."""
    parser = subparsers.add_parser("setup-devcontainer", help="Set up a devcontainer in a project directory")
    parser.add_argument("path", help="Path to the root of the repository to set up")
    parser.add_argument(
        "--manual", action="store_true", help="Skip interactive prompts and copy files for manual configuration"
    )
    parser.add_argument(
        "--update", action="store_true", help="Update existing devcontainer files to the current CLI version"
    )
    parser.add_argument("--ref", help="Git reference (branch, tag, or commit) to clone instead of CLI version")
    parser.set_defaults(func=handle_setup)


def handle_setup(args):
    """Handle the setup-devcontainer command."""
    target_path = args.path
    manual_mode = args.manual
    update_mode = args.update
    git_ref = args.ref if args.ref else __version__

    # Validate target path
    if not os.path.isdir(target_path):
        log("ERR", f"Target path does not exist or is not a directory: {target_path}")
        import sys

        sys.exit(1)

    # Check if we're updating existing devcontainer files
    target_devcontainer = os.path.join(target_path, ".devcontainer")
    should_clone = True  # Flag to determine if we need to clone repo

    if update_mode:
        if not os.path.exists(target_devcontainer):
            log("ERR", f"No .devcontainer directory found at {target_path} to update")
            import sys

            sys.exit(1)

        log("INFO", f"Updating devcontainer files to version {__version__}...")
    else:
        # Check if devcontainer already exists
        if os.path.exists(target_devcontainer):
            version_file = os.path.join(target_devcontainer, "VERSION")
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    current_version = f.read().strip()
                log("INFO", f"Found existing devcontainer (version {current_version})")
                if not confirm_overwrite(f"Devcontainer already exists. Overwrite with version {__version__}?"):
                    log("INFO", "Overwrite declined by user.")
                    should_clone = False  # Skip cloning, work with existing setup
            else:
                if not confirm_overwrite(
                    f"Devcontainer already exists but has no version information. Overwrite with version {__version__}?"
                ):
                    log("INFO", "Overwrite declined by user.")
                    should_clone = False  # Skip cloning, work with existing setup

    if should_clone:
        # Clone repository to temporary location
        with tempfile.TemporaryDirectory() as temp_dir:
            log("INFO", f"Cloning devcontainer repository (ref: {git_ref})...")
            clone_repo(temp_dir, git_ref)

            if manual_mode:
                # Copy .devcontainer folder to target path
                copy_devcontainer_files(temp_dir, target_path, keep_examples=True)
                # Create VERSION file
                create_version_file(target_path)
                # Check and create .tool-versions file with default Python version
                check_and_create_tool_versions(target_path, EXAMPLE_ENV_VALUES["DEFAULT_PYTHON_VERSION"])
                # Ensure .gitignore entries
                ensure_gitignore_entries(target_path)
                show_manual_instructions(target_path)
            else:
                # Interactive setup
                interactive_setup(temp_dir, target_path)
                # Create VERSION file
                create_version_file(target_path)
                # Ensure .gitignore entries
                ensure_gitignore_entries(target_path)
    else:
        # User declined overwrite, continue with existing .devcontainer
        if manual_mode:
            # Check and create .tool-versions file with default Python version
            check_and_create_tool_versions(target_path, EXAMPLE_ENV_VALUES["DEFAULT_PYTHON_VERSION"])
            # Ensure .gitignore entries
            ensure_gitignore_entries(target_path)
            show_manual_instructions(target_path)
        else:
            # Interactive setup without cloning - just create environment files
            interactive_setup_without_clone(target_path)
            # Ensure .gitignore entries
            ensure_gitignore_entries(target_path)


def create_version_file(target_path: str) -> None:
    """Create a VERSION file in the .devcontainer directory."""
    version_file = os.path.join(target_path, ".devcontainer", "VERSION")
    with open(version_file, "w") as f:
        f.write(__version__ + "\n")  # Add newline
    log("INFO", f"Created VERSION file with version {__version__}")


def check_and_create_tool_versions(target_path: str, python_version: str) -> None:
    """Check for .tool-versions file and create if missing."""
    tool_versions_path = os.path.join(target_path, ".tool-versions")

    if os.path.exists(tool_versions_path):
        log("OK", "Found .tool-versions file")
        return

    log(
        "INFO",
        ".tool-versions file not found but is required as the Caylent Devcontainer "
        "requires runtimes and tools to be managed by asdf",
    )

    file_content = f"python {python_version}\n"
    print(f"\nWill create file: {tool_versions_path}")
    print(f"With content:\n{file_content}")

    try:
        input("Press Enter to create the file...")
    except (EOFError, KeyboardInterrupt):
        # Handle non-interactive environments (like tests) or user cancellation
        pass

    with open(tool_versions_path, "w") as f:
        f.write(file_content)

    log("OK", f"Created .tool-versions file with Python {python_version}")


def ensure_gitignore_entries(target_path: str) -> None:
    """Ensure required entries are in .gitignore."""
    gitignore_path = os.path.join(target_path, ".gitignore")
    required_files = ["shell.env", "devcontainer-environment-variables.json", ".devcontainer/aws-profile-map.json"]

    log("INFO", "Checking .gitignore for required environment file entries to prevent the commit of your secrets.")
    log("INFO", "Files to check:")
    for file_entry in required_files:
        print(f"  - {file_entry}")

    # Read existing .gitignore if it exists
    existing_lines = []
    gitignore_exists = os.path.exists(gitignore_path)

    if gitignore_exists:
        with open(gitignore_path, "r") as f:
            existing_lines = [line.strip() for line in f.readlines()]
    else:
        log("INFO", ".gitignore file does not exist, will create it")

    # Check which files are missing
    missing_files = []
    for file_entry in required_files:
        if file_entry not in existing_lines:
            missing_files.append(file_entry)

    if not missing_files:
        log("OK", "All required entries already present in .gitignore")
        return

    # Inform user about missing entries
    log("INFO", f"Missing {len(missing_files)} entries in .gitignore:")
    for file_entry in missing_files:
        print(f"  - {file_entry}")

    # Add missing entries
    with open(gitignore_path, "a") as f:
        if existing_lines and existing_lines[-1] != "":  # Add newline if file doesn't end with one
            f.write("\n")
        # Add comment header if we're adding any files
        f.write("# Environment files\n")
        for file_entry in missing_files:
            f.write(file_entry + "\n")

    action = "Created" if not gitignore_exists else "Updated"
    log("OK", f"{action} .gitignore with {len(missing_files)} new entries:")
    for file_entry in missing_files:
        print(f"  - {file_entry}")


def clone_repo(temp_dir: str, git_ref: str) -> None:
    """Clone the repository at the specified git reference (branch, tag, or commit)."""
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", git_ref, REPO_URL, temp_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        log("ERR", f"Failed to clone devcontainer repository at ref '{git_ref}'")
        log("ERR", f"Reference '{git_ref}' does not exist in the repository")
        log("ERR", f"Please check available branches/tags at: {REPO_URL}")
        log("ERR", f"Git error: {e}")
        import sys

        sys.exit(1)


def copy_devcontainer_files(source_dir: str, target_path: str, keep_examples: bool = False) -> None:
    """Copy .devcontainer folder to target path."""
    source_devcontainer = os.path.join(source_dir, ".devcontainer")
    target_devcontainer = os.path.join(target_path, ".devcontainer")

    if os.path.exists(target_devcontainer):
        from caylent_devcontainer_cli.utils.ui import confirm_action

        if not confirm_action(f".devcontainer folder already exists at {target_devcontainer}. Overwrite?"):
            log("INFO", "Setup cancelled by user.")
            import sys

            sys.exit(0)
            return  # This return is needed for tests but will never be reached in real code

        try:
            shutil.rmtree(target_devcontainer)
        except FileNotFoundError:
            # This can happen in tests, just continue
            pass

    log("INFO", f"Copying .devcontainer folder to {target_path}...")
    shutil.copytree(source_devcontainer, target_devcontainer)

    # Remove example files if not in manual mode
    if not keep_examples:
        example_files = [
            os.path.join(target_devcontainer, "example-container-env-values.json"),
            os.path.join(target_devcontainer, "example-aws-profile-map.json"),
        ]

        for file_path in example_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    # This can happen in tests, just continue
                    pass

    log("OK", "Devcontainer files copied successfully.")


def show_manual_instructions(target_path: str) -> None:
    """Show instructions for manual setup."""
    log("OK", "Devcontainer files have been copied to your project.")
    print("\n📋 Next steps:")
    print("1. Create a devcontainer-environment-variables.json file:")
    print(
        f"   cp {os.path.join(target_path, '.devcontainer', 'example-container-env-values.json')} "
        f"{os.path.join(target_path, 'devcontainer-environment-variables.json')}"
    )
    print("2. Edit the file with your settings")
    print("3. If using AWS, create an aws-profile-map.json file:")
    print(
        f"   cp {os.path.join(target_path, '.devcontainer', 'example-aws-profile-map.json')} "
        f"{os.path.join(target_path, '.devcontainer', 'aws-profile-map.json')}"
    )
    print("4. Edit the AWS profile map with your settings")
    print("\n📚 For more information, see: https://github.com/caylent-solutions/devcontainer#-quick-start")


def interactive_setup(source_dir: str, target_path: str) -> None:
    """Run interactive setup process."""
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

    try:
        # Ask if they want to use a saved template
        if prompt_use_template():
            template_name = select_template()
            if template_name:
                template_data = load_template_from_file(template_name)
                apply_template(template_data, target_path, source_dir)
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
        apply_template(template_data, target_path, source_dir)
        log("OK", "Setup completed successfully.")
    except KeyboardInterrupt:
        log("INFO", "Setup cancelled by user.")
        import sys

        sys.exit(0)


def interactive_setup_without_clone(target_path: str) -> None:
    """Run interactive setup without cloning - only create environment files."""
    from caylent_devcontainer_cli.commands.setup_interactive import (
        apply_template_without_clone,
        create_template_interactive,
        load_template_from_file,
        prompt_save_template,
        prompt_template_name,
        prompt_use_template,
        save_template_to_file,
        select_template,
    )

    try:
        # Ask if they want to use a saved template
        if prompt_use_template():
            template_name = select_template()
            if template_name:
                template_data = load_template_from_file(template_name)
                apply_template_without_clone(template_data, target_path)
                log("OK", f"Template '{template_name}' applied successfully.")
                return

        # Create new template
        log("INFO", "Creating a new configuration...")
        template_data = create_template_interactive()

        # Ask if they want to save the template
        if prompt_save_template():
            template_name = prompt_template_name()
            save_template_to_file(template_data, template_name)

        # Apply the template without overwriting .devcontainer
        apply_template_without_clone(template_data, target_path)
        log("OK", "Setup completed successfully.")
    except KeyboardInterrupt:
        log("INFO", "Setup cancelled by user.")
        import sys

        sys.exit(0)
