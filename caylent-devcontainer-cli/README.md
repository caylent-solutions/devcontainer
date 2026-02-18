# Caylent Devcontainer CLI

A command-line tool for managing Caylent devcontainer environments.

## Table of Contents

1. [Installation](#installation)
   - [Prerequisites](#prerequisites)
   - [Install CLI](#install-cli)
2. [Usage](#usage)
   - [Commands](#commands)
   - [Setting Up a Devcontainer](#setting-up-a-devcontainer)
   - [Managing Templates](#managing-templates)
   - [Launching IDEs](#launching-ides)
   - [Browsing and Validating Catalogs](#browsing-and-validating-catalogs)
   - [Catalog Tagging](#catalog-tagging)
   - [Shell Completion](#shell-completion)
3. [Development](#development)
   - [Setup](#setup)
   - [Testing](#testing)
   - [Linting and Formatting](#linting-and-formatting)
   - [Building and Publishing](#building-and-publishing)
4. [License](#license)

## Installation

### Prerequisites

The CLI requires IDE command-line tools to launch projects:

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

### Install CLI

```bash
# Install from PyPI using pipx (recommended to avoid package conflicts)
pipx install caylent-devcontainer-cli

# Install from GitHub with a specific version tag
pipx install git+https://github.com/caylent-solutions/devcontainer.git@0.1.0#subdirectory=caylent-devcontainer-cli

# If you don't have pipx installed, install it first:
python -m pip install pipx
```

## Usage

```bash
cdevcontainer --help
```

### Commands

- `catalog`: Browse and validate devcontainer catalog repositories
- `setup-devcontainer`: Set up a devcontainer in a project directory
- `code`: Launch IDE (VS Code, Cursor) with the devcontainer environment
- `template`: Manage devcontainer templates

### Global Options

- `-v, --version`: Show version information
- `--skip-update-check`: Skip automatic update check

### Update Notifications

The CLI automatically checks for updates when run in interactive environments and provides manual upgrade instructions:

```bash
🔄 Update Available
Current version: 1.10.0
Latest version:  1.11.0

Select an option:
  1 - Exit and upgrade manually
  2 - Continue without upgrading

Enter your choice [1]:
```

**Manual Upgrade Instructions by Installation Type:**
- **pipx installations**: `pipx upgrade caylent-devcontainer-cli`
- **pip installations**: Switch to pipx (recommended) or upgrade with pip
- **Editable installations**: Pull latest changes and reinstall, or switch to pipx

**Update Check Behavior:**
- **Interactive environments**: Shows update notifications with manual upgrade instructions
- **Non-interactive environments**: Skips update checks silently (CI/CD, scripts, etc.)
- **Skip mechanisms**: Use `--skip-update-check` flag or set `CDEVCONTAINER_SKIP_UPDATE=1`

**Environment Variables:**
- `DEVCONTAINER_CATALOG_URL`: Override the default catalog repository URL (e.g., `https://github.com/org/custom-catalog.git@v1.0`). When not set, the CLI auto-resolves the latest semver tag >= 2.0.0 from the default catalog repository. See [Catalog Tagging](#catalog-tagging).
- `CDEVCONTAINER_SKIP_UPDATE=1`: Globally disable all automatic update checks
- `CDEVCONTAINER_DEBUG_UPDATE=1`: Enable debug logging for update check process

**Debug Mode:**
To troubleshoot update issues, enable debug logging:
```bash
export CDEVCONTAINER_DEBUG_UPDATE=1
cdevcontainer --version
```

This will show detailed information about:
- Update check process and network requests
- Installation type detection
- Lock file operations



### Setting Up a Devcontainer

```bash
# Interactive setup (auto-resolves the latest semver tag from the default catalog)
cdevcontainer setup-devcontainer /path/to/your/project

# Use a specialized catalog (pin to a specific tag)
export DEVCONTAINER_CATALOG_URL="https://github.com/your-org/catalog.git@v1.0"
cdevcontainer setup-devcontainer /path/to/your/project

# Select a specific entry by name (requires DEVCONTAINER_CATALOG_URL)
cdevcontainer setup-devcontainer --catalog-entry java-backend /path/to/your/project

# Override catalog URL directly (bypasses tag resolution; useful for testing branches)
cdevcontainer setup-devcontainer --catalog-url "https://github.com/org/repo.git@feature/branch" /path/to/project

# Combine --catalog-url with --catalog-entry
cdevcontainer setup-devcontainer --catalog-url "https://github.com/org/repo.git@v2.0.0" --catalog-entry java-backend /path/to/project
```

The setup command will:
1. Create an empty `.tool-versions` file if one doesn't exist
2. Detect existing `.devcontainer/` configuration and show version/catalog info
3. If `.tool-versions` contains a Python entry, recommend managing Python through devcontainer features
4. Ask whether to replace existing `.devcontainer/` files or keep them
5. Clone the catalog, discover entries, and copy selected entry files to `.devcontainer/`
6. Copy common assets from `common/devcontainer-assets/` (shared scripts, host proxy toolkits) into `.devcontainer/`
7. Copy root project assets from `common/root-project-assets/` (e.g., `CLAUDE.md`, `.claude/`) into the project root
8. Run informational validation on existing project configuration files
8. Guide you through interactive template selection or creation
9. Generate project configuration files via `write_project_files()`

> **Note**: All files and directories in the catalog's `common/devcontainer-assets/` are automatically included in every project — this is how shared scripts (postcreate, functions) and host-side proxy toolkits (`nix-family-os/`, `wsl-family-os/`) are distributed.

### Managing Templates

```bash
# Save current environment as a template
cdevcontainer template save my-template

# List available templates
cdevcontainer template list

# View a template's configuration values
cdevcontainer template view my-template

# Edit an existing template interactively
cdevcontainer template edit my-template

# Load a template into a project
cdevcontainer template load my-template

# Delete one or more templates
cdevcontainer template delete template1 template2

# Upgrade a template to the current CLI version
cdevcontainer template upgrade my-template
```

When using templates created with older versions of the CLI, the tool will automatically detect version mismatches and provide options to:
- Upgrade the profile to the current version
- Create a new profile from scratch
- Try to use the profile anyway (with a warning)
- Exit without making changes

### Launching IDEs

```bash
# Launch VS Code for the current project (default)
cdevcontainer code

# Launch Cursor for the current project
cdevcontainer code --ide cursor

# Launch VS Code for a specific project
cdevcontainer code /path/to/your/project

# Launch Cursor for a specific project
cdevcontainer code /path/to/your/project --ide cursor

# Launch IDE for another project (works from within any devcontainer)
cdevcontainer code /path/to/another-project --ide cursor
```

**Supported IDEs:**
- `vscode` - Visual Studio Code (default)
- `cursor` - Cursor AI IDE

**Options:**
- `--regenerate-shell-env` - Regenerate `shell.env` from existing JSON configuration without running full setup

**Validation:** Before launching, the code command validates environment variables against both the base configuration and the developer template. If missing variables are detected, you will be prompted to update project files or add the missing variables.

> **Note**: You can run `cdevcontainer code` from within any devcontainer to launch any supported IDE for other projects. This allows you to work on multiple projects simultaneously, each in their own devcontainer environment.

### Browsing and Validating Catalogs

```bash
# List available devcontainer configurations from the default catalog
cdevcontainer catalog list

# Filter entries by tags (ANY match)
cdevcontainer catalog list --tags java,python

# Validate the default catalog
cdevcontainer catalog validate

# Validate a local catalog directory
cdevcontainer catalog validate --local /path/to/catalog

# Use a custom catalog repository
export DEVCONTAINER_CATALOG_URL="https://github.com/org/custom-catalog.git@v1.0"
cdevcontainer catalog list

# Override catalog URL directly (bypasses tag resolution and DEVCONTAINER_CATALOG_URL)
cdevcontainer catalog list --catalog-url "https://github.com/org/repo.git@feature/branch"
cdevcontainer catalog validate --catalog-url "https://github.com/org/repo.git@feature/branch"
```

### Catalog Tagging

All catalog repositories should use semver tags (e.g. `2.0.0`, `2.1.0`) for releases. The CLI relies on tags for deterministic, reproducible behavior:

- **Default catalog**: When `DEVCONTAINER_CATALOG_URL` is not set, the CLI queries `git ls-remote --tags` against the default catalog and selects the latest semver tag >= `2.0.0`. This ensures the CLI always clones a known release rather than the default branch.
- **Custom catalogs**: When setting `DEVCONTAINER_CATALOG_URL`, use the `@tag` suffix to pin to a specific version (e.g., `https://github.com/org/catalog.git@1.2.0`). Without a tag suffix, the default branch is cloned.

**Recommendations for catalog maintainers:**
- Tag every release with a semver version (`MAJOR.MINOR.PATCH`)
- Do not rely on the default branch (`main`) for production use
- Use annotated tags (`git tag -a 2.1.0 -m "Release 2.1.0"`) for provenance
- Place shared files in `common/devcontainer-assets/` — everything in this directory is automatically copied into every project's `.devcontainer/` regardless of which entry is selected
- Place root-level project files in `common/root-project-assets/` — everything in this directory is automatically copied into the **project root** (e.g., `CLAUDE.md`, `.claude/`). This directory is optional.
- Place entry-specific files (e.g., `devcontainer.json`, `catalog-entry.json`) in `catalog/<name>/`

### Shell Completion

Enable tab completion for all commands, subcommands, and flags. Completions stay in sync automatically after `pipx upgrade`.

```bash
# Bash — add to ~/.bashrc
eval "$(cdevcontainer completion bash)"

# Zsh — add to ~/.zshrc
eval "$(cdevcontainer completion zsh)"
```

For static file installation, prerequisites, troubleshooting, and verification steps, see the [Shell Completion Guide](docs/SHELL_COMPLETION.md).

## Development

### Setup

For development, we recommend using the devcontainer itself. See the [Contributing Guide](docs/CONTRIBUTING.md) for detailed setup instructions.

### Testing

```bash
# Run unit tests
make unit-test

# Run functional tests
make functional-test

# Run all tests
make test

# Generate coverage report
make coverage

# View functional test coverage report
make functional-test-report
```

#### Testing Requirements

- **Unit Tests**: Must maintain at least 90% code coverage
- **Functional Tests**: Must test CLI commands as they would be used by actual users
- All tests must pass before merging code

### Code Quality and Validation

```bash
# Check code style (Python linting)
make lint

# Format code (Python formatting)
make format

# Check GitHub workflow YAML files (from repository root)
make github-workflow-yaml-lint

# Run comprehensive pre-commit checks (from repository root)
make pre-commit-check

# Fix YAML formatting issues (from repository root)
make yaml-fix
```

The repository includes comprehensive quality assurance with pre-commit hooks that run automatically in CI/CD, including YAML validation, security scanning, and code formatting.

### Building and Publishing

#### Automated Release Process

The package is automatically published to PyPI when a new tag is pushed to GitHub.

To create a new release:

1. Ensure all tests pass (`make test`)
2. Perform the [manual tests](docs/MANUAL_TESTING.md) to verify functionality
3. Create and push a new tag following semantic versioning:

```bash
git tag -a X.Y.Z -m "Release X.Y.Z"
git push origin X.Y.Z
```

The GitHub Actions workflow will:
1. Validate the tag follows semantic versioning (MAJOR.MINOR.PATCH)
2. Build the package using ASDF for Python version management
3. Publish the package to PyPI

#### Manual Release Process

Follow the manual release process documented in the [Contributing Guide](docs/CONTRIBUTING.md#manual-release-process-when-github-actions-workflow-is-not-working).

## License

Apache License 2.0
