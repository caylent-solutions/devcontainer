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
# - Press Enter when prompted to create .tool-versions file

# Verify files were created
ls -la .devcontainer/
cat devcontainer-environment-variables.json
# Should see the values you entered
cat .tool-versions
# Should contain: python 3.12.9
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
# - Press Enter when prompted to create .tool-versions file

# Verify AWS profile map was created
cat .devcontainer/aws-profile-map.json
# Verify .tool-versions was created
cat .tool-versions
```

### 6. .tool-versions File Management Test

**Purpose**: Verify .tool-versions file detection and creation

```bash
# Test 1: Project without .tool-versions
mkdir -p /tmp/test-no-tool-versions
cd /tmp/test-no-tool-versions

# Run setup (manual mode for simplicity)
cdevcontainer setup-devcontainer --manual .
# Should prompt to create .tool-versions file
# Press Enter to create it

# Verify file was created with correct content
cat .tool-versions
# Should contain: python 3.12.9

# Test 2: Project with existing .tool-versions
mkdir -p /tmp/test-existing-tool-versions
cd /tmp/test-existing-tool-versions
echo "python 3.11.5" > .tool-versions

# Run setup
cdevcontainer setup-devcontainer --manual .
# Should detect existing file and not prompt to create

# Verify original content preserved
cat .tool-versions
# Should still contain: python 3.11.5
```

### 7. Git Reference Override Test

**Purpose**: Verify the --ref flag works with different git references

```bash
# Test 1: Use main branch instead of CLI version
mkdir -p /tmp/test-ref-main
cd /tmp/test-ref-main

# Run setup with main branch
cdevcontainer setup-devcontainer --ref main --manual .
# Should clone from main branch instead of CLI version tag

# Verify files were created
ls -la .devcontainer/
# Should see devcontainer files

# Test 2: Use specific tag
mkdir -p /tmp/test-ref-tag
cd /tmp/test-ref-tag

# Run setup with specific tag (use a known existing tag)
cdevcontainer setup-devcontainer --ref 1.0.0 --manual .
# Should clone from the specified tag

# Verify files were created
ls -la .devcontainer/
# Should see devcontainer files

# Test 3: Invalid reference should fail gracefully
mkdir -p /tmp/test-ref-invalid
cd /tmp/test-ref-invalid

# Run setup with invalid reference
cdevcontainer setup-devcontainer --ref nonexistent-branch --manual .
# Should fail with clear error message about the reference not existing
```

## Reporting Issues

If any test fails:

1. Note the exact command that failed
2. Capture any error messages
3. Document the environment (OS, Python version)
4. Create an issue with these details
