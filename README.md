# Caylent Devcontainer Base

## 📑 Table of Contents

- [🚀 Overview](#-overview)
- [🧰 What's Included](#-whats-included)
- [💡 Built-In Tooling](#-built-in-tooling)
- [🖥 Prerequisites](#-prerequisites)
- [🪄 Quick Start](#-quick-start)
- [🧩 Post-Launch Setup](#-post-launch-setup)
- [🔧 Project-Specific Setup](#-project-specific-setup)
- [🐍 Python Install Logic](#-python-install-logic)
- [🔄 Rebuilding the Devcontainer](#-rebuilding-the-devcontainer)
- [🐳 Docker-in-Docker Support](#-docker-in-docker-support)
- [🔌 Disabling VS Code Auto Port Forwarding](#-disabling-vs-code-auto-port-forwarding)
- [📡 Debug Ports](#-debug-ports)
- [🧩 JetBrains Compatibility](#-jetbrains-compatibility)
- [📁 File Reference](#-file-reference)
- [🧪 Validate Your Config](#-validate-your-config)
- [🧼 Git Hygiene](#-git-hygiene)
- [🛠️ CLI Reference](#️-cli-reference)
- [DevContainer Catalogs](#devcontainer-catalogs)
- [ECR Public Image Mirror](#ecr-public-image-mirror)
- [🤝 Contributing](#-contributing)

## 🚀 Overview

This repository provides the **base development container** configuration used across Caylent engineering projects. It is designed to be:

- ✅ **Cross-platform**: macOS and Windows (WSL2) compatible using VS Code or Cursor
- 🧱 **Reusable**: drop into any repo to enable consistent local dev experience
- 🔐 **Secure and configurable**: injects secrets via environment, not committed
- 🧩 **Smart defaults**: tools, AWS profiles, aliases, Python setup, Git config, and more
- 🧪 **Consistent environments**: ensures identical local dev setups across teams using `asdf` to pin and manage exact binary versions
- 🚀 **CI/CD ready**: supports automated environments with `CICD=true` flag
- 📝 **Windows line ending support**: automatically converts CRLF to LF on WSL for compatibility

📦 Repo URL: [`https://github.com/caylent-solutions/devcontainer`](https://github.com/caylent-solutions/devcontainer)

---

## 🧰 What's Included

- `devcontainer.json` — VS Code container definition
- `.devcontainer.postcreate.sh` — container setup script
- `project-setup.sh` — project-specific setup script for custom initialization
- `fix-line-endings.py` — automatic Windows line ending conversion for WSL compatibility
- `cdevcontainer` — Caylent Devcontainer CLI tool for environment management
- Git, AWS CLI, Docker, Python, `asdf`, aliases, shell profile injection
- Extension support for Amazon Q and GitHub Copilot

---

## 💡 Built-In Tooling

The devcontainer installs:

- ✅ Amazon Q extension (VS Code/Cursor compatible)
- ✅ GitHub Copilot + Copilot Chat
- ✅ GitLens, YAML, Python, Docker, Makefile Tools
- ✅ Jinja, spell checking

These extensions are auto-installed on container start and work with both VS Code and Cursor.

---

## 🖥 Prerequisites

### For macOS
- [VS Code](https://code.visualstudio.com/Download) or [Cursor](https://cursor.sh/)
- [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- [Homebrew](https://brew.sh/) — optional
- Python 3.12.9 - [Installation Guide](supplemental-docs/PYTHON_INSTALL.md#for-macos-using-asdf)

### For Windows
- [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install)
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- [VS Code](https://code.visualstudio.com/Download) or [Cursor](https://cursor.sh/)
- Python 3.12.9 - [Installation Guide](supplemental-docs/PYTHON_INSTALL.md#for-windows-using-windows-store-or-official-installer)

> ⚠️ **Important for Windows users**: When cloning Git repositories that will use this devcontainer, ensure Git is configured to use Unix line endings (LF) instead of Windows line endings (CRLF). Configure this globally with:
> ```bash
> git config --global core.autocrlf false
> git config --global core.eol lf
> ```
>
> This prevents issues with shell scripts and other text files when running in WSL environments. The devcontainer includes automatic line ending conversion for WSL compatibility.

### VS Code / Cursor Host Settings

Before opening any devcontainer, configure these **host-level** settings. Without this, VS Code will forward ports used by internal services and auto-install unwanted extensions.

1. Open Settings (Cmd/Ctrl + ,)
2. Search for "Remote" or navigate to **Features > Remote**
3. Configure these settings:
   - **Auto Forward Ports** — uncheck (disable)
   - **Auto Forward Ports Source** — set to `hybrid`
   - **Forward Ports On Open** — uncheck (disable)
   - **Restore Forwarded Ports** — uncheck (disable)
   - **Default Extensions If Installed Locally** — remove `GitHub.copilot` and `GitHub.copilot-chat` from the list (keep `GitHub.vscode-pull-request-github` if desired)
4. **Disable built-in Copilot extensions** (VS Code 1.96+ bundles Copilot as a built-in extension):
   - Open Extensions sidebar → type `@builtin copilot` in the search bar
   - Disable both **GitHub Copilot** and **GitHub Copilot Chat**
   - This removes the "Finish setup" prompt and Copilot chat panel from VS Code
5. **Disable Copilot extension unification:**
   - Search for `chat.extensionUnification.enabled` in Settings
   - Uncheck **Chat › Extension Unification: Enabled**
   - This prevents VS Code from merging all Copilot functionality into the chat extension

These settings persist across sessions and only need to be configured once. See [Disabling VS Code Auto Port Forwarding](#-disabling-vs-code-auto-port-forwarding) for details.

### IDE Command Line Setup

The `cdevcontainer` CLI requires IDE command-line tools to launch projects. Enable them as follows:

#### VS Code CLI Setup
1. Open **VS Code**
2. Press `⌘ + Shift + P` (macOS) or `Ctrl + Shift + P` (Windows/Linux)
3. Type: **Shell Command: Install 'code' command in PATH**
4. Run the command and restart your terminal
5. Test: `code .`

#### Cursor CLI Setup
1. Open **Cursor**
2. Press `⌘ + Shift + P` (macOS) or `Ctrl + Shift + P` (Windows/Linux)
3. Type: **Shell Command: Install 'cursor' command in PATH**
4. Run the command and restart your terminal
5. Test: `cursor .`

---

## 🪄 Quick Start

### 1. Install the CLI Tool

First, install the Caylent Devcontainer CLI using pipx (recommended to avoid package conflicts):

```bash
pipx install caylent-devcontainer-cli
```

You can also install a specific version:

```bash
pipx install caylent-devcontainer-cli==1.1.0
```

To install directly from GitHub (alternative method):

```bash
pipx install git+https://github.com/caylent-solutions/devcontainer.git@1.1.0#subdirectory=caylent-devcontainer-cli
```

If you don't have pipx installed, install it first:
```bash
python -m pip install pipx
```

After installation, you can run the CLI from anywhere:

```bash
cdevcontainer --help
```

### 2. Set Up Your Project

You can set up a devcontainer in your project using the CLI:

```bash
cdevcontainer setup-devcontainer /path/to/your/project
```

This will:
1. Clone the devcontainer catalog and copy configuration files to your project
2. Guide you through an interactive setup process
3. Let you select or create a template for your environment
4. Configure AWS profiles if needed

If your organization provides a specialized catalog, set the environment variable:

```bash
export DEVCONTAINER_CATALOG_URL="https://github.com/your-org/devcontainer-catalog.git"
cdevcontainer setup-devcontainer /path/to/your/project
```

You can also select a specific entry directly (useful for CI/automation):

```bash
export DEVCONTAINER_CATALOG_URL="https://github.com/your-org/devcontainer-catalog.git"
cdevcontainer setup-devcontainer --catalog-entry java-backend /path/to/your/project
```



> 💡 **Pro tip**: Consider committing the `.devcontainer` directory to your repository (excluding sensitive files) to speed up environment setup for your team. See the [Git Hygiene](#-git-hygiene) section for details.

---

### 3. Customize Your Developer Environment

When running `cdevcontainer setup-devcontainer`, you'll be guided through configuring:

- AWS configuration (enabled by default)
- Git branch and credentials
- Python version
- Developer information
- Extra Ubuntu packages
- Pager selection (cat, less, more, most)
- AWS CLI output format (json, table, text, yaml) - only if AWS is enabled

The interactive setup will create a `devcontainer-environment-variables.json` file with your settings.

The `devcontainer-environment-variables.json` file supports these values:
- `AWS_CONFIG_ENABLED` (default: `true`) - Set to `false` to disable AWS configuration
- `DEFAULT_GIT_BRANCH` (e.g. `main`)
- `DEFAULT_PYTHON_VERSION` (e.g. `3.12.9`)
- Git credentials: `GIT_USER`, `GIT_USER_EMAIL`, `GIT_TOKEN`
- AWS SSO and account information (required if `AWS_CONFIG_ENABLED=true`)
- Extra Ubuntu LTS packages: `EXTRA_APT_PACKAGES`
- `PAGER` (default: `cat`) - Choose from: cat, less, more, most
- `AWS_DEFAULT_OUTPUT` (default: `json`) - Choose from: json, table, text, yaml

#### Client/Project Templates

The `setup-devcontainer` command will ask if you want to:
- Use an existing template
- Create a new reusable template
- Create a one-time configuration

Templates are saved in `~/.devcontainer-templates/` and can be reused across projects.

You can also manage templates directly:

```bash
# Create a new template interactively
cdevcontainer template create client1



# Save current environment as a template
cdevcontainer template save client1

# List available templates
cdevcontainer template list

# Load a template into a new project
cd /path/to/new-project
cdevcontainer template load client1

# Delete one or more templates
cdevcontainer template delete template1 template2

# Upgrade a template to the current CLI version
cdevcontainer template upgrade my-template



# Force upgrade with interactive prompts for missing variables
cdevcontainer template upgrade --force my-template
cdevcontainer template upgrade -f my-template
```

When loading a template:
1. The CLI copies the template from `~/.devcontainer-templates/client1.json`
2. It creates a new `devcontainer-environment-variables.json` file in your project
3. This file contains all the environment settings from the template (Git credentials, AWS settings, etc.)
4. You can then run `cdevcontainer code` to use these settings with your project

This allows you to maintain consistent configurations across multiple projects for the same client.

#### Template Version Compatibility

Templates are saved with version information that tracks which CLI version created them. When loading a template created with an older version of the CLI, the tool automatically detects version mismatches and provides options:

- **Upgrade the template**: Updates the template to the current CLI format while preserving settings
- **Create a new template**: Starts fresh with the current CLI version
- **Use anyway**: Attempts to use the template as-is (may cause issues)
- **Exit**: Cancels the operation without making changes

This version checking ensures templates remain compatible as the CLI evolves.

#### Force Upgrade for Missing Variables

The CLI can detect when your templates are missing new environment variables that have been added to newer versions. Use the `--force` flag to interactively add missing variables:

```bash
# Force upgrade with interactive prompts for missing variables
cdevcontainer template upgrade --force my-template
```

During a force upgrade:
- The CLI detects missing single-line environment variables
- For each missing variable, you can choose the default value or enter a custom value
- Only simple string variables are prompted (complex objects are skipped)
- The template is updated with your choices

#### Missing Variable Warnings

When running `cdevcontainer code <path>`, the CLI checks for missing environment variables in your configuration. If missing variables are detected:

- A colorful warning displays the missing variables
- Instructions are provided to:
  1. Run `cdevcontainer template upgrade --force <template-name>` to upgrade the template
  2. Run `cdevcontainer template load --project-root <project-root> <template-name>` to load the upgraded template into the project
- You can choose to exit and upgrade, or continue with potential issues

This ensures your development environment stays up-to-date with the latest requirements.

---

### 4. Configure AWS Profile Map (Optional)

By default, AWS configuration is enabled. If you don't need AWS access, you can disable it during the interactive setup or by setting `AWS_CONFIG_ENABLED=false` in your `devcontainer-environment-variables.json`.

When using the interactive setup with AWS enabled, you'll be presented with two options for providing your AWS profile configuration:

#### Option 1: JSON Format (Complete Configuration)
Paste your complete AWS profile configuration in JSON format:

```json
{
  "default": {
    "region": "us-west-2",
    "sso_start_url": "https://example.awsapps.com/start",
    "sso_region": "us-west-2",
    "account_name": "example-dev-account",
    "account_id": "123456789012",
    "role_name": "DeveloperAccess"
  }
}
```

#### Option 2: Standard Format (Profile by Profile)
Enter AWS profiles one at a time in standard AWS config format:

```ini
[default]
sso_start_url       = https://example.awsapps.com/start
sso_region          = us-west-2
sso_account_name    = example-dev-account
sso_account_id      = 123456789012
sso_role_name       = DeveloperAccess
region              = us-west-2
```

The setup will:
- Validate each profile for required fields
- Prompt you to re-enter if validation fails
- Ask if you want to add additional profiles
- Automatically convert to the expected JSON format

#### Manual Configuration
Create `.devcontainer/aws-profile-map.json` and define your AWS SSO accounts using the JSON format shown above.

> ⚠️ This file is required only when AWS configuration is enabled (`AWS_CONFIG_ENABLED=true`).
>
> AWS configuration is completely optional and not required for using Amazon Q.

---

### 5. Setting Up Your Environment

```bash
# Launch VS Code for the current project (default IDE)
cdevcontainer code

# Launch Cursor for the current project
cdevcontainer code --ide cursor

# Launch VS Code for a specific project
cdevcontainer code /path/to/your-project

# Launch Cursor for a specific project
cdevcontainer code /path/to/your-project --ide cursor
```

This will:
- Generate `shell.env` from your `devcontainer-environment-variables.json`
- Load the environment variables
- Launch VS Code
- Display a confirmation message

> ⚠️ **Note**: After VS Code launches, you'll need to accept the prompt to reopen in container.

> 💡 **Pro tip for multiple projects**: Use a dedicated terminal for each project:
> ```bash
> # In terminal 1 (for project A)
> cdevcontainer code /path/to/project-a
>
> # In terminal 2 (for project B)
> cdevcontainer code /path/to/project-b
> ```
>
> This approach prevents environment variable conflicts when working with multiple projects simultaneously.

> 🚀 **Advanced tip**: You can launch any supported IDE for another project directly from within a running devcontainer:
> ```bash
> # From within any devcontainer terminal
> cdevcontainer code /path/to/another-project
> cdevcontainer code /path/to/another-project --ide cursor
> ```
>
> This will open a new IDE window with the other project's devcontainer, allowing you to work on multiple projects simultaneously.

---

## 🚀 CI/CD Support

The devcontainer supports running in CI/CD environments where developer-specific configurations (Git credentials, AWS profiles, developer names) are not needed or are handled separately.

To enable CI/CD mode, set the `CICD` environment variable to `true`:

```bash
export CICD=true
```

When `CICD=true`, the devcontainer will skip:
- AWS configuration validation and setup
- Git credential configuration
- Developer name environment variable setup
- AWS profile creation

This allows the devcontainer to run in automated environments where:
- Git authentication is handled by the CI/CD system
- AWS credentials are provided through IAM roles or other mechanisms
- Developer-specific personalization is not required

### Required Environment Variables for CI/CD

When running in CI/CD mode, you still need to set these core environment variables:

```yaml
# GitHub Actions example
env:
  CICD: "true"                           # Enable CI/CD mode
  DEFAULT_GIT_BRANCH: "main"              # Required: Git branch for aliases
  DEFAULT_PYTHON_VERSION: "3.12.9"        # Required: Python version to install
  EXTRA_APT_PACKAGES: ""                  # Optional: Additional Ubuntu packages
  PAGER: "cat"                            # Optional: Pager for command output (defaults to cat)
  AWS_DEFAULT_OUTPUT: "json"              # Optional: AWS CLI output format (defaults to json)
```

### Environment Variables Skipped in CI/CD Mode

These variables are not needed when `CICD=true` as they're handled by the CI/CD system:

```yaml
# These are SKIPPED in CI/CD mode - do not set them
# AWS_CONFIG_ENABLED: "true"             # Skipped: AWS handled by CI/CD
# DEVELOPER_NAME: "johndoe"              # Skipped: Not needed in CI/CD
# GIT_PROVIDER_URL: "github.com"         # Skipped: Git handled by CI/CD
# GIT_TOKEN: "<token>"                   # Skipped: Git handled by CI/CD
# GIT_USER: "john.doe"                   # Skipped: Git handled by CI/CD
# GIT_USER_EMAIL: "john.doe@example.com" # Skipped: Git handled by CI/CD
```

---

## 🧩 Post-Launch Setup

### 🧠 GitHub Copilot

- Auto-installed
- Login prompt appears if not authenticated
- To verify: open any `.py` file and type a comment — suggestions will appear

### 🤖 Amazon Q

- Open the Amazon Q sidebar (left bar in VS Code/Cursor) or use Command+Shift+P and type "AmazonQ: Open Chat"
- Click **Sign in** and follow the browser flow
- Enter your SSO start URL, select your region and Pro account
- Authentication will complete via browser
- No AWS profile configuration is required if you only want to use Amazon Q

---

### 🔐 Connect to AWS via SSO

From the container:
```bash
aws sso login --profile your-profile-name
```

- Omitting `--profile` uses the `"default"` profile from your `~/.aws/config`.

---

### ✅ Confirm Git Auth

```bash
git config --get user.email
git config --get user.name
git ls-remote https://github.com/your-org/your-repo.git
```

Or open the Source Control tab in your IDE to confirm the repo is accessible.

---

## 🔧 Project-Specific Setup

The devcontainer includes a **project-specific setup script** that runs automatically after the main devcontainer setup is complete. This allows you to add project-specific initialization commands without modifying the core devcontainer files.

### 📝 Setup Script Location

The project setup script is located at:
```
.devcontainer/project-setup.sh
```

### 🚀 What to Add

Add any commands needed to make your project immediately ready for development:

```bash
# Example project-specific setup commands
if [ -f "Makefile" ]; then
  log_info "Running make configure..."
  make configure
fi

if [ -f "requirements.txt" ]; then
  log_info "Installing Python dependencies..."
  pip install -r requirements.txt
fi

if [ -f "package.json" ]; then
  log_info "Installing Node.js dependencies..."
  npm install
fi

if [ -f "docker-compose.yml" ]; then
  log_info "Starting Docker services..."
  docker-compose up -d
fi
```

### 🌐 Environment Variables

The project setup script has access to:
- All environment variables from `shell.env`
- All environment variables from `devcontainer.json`
- Logging functions: `log_info`, `log_success`, `log_warn`, `log_error`

### 🎨 IDE Customizations

Projects can also customize IDE settings and extensions by modifying the `customizations` section in `.devcontainer/devcontainer.json`:

```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-toolsai.jupyter",
        "your-project-specific-extension"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "editor.tabSize": 2,
        "files.exclude": {
          "**/.git": true,
          "**/node_modules": true
        }
      }
    }
  }
}
```

This works for all supported IDEs including VS Code, Cursor, and others that support devcontainer customizations.

### ⚠️ Important Notes

- **DO NOT modify** `.devcontainer.postcreate.sh` for project-specific setup
- **DO modify** `.devcontainer/project-setup.sh` for your project needs
- **DO customize** `.devcontainer/devcontainer.json` for IDE settings and extensions
- This approach ensures you can receive devcontainer updates without conflicts
- The script runs with the same permissions and environment as the main setup

### 📝 Example Use Cases

- **Python projects**: Install dependencies, set up virtual environments
- **Node.js projects**: Run `npm install`, build assets
- **Docker projects**: Start required services with `docker-compose`
- **Database projects**: Initialize databases, run migrations
- **Configuration**: Generate config files, set up symlinks
- **Build tools**: Run `make configure`, `cmake`, or other build setup

---

## 🐍 Python Install Logic

- `.tool-versions` present with Python? → installs that pinned Python version
- Not present or no Python entry? → installs fallback version from:
```json
"DEFAULT_PYTHON_VERSION": "3.12.9"
```

> ✅ **Automatic .tool-versions creation**: The setup command will automatically check for a `.tool-versions` file in your project root. If not found, it will create one with your chosen Python version to ensure consistent runtime management via asdf.

> ✅ Best practice: commit `.tool-versions` to your repo:
```bash
echo "python 3.12.9" > .tool-versions
git add .tool-versions
git commit -m "Add Python version pin for devcontainer"
```

Then rebuild the container.

---

## 🔄 Rebuilding the Devcontainer

When you make changes to the devcontainer configuration (such as modifying `devcontainer.json`, `devcontainer-environment-variables.json`, or `.tool-versions`), you'll need to rebuild the container for changes to take effect:

1. A popup will typically appear in your IDE prompting you to rebuild when configuration files change
2. Alternatively, you can manually rebuild by:
   - Opening the Command Palette (Command+Shift+P or Ctrl+Shift+P)
   - Typing "Dev Containers: Rebuild Container" and selecting it

> ⚠️ **Important**: Always rebuild the container after changing any devcontainer configuration files to ensure your changes are applied.

---

## 🐳 Docker-in-Docker Support

The devcontainer supports **nested Docker** with `docker-in-docker`.

To enable Docker Swarm inside the container:
```bash
docker swarm init
```

> You can now run full containerized workflows inside the devcontainer itself.

---

## 🔌 Disabling VS Code Auto Port Forwarding

VS Code automatically detects and forwards ports from processes running inside the devcontainer to the host. This includes any listening socket found by VS Code's port scanning. While convenient for web development, this causes port conflicts in environments that use host-side proxies (e.g., tinyproxy for corporate proxy support).

The `devcontainer.json` includes settings to disable this behavior inside the container (`remote.autoForwardPorts: false`, `remote.autoForwardPortsSource: "process"`, and `remote.otherPortsAttributes.onAutoForward: "ignore"`). However, VS Code also has **host-level settings** that must be configured before opening any Remote or Dev Container connection.

**Required VS Code Host Settings** (set these on your local machine before connecting):

1. Open VS Code Settings (Cmd/Ctrl + ,)
2. Search for "Remote" or navigate to **Features > Remote**
3. Disable/configure these settings:
   - **Auto Forward Ports** — uncheck (disable)
   - **Auto Forward Ports Source** — set to `hybrid`
   - **Forward Ports On Open** — uncheck (disable)
   - **Restore Forwarded Ports** — uncheck (disable)
   - **Default Extensions If Installed Locally** — remove `GitHub.copilot` and `GitHub.copilot-chat` from the list. These extensions are auto-installed in remote environments when present locally, which causes unwanted Copilot prompts inside devcontainers.

These settings persist across VS Code sessions and only need to be configured once.

---

## 📡 Debug Ports

| Port      | Purpose                  |
|-----------|--------------------------|
| 5678      | Python debug (debugpy)   |
| 9229      | Node.js inspector        |
| 5005      | Java debug (JDWP)        |
| 4020      | Custom web app / tools   |
| 4711      | Internal dev tools       |
| 8080      | Web servers (HTTP)       |
| 5050      | WebSocket / APIs         |

---

## 🧩 JetBrains Compatibility

JetBrains IDEs (like PyCharm) support Devcontainers via [JetBrains Gateway](https://www.jetbrains.com/remote-development/gateway/), but:

- Post-create hooks, VS Code extensions, and shell customization are **not** guaranteed
- VS Code or Cursor are **strongly recommended** for full compatibility

---

## 📁 File Reference

| File | Purpose |
|------|---------|
| `.devcontainer/devcontainer.json` | VS Code container setup |
| `.devcontainer/.devcontainer.postcreate.sh` | Container provisioning logic |
| `.devcontainer/project-setup.sh` | Project-specific setup commands |
| `.devcontainer/fix-line-endings.py` | Windows line ending conversion for WSL compatibility |
| `.devcontainer/aws-profile-map.json` | Your active AWS profiles |

---

## 🧪 Validate Your Config

### Catalog Validation

The CLI includes a comprehensive catalog validation command that checks structural integrity, content correctness, and consistency across the entire catalog:

```bash
# Validate the default catalog (remote)
cdevcontainer catalog validate

# Validate a local catalog directory
cdevcontainer catalog validate --local /path/to/catalog

# Validate using the Makefile target (installs CLI from this repo first)
make validate-catalog
```

The `catalog validate` command checks:

| Area | Check |
|------|-------|
| Common assets | Required files present (`postcreate`, `functions`, `wrapper`, `project-setup`) |
| Common assets | Subdirectories exist (`nix-family-os/`, `wsl-family-os/`) with required files |
| Common assets | Shell scripts have executable permission |
| Common assets | All `.json` files in `root-project-assets/` are valid JSON |
| Per-entry | Required files present (`catalog-entry.json`, `devcontainer.json`, `VERSION`) |
| Per-entry | `VERSION` contains valid semver (X.Y.Z) |
| Per-entry | `devcontainer.json` has `name` field and at least one container source (`image`/`build`/`dockerFile`/`dockerComposeFile`) |
| Per-entry | `postCreateCommand` references postcreate scripts |
| Per-entry | Directory name matches `catalog-entry.json` `name` field |
| Per-entry | No file conflicts with common assets (including subdirectories) |
| Per-entry | `catalog-entry.json` has valid name pattern, description, tags, and no unknown fields |
| Cross-entry | No duplicate entry names |

### JSON Validation

To validate your `devcontainer-environment-variables.json` file is valid JSON:

```bash
python3 -c "import json; json.load(open('devcontainer-environment-variables.json'))" && echo "Valid JSON"
```

If the JSON is malformed, Python will report a parse error with the line and column number.

---

## 🧼 Git Hygiene

- ❌ Never commit `shell.env` or `devcontainer-environment-variables.json`
- ✅ Use `.tool-versions` to ensure reproducibility
- ✅ Use `aws-profile-map.json` to declare AWS SSO profiles
- `.gitignore` excludes common temp files, IDE config, and secrets

> 💡 **Pro tip**: You can commit the `.devcontainer` directory to your repository for faster team onboarding. Add these lines to your `.gitignore`:
> ```
> # Devcontainer - commit structure but not secrets
> devcontainer-environment-variables.json
> .devcontainer/aws-profile-map.json
> shell.env
> ```
>
> This approach lets you version control the devcontainer configuration while excluding sensitive information.

---

## 🛠️ CLI Reference

The Caylent Devcontainer CLI provides several commands to manage your devcontainer environment:

```bash
# Show help
cdevcontainer --help

# Set up a devcontainer in a project directory
cdevcontainer setup-devcontainer /path/to/your/project

# Set up using a specific entry from a specialized catalog
export DEVCONTAINER_CATALOG_URL="https://github.com/your-org/catalog.git"
cdevcontainer setup-devcontainer --catalog-entry java-backend /path/to/your/project

# Launch IDE with the devcontainer environment (default: VS Code)
cdevcontainer code [/path/to/your/project]

# Launch specific IDE
cdevcontainer code --ide cursor [/path/to/your/project]
cdevcontainer code --ide vscode [/path/to/your/project]

# Launch IDE for another project (works from within any devcontainer)
cdevcontainer code /path/to/another-project --ide cursor

# Manage templates
cdevcontainer template list
cdevcontainer template view my-template
cdevcontainer template edit my-template
cdevcontainer template create my-template
cdevcontainer template save my-template
cdevcontainer template load my-template
cdevcontainer template delete template1 template2
cdevcontainer template upgrade my-template
```

### CLI Environment Variables

The CLI reads the following environment variables. Run `cdevcontainer <command> --help` to see which variables apply to each command.

| Variable | Description |
|---|---|
| `DEVCONTAINER_CATALOG_URL` | Override the default catalog repository URL (supports `@tag` suffix). Used by `setup-devcontainer` and `catalog` commands. |
| `CDEVCONTAINER_SKIP_UPDATE` | Set to `1` to disable automatic update checks. |
| `CDEVCONTAINER_DEBUG_UPDATE` | Set to `1` to enable debug logging for update checks. |

### Shell Completion

Enable tab completion for all commands, subcommands, and flags. Completions stay in sync automatically after `pipx upgrade`.

```bash
# Bash — add to ~/.bashrc
eval "$(cdevcontainer completion bash)"

# Zsh — add to ~/.zshrc
eval "$(cdevcontainer completion zsh)"
```

See the [Shell Completion Guide](caylent-devcontainer-cli/docs/SHELL_COMPLETION.md) for static file installation, prerequisites, and troubleshooting.

For detailed information about the Caylent Devcontainer CLI, see the [CLI documentation](caylent-devcontainer-cli/README.md).

---

## DevContainer Catalogs

This repository serves as the **default catalog** for the Caylent DevContainer CLI. A catalog is a Git repository containing one or more entries — each entry is a complete devcontainer configuration that can be applied to a project.

Organizations can create their own specialized catalogs with custom entries, shared assets, and team-specific tooling. The CLI discovers and applies entries from any catalog repository.

### Key Concepts

- **Catalog** — A Git repository with `common/devcontainer-assets/` (shared files), `common/root-project-assets/` (root-level project files), and `catalog/` (one or more entries)
- **Entry** — A directory under `catalog/` containing `catalog-entry.json`, `devcontainer.json`, and `VERSION`
- **Common assets** — Files and directories in `common/devcontainer-assets/` that are **automatically copied into every project's `.devcontainer/`** when an entry is installed. This includes shared scripts (postcreate, functions, project-setup) and host-side proxy toolkits (`nix-family-os/`, `wsl-family-os/`). Any file or directory added to `common/devcontainer-assets/` is distributed to all projects regardless of which entry is selected.
- **Root project assets** — Files and directories in `common/root-project-assets/` that are **automatically copied into the project root** (not `.devcontainer/`) when an entry is installed. This is used for standardized root-level files such as `CLAUDE.md` (AI coding standards) and `.claude/` (Claude Code configuration). This directory is optional — catalogs without it still work normally.

### Catalog Commands

```bash
# List entries from a catalog
DEVCONTAINER_CATALOG_URL="https://github.com/your-org/your-catalog.git" \
  cdevcontainer catalog list

# Filter by tags
cdevcontainer catalog list --tags java,backend

# Validate a catalog (remote)
cdevcontainer catalog validate

# Validate a catalog (local clone)
cdevcontainer catalog validate --local /path/to/catalog
```

### Catalog Repository Structure

```
catalog-repo/
  common/
    devcontainer-assets/
      .devcontainer.postcreate.sh      # Shared postcreate hook (required)
      devcontainer-functions.sh         # Shared shell functions (required)
      project-setup.sh                 # Project-setup template (required)
      nix-family-os/                   # Host proxy toolkit for macOS/Linux
      wsl-family-os/                   # Host proxy toolkit for Windows/WSL
    root-project-assets/               # Root-level project files (optional)
      CLAUDE.md                        # AI coding standards
      .claude/                         # Claude Code configuration
  catalog/
    <entry-name>/
      catalog-entry.json               # Entry metadata (required)
      devcontainer.json                # DevContainer config (required)
      VERSION                          # Semver version (required)
```

Everything in `common/devcontainer-assets/` is automatically copied into every project's `.devcontainer/` directory — this is how shared scripts and proxy toolkits are distributed to all projects. Entry-specific files are copied first, then common assets are overlaid (common assets take precedence on name collisions).

Everything in `common/root-project-assets/` is automatically copied into the **project root** directory — this distributes standardized root-level files (such as `CLAUDE.md` and `.claude/` configuration) to all projects when an entry is installed.

### Creating a Custom Catalog

See the catalog documentation in any catalog repository's README.md for the full guide covering:

- Catalog repo structure and required files
- Adding and validating catalog entries
- The `postCreateCommand` reference
- The 3-layer customization model (catalog entries, developer templates, project-setup.sh)
- Distribution via `DEVCONTAINER_CATALOG_URL`

---

## ECR Public Image Mirror

The devcontainer base image (`mcr.microsoft.com/devcontainers/base`) is hosted on Microsoft Container Registry, which distributes images through Azure CDN. Azure CDN has limited Points of Presence (POPs) in certain regions — notably parts of South America, Africa, and Southeast Asia. Developers in these regions experience slow or unreliable image pulls when building devcontainers.

To solve this, we mirror the base image to **Amazon ECR Public**, which uses Amazon CloudFront for global distribution with broader edge coverage in underserved regions:

```
public.ecr.aws/g0u3p4x2/caylent-solutions/devcontainer-base
```

The mirror infrastructure is managed via Terraform and Terragrunt in `platform/infra/`. For full operations documentation — including how to deploy, update, destroy, and troubleshoot the ECR Public repository — see the **[ECR Public Image Mirror Infrastructure Guide](platform/infra/README.md)**.

---

## 🤝 Contributing

### Development Setup

To set up your development environment:

1. Clone the repository:
   ```bash
   git clone https://github.com/caylent-solutions/devcontainer.git
   cd devcontainer
   make configure
   ```

2. Follow the [Quick Start](#-quick-start) instructions (steps 2-5) to set up the devcontainer environment.

3. For CLI development, install the package in development mode:
   ```bash
   cd caylent-devcontainer-cli
   make install
   ```

### Quality Assurance Tasks

This repository includes comprehensive quality checks:

```bash
# Run all pre-commit checks (formatting, linting, YAML validation, security)
make pre-commit-check

# Validate catalog structure using the CLI from this repo
make validate-catalog

# Check GitHub workflow YAML files specifically
make github-workflow-yaml-lint

# Fix YAML formatting and validation issues
make yaml-fix
```

The `pre-commit-check` task runs automatically in CI/CD and includes:
- Trailing whitespace removal
- Python debug statement detection
- JSON and YAML validation with yamllint
- Large file detection
- AWS credential detection
- Merge conflict detection
- End-of-file fixing
- Private key detection
- Secret scanning with gitleaks

### Contribution Guidelines

#### If Public (Open Source)

1. Fork the repo on GitHub
2. Create a feature branch: `git checkout -b feat/my-change`
3. Ensure all tests pass: `make test`
4. Push and open a Pull Request

#### If Caylent (Internal)

1. Pull `main`: `git checkout main && git pull`
2. Create a new branch: `git checkout -b feat/thing`
3. Ensure all tests pass: `make test`
4. Commit and push: `git add . && git commit -m "feat: update thing" && git push`
5. Open a PR to `main` and request review

> All PRs must pass CI, maintain 85% test coverage, and be reviewed before merge.
> See [CONTRIBUTING.md](caylent-devcontainer-cli/docs/CONTRIBUTING.md) for detailed guidelines.
