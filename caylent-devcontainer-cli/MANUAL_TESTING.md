# Manual Testing Guide

This document outlines essential manual tests to perform before creating a release tag. These tests verify functionality that automated tests cannot easily cover.

## Prerequisites

- Clean environment (preferably a fresh VM or container)
- Git installed
- Python managed by ASDF (as specified in `.tool-versions`)
- VS Code (latest version)
- Dev Containers extension for VS Code (latest version)

## Test Cases

### 1. Installation Test

**Purpose**: Verify the CLI can be installed from source

```bash
# Clone the repository
git clone https://github.com/caylent-solutions/devcontainer.git
cd devcontainer

# Install the CLI
pip install ./caylent-devcontainer-cli

# Verify installation
cdevcontainer --version
# Should display: "Caylent Devcontainer CLI X.Y.Z"
```

### 2. Interactive Setup Test

**Purpose**: Verify the interactive setup process works with user input

```bash
# Create a test directory
mkdir -p /tmp/test-project
cd /tmp/test-project

# Run the setup command in interactive mode
cdevcontainer setup-devcontainer .

# Follow the prompts with these values:
# - No saved template
# - AWS Config: false
# - Git branch: main
# - Python version: 3.12.9
# - Developer name: Test User
# - Git provider: github.com
# - Git username: testuser
# - Git email: test@example.com
# - Git token: test-token
# - Extra packages: (leave empty)
# - Don't save as template

# Verify files were created
ls -la .devcontainer/
cat devcontainer-environment-variables.json
# Should see the values you entered
```

### 3. Template Save and Load Workflow

**Purpose**: Verify the complete template workflow across projects

```bash
# Save the template from the previous test
cd /tmp/test-project
cdevcontainer template save test-template

# Create a new project
mkdir -p /tmp/test-project2
cd /tmp/test-project2

# List templates
cdevcontainer template list
# Should see "test-template" in the list

# Load the template
cdevcontainer template load test-template

# Verify the environment file was created
cat devcontainer-environment-variables.json
# Should contain the same values as the first project
```

### 4. VS Code Launch and Container Build

**Purpose**: Verify VS Code launches and builds the container correctly

```bash
# Navigate to a project with devcontainer setup
cd /tmp/test-project

# Launch VS Code
cdevcontainer code .

# Verify:
# 1. VS Code opens
# 2. You get a prompt to reopen in container
# 3. After reopening, the container builds successfully
# 4. The terminal in VS Code shows the correct environment
```

### 5. AWS Profile Configuration

**Purpose**: Verify AWS profile configuration works correctly (if applicable)

```bash
# Create a new project with AWS enabled
mkdir -p /tmp/test-project-aws
cd /tmp/test-project-aws

# Run setup with AWS enabled
cdevcontainer setup-devcontainer .

# Follow prompts, but this time set:
# - AWS_CONFIG_ENABLED: true
# - Add a simple AWS profile configuration

# Verify AWS profile map was created
cat .devcontainer/aws-profile-map.json
```

## Reporting Issues

If any test fails:

1. Note the exact command that failed
2. Capture any error messages
3. Document the environment (OS, Python version)
4. Create an issue with these details
