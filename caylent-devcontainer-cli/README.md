# Caylent Devcontainer CLI

A command-line tool for managing Caylent devcontainers.

## Features

- Launch VS Code with the devcontainer environment
- Manage environment variables
- Save and load configuration templates
- Install the CLI tool to your PATH

## Installation

### Install from GitHub

```bash
pip install git+https://github.com/caylent-solutions/devcontainer.git#subdirectory=caylent-devcontainer-cli
```

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

### Installation management

```bash
# Install the CLI tool to your PATH
cdevcontainer install

# Uninstall the CLI tool
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

# Format the code
make format

# Run unit tests with coverage
make test

# Clean build artifacts
make clean

# Build the package
make build
```

## Versioning

The CLI version is determined by the git tag of the repository. When a new tag is created, the CLI version will be updated accordingly.

For example, if the repository is tagged with `v1.0.0`, the CLI version will be `1.0.0`.