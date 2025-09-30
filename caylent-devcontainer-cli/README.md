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

- `setup-devcontainer`: Set up a devcontainer in a project directory
- `code`: Launch IDE (VS Code, Cursor) with the devcontainer environment
- `env`: Manage environment variables
- `template`: Manage devcontainer templates
- `install`: Install the CLI tool to your PATH
- `uninstall`: Uninstall the CLI tool

### Setting Up a Devcontainer

```bash
# Interactive setup
cdevcontainer setup-devcontainer /path/to/your/project

# Manual setup (skip interactive prompts)
cdevcontainer setup-devcontainer --manual /path/to/your/project

# Update existing devcontainer files to the current CLI version
cdevcontainer setup-devcontainer --update /path/to/your/project

# Use specific git reference (branch, tag, or commit) instead of CLI version
cdevcontainer setup-devcontainer --ref main /path/to/your/project
cdevcontainer setup-devcontainer --ref 1.0.0 /path/to/your/project
cdevcontainer setup-devcontainer --ref feature/new-feature /path/to/your/project
```

The interactive setup will guide you through:
1. Using an existing template or creating a new one
2. Configuring environment variables
3. Selecting pager preference (cat, less, more, most)
4. Setting up AWS profiles (if enabled)
5. Selecting AWS CLI output format (json, table, text, yaml) - only if AWS is enabled
6. Automatically creating a `.tool-versions` file if one doesn't exist to ensure consistent runtime management via asdf

### Managing Templates

```bash
# Save current environment as a template
cdevcontainer template save my-template

# List available templates
cdevcontainer template list

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

> **Note**: You can run `cdevcontainer code` from within any devcontainer to launch any supported IDE for other projects. This allows you to work on multiple projects simultaneously, each in their own devcontainer environment.

## Development

### Setup

For development, we recommend using the devcontainer itself. See the [Contributing Guide](CONTRIBUTING.md) for detailed setup instructions.

### Testing

```bash
# Run unit tests
make unit-test

# Run functional tests
make functional-test

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
2. Perform the [manual tests](MANUAL_TESTING.md) to verify functionality
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

Follow the manual release process documented in the [Contributing Guide](CONTRIBUTING.md#manual-release-process-when-github-actions-workflow-is-not-working).

## License

Apache License 2.0
