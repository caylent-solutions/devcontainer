# Caylent Devcontainer CLI

A command-line tool for managing Caylent devcontainers.

## Features

- Launch VS Code with the devcontainer environment
- Manage environment variables
- Save and load configuration templates
- Install the CLI tool to your PATH

## Installation

For detailed installation instructions, please refer to the [Quick Start section in the main README](../README.md#-quick-start).

## Usage

### Launch VS Code with the devcontainer environment

```bash
# Launch VS Code for the current project
cdevcontainer code

# Launch VS Code for a specific project
cdevcontainer code /path/to/your/project
```

### Manage environment variables

```bash
# Generate shell exports from JSON
cdevcontainer env export devcontainer-environment-variables.json -o shell.env

# Load environment variables
cdevcontainer env load
```

### Manage templates

```bash
# Save current environment as a template
cdevcontainer template save client1

# List available templates
cdevcontainer template list

# Load a template into current project
cdevcontainer template load client1
```

### Self-management

```bash
# Fix PATH issues or reinstall symlinks after code changes
# Use when: the command isn't found, you've updated the CLI code, or changed Python environments
cdevcontainer install

# Completely remove the CLI tool and its symlinks from your system
# Use when: you no longer need the tool or want to perform a clean reinstallation
cdevcontainer uninstall
```

## Development

For development setup and contribution guidelines, please refer to the [main repository README](../README.md#🤝-contributing).

### Development Tasks

Once you have the devcontainer set up, you can use the following Makefile tasks:

```bash
# Install the package in development mode
make install

# Run linting checks
make lint

# Auto-fix linting issues
make format

# Run unit tests with coverage
make test

# Clean build artifacts
make clean

# Build the package
make build
```

### Note on Tests

The test suite is currently being updated. Some tests may fail due to changes in the codebase structure. 
If you're contributing, please ensure your changes don't break existing functionality.

## Versioning

The CLI version is determined by the git tag of the repository. When a new tag is created, the CLI version will be updated accordingly.

For example, if the repository is tagged with `v1.0.0`, the CLI version will be `1.0.0`.