# Caylent Devcontainer CLI

A command-line tool for managing Caylent devcontainer environments.

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
   - [Commands](#commands)
   - [Setting Up a Devcontainer](#setting-up-a-devcontainer)
   - [Managing Templates](#managing-templates)
   - [Launching VS Code](#launching-vs-code)
3. [Development](#development)
   - [Setup](#setup)
   - [Testing](#testing)
   - [Linting and Formatting](#linting-and-formatting)
   - [Building and Publishing](#building-and-publishing)
4. [License](#license)

## Installation

```bash
# Install from PyPI (when available)
pip install caylent-devcontainer-cli

# Install from GitHub with a specific version tag
pip install git+https://github.com/caylent-solutions/devcontainer.git@0.1.0#subdirectory=caylent-devcontainer-cli
```

## Usage

```bash
cdevcontainer --help
```

### Commands

- `setup-devcontainer`: Set up a devcontainer in a project directory
- `code`: Launch VS Code with the devcontainer environment
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
```

The interactive setup will guide you through:
1. Using an existing template or creating a new one
2. Configuring environment variables
3. Setting up AWS profiles (if enabled)

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

### Launching VS Code

```bash
# Launch VS Code for the current project
cdevcontainer code

# Launch VS Code for a specific project
cdevcontainer code /path/to/your/project
```

## Development

### Setup

For development, we recommend using the devcontainer itself. See the [Contributing Guide](CONTRIBUTING.md) for detailed setup instructions.

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

### Linting and Formatting

```bash
# Check code style
make lint

# Format code
make format
```

### Building and Publishing

The package is automatically published to PyPI when a new tag is pushed to GitHub.

To create a new release:

1. Ensure all tests pass (`make test`)
2. Perform the [manual tests](MANUAL_TESTING.md) to verify functionality
3. Create and push a new tag following semantic versioning:

```bash
git tag -a 0.1.0 -m "Release 0.1.0"
git push origin 0.1.0
```

The GitHub Actions workflow will:
1. Validate the tag follows semantic versioning (MAJOR.MINOR.PATCH)
2. Build the package using ASDF for Python version management
3. Publish the package to PyPI

## License

Apache License 2.0
