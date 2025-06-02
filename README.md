# Caylent Devcontainer Base

## 📑 Table of Contents

- [🚀 Overview](#-overview)
- [🧰 What's Included](#-whats-included)
- [💡 Built-In Tooling](#-built-in-tooling)
- [🖥 Prerequisites](#-prerequisites)
- [🪄 Quick Start](#-quick-start)
- [🧩 Post-Launch Setup](#-post-launch-setup)
- [🐍 Python Install Logic](#-python-install-logic)
- [🔄 Rebuilding the Devcontainer](#-rebuilding-the-devcontainer)
- [🐳 Docker-in-Docker Support](#-docker-in-docker-support)
- [📡 Debug Ports](#-debug-ports)
- [🧩 JetBrains Compatibility](#-jetbrains-compatibility)
- [📁 File Reference](#-file-reference)
- [🧪 Validate Your Config](#-validate-your-config)
- [🧼 Git Hygiene](#-git-hygiene)
- [🛠️ CLI Reference](#️-cli-reference)
- [🤝 Contributing](#-contributing)

## 🚀 Overview

This repository provides the **base development container** configuration used across Caylent engineering projects. It is designed to be:

- ✅ **Cross-platform**: macOS and Windows (WSL2) compatible using VS Code
- 🧱 **Reusable**: drop into any repo to enable consistent local dev experience
- 🔐 **Secure and configurable**: injects secrets via environment, not committed
- 🧩 **Smart defaults**: tools, AWS profiles, aliases, Python setup, Git config, and more
- 🧪 **Consistent environments**: ensures identical local dev setups across teams using `asdf` to pin and manage exact binary versions

📦 Repo URL: [`https://github.com/caylent-solutions/devcontainer`](https://github.com/caylent-solutions/devcontainer)

---

## 🧰 What's Included

- `devcontainer.json` — VS Code container definition
- `.devcontainer.postcreate.sh` — container setup script
- `cdevcontainer` — Caylent Devcontainer CLI tool for environment management
- `example-aws-profile-map.json` — declarative AWS SSO profile config template
- Git, AWS CLI, Docker, Python, `asdf`, aliases, shell profile injection
- Extension support for Amazon Q and GitHub Copilot

---

## 💡 Built-In Tooling

The devcontainer installs:

- ✅ Amazon Q VS Code extension
- ✅ GitHub Copilot + Copilot Chat
- ✅ GitLens, YAML, Python, Docker, Makefile Tools
- ✅ Jinja, spell checking

These extensions are auto-installed on container start.

---

## 🖥 Prerequisites

### For macOS
- [VS Code](https://code.visualstudio.com/Download)
- [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- [Homebrew](https://brew.sh/) — optional
- Python 3.12.9 - [Installation Guide](supplemental-docs/PYTHON_INSTALL.md#for-macos-using-asdf)

### For Windows
- [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install)
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- [VS Code](https://code.visualstudio.com/Download)
- Python 3.12.9 - [Installation Guide](supplemental-docs/PYTHON_INSTALL.md#for-windows-using-windows-store-or-official-installer)

---

## 🪄 Quick Start

### 1. Install the CLI Tool

First, install the Caylent Devcontainer CLI:

```bash
pip install caylent-devcontainer-cli
```

You can also install a specific version:

```bash
pip install caylent-devcontainer-cli==1.1.0
```

To install directly from GitHub (alternative method):

```bash
pip install git+https://github.com/caylent-solutions/devcontainer.git@1.1.0#subdirectory=caylent-devcontainer-cli
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
1. Guide you through an interactive setup process
2. Let you select or create a template for your environment
3. Configure AWS profiles if needed
4. Copy the devcontainer files to your project

If you prefer to set up manually, use the `--manual` flag:

```bash
cdevcontainer setup-devcontainer --manual /path/to/your/project
```

To update an existing devcontainer setup to the latest version:

```bash
cdevcontainer setup-devcontainer --update /path/to/your/project
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

The interactive setup will create a `devcontainer-environment-variables.json` file with your settings.

If you prefer to configure manually:

```bash
cp .devcontainer/example-container-env-values.json devcontainer-environment-variables.json
```

Then edit `devcontainer-environment-variables.json` with your values:
- `AWS_CONFIG_ENABLED` (default: `true`) - Set to `false` to disable AWS configuration
- `DEFAULT_GIT_BRANCH` (e.g. `main`)
- `DEFAULT_PYTHON_VERSION` (e.g. `3.12.9`)
- Git credentials: `GIT_USER`, `GIT_USER_EMAIL`, `GIT_TOKEN`
- AWS SSO and account information (required if `AWS_CONFIG_ENABLED=true`)
- Extra Ubuntu LTS packages: `EXTRA_APT_PACKAGES`

#### Client/Project Templates

The `setup-devcontainer` command will ask if you want to:
- Use an existing template
- Create a new reusable template
- Create a one-time configuration

Templates are saved in `~/.devcontainer-templates/` and can be reused across projects.

You can also manage templates directly:

```bash
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

---

### 4. Configure AWS Profile Map (Optional)

By default, AWS configuration is enabled. If you don't need AWS access, you can disable it during the interactive setup or by setting `AWS_CONFIG_ENABLED=false` in your `devcontainer-environment-variables.json`.

When using the interactive setup with AWS enabled, you'll be prompted to enter your AWS profile configuration in JSON format. The setup will validate your input and create the AWS profile map file automatically.

If configuring manually, copy the example:
```bash
cp .devcontainer/example-aws-profile-map.json .devcontainer/aws-profile-map.json
```

Edit `.devcontainer/aws-profile-map.json` to define your AWS SSO accounts:

```json
{
  "default": {
    "region": "us-east-2",
    "sso_start_url": "https://your-org.awsapps.com/start",
    "sso_region": "us-east-1",
    "account_name": "your-default-account",
    "account_id": "123456789012",
    "role_name": "AdministratorAccess"
  },
  ...
}
```

> ⚠️ This file is required only when AWS configuration is enabled (`AWS_CONFIG_ENABLED=true`).
>
> AWS configuration is completely optional and not required for using Amazon Q.

---

### 5. Setting Up Your Environment

```bash
# Launch VS Code for the current project
cdevcontainer code

# Launch VS Code for a specific project
cdevcontainer code /path/to/your-project
```

This will:
- Generate `shell.env` from your `devcontainer-environment-variables.json`
- Load the environment variables
- Launch VS Code
- Display a confirmation message

To skip all confirmation prompts, use the `-y` or `--yes` flag:

```bash
cdevcontainer code -y
```

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

---

## 🧩 Post-Launch Setup

### 🧠 GitHub Copilot

- Auto-installed
- Login prompt appears if not authenticated
- To verify: open any `.py` file and type a comment — suggestions will appear

### 🤖 Amazon Q

- Open the Amazon Q sidebar (left bar in VS Code) or use Command+Shift+P and type "AmazonQ: Open Chat"
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

Or open the Source Control tab in VS Code to confirm the repo is accessible.

---

## 🐍 Python Install Logic

- `.tool-versions` present with Python? → installs that pinned Python version
- Not present or no Python entry? → installs fallback version from:
```json
"DEFAULT_PYTHON_VERSION": "3.12.9"
```

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

1. A popup will typically appear in VS Code prompting you to rebuild when configuration files change
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
- VS Code is **strongly recommended** for full compatibility

---

## 📁 File Reference

| File | Purpose |
|------|---------|
| `.devcontainer/devcontainer.json` | VS Code container setup |
| `.devcontainer/.devcontainer.postcreate.sh` | Container provisioning logic |
| `.devcontainer/example-aws-profile-map.json` | AWS profile template |
| `.devcontainer/aws-profile-map.json` | Your active AWS profiles |
| `.devcontainer/example-container-env-values.json` | Developer config example |

---

## 🧪 Validate Your Config

```bash
cdevcontainer env export devcontainer-environment-variables.json -o /tmp/test-env.sh
```

This will validate your configuration file and show any errors. For example:

```
[ERR] Error loading devcontainer-environment-variables.json: Expecting property name enclosed in double quotes
[ERR] JSON must contain a 'containerEnv' object.
```

If the validation succeeds, you'll see:

```
[OK] Wrote 12 exports to /tmp/test-env.sh
```

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
> This approach lets you version control the devcontainer configuration while excluding sensitive information. When you need to update the devcontainer, run:
> ```bash
> cdevcontainer setup-devcontainer --update .
> git add .devcontainer
> git commit -m "chore: Update devcontainer to version X.Y.Z"
> ```

---

## 🛠️ CLI Reference

The Caylent Devcontainer CLI provides several commands to manage your devcontainer environment:

```bash
# Show help
cdevcontainer --help

# Set up a devcontainer in a project directory
cdevcontainer setup-devcontainer /path/to/your/project

# Launch VS Code with the devcontainer environment
cdevcontainer code [/path/to/your/project]

# Manage templates
cdevcontainer template list
cdevcontainer template save my-template
cdevcontainer template load my-template
cdevcontainer template delete template1 template2
cdevcontainer template upgrade my-template

# Manage environment variables
cdevcontainer env export input.json -o output.sh
cdevcontainer env load

# Install/uninstall the CLI
cdevcontainer install
cdevcontainer uninstall
```

For detailed information about the Caylent Devcontainer CLI, see the [CLI documentation](caylent-devcontainer-cli/README.md).

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
> See [CONTRIBUTING.md](caylent-devcontainer-cli/CONTRIBUTING.md) for detailed guidelines.
