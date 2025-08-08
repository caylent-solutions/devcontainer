# Contributing to Caylent Devcontainer CLI

Thank you for your interest in contributing to the Caylent Devcontainer CLI! This document provides guidelines and instructions for contributing to this project.

## Development Setup

The recommended way to set up your development environment is to use the devcontainer itself:

1. Ensure you have the [prerequisites](../README.md#-prerequisites) installed:
   - VS Code (latest version)
   - Docker Desktop
   - Dev Containers extension for VS Code (latest version)

2. Clone the repository:
   ```bash
   git clone https://github.com/caylent-solutions/devcontainer.git
   cd devcontainer
   ```

3. Set up git hooks to ensure code quality:
   ```bash
   make configure
   ```

   This will:
   - Install pre-commit using asdf (or pip if asdf is not available)
   - Set up git hooks that:
     - Prevent secrets from being committed (AWS credentials, private keys)
     - Automatically format code in the CLI subdirectory
     - Ensure tests and linting pass before pushing CLI changes

4. Launch VS Code with the devcontainer:
   ```bash
   # If you already have the CLI installed
   cdevcontainer code .

   # Or open VS Code manually and reopen in container when prompted
   code .
   ```

5. For CLI development, install the package in development mode:
   ```bash
   cd caylent-devcontainer-cli
   make install
   ```

For more detailed setup instructions, see the [Quick Start](../README.md#-quick-start) guide in the main README.

## Code Style and Quality

We use the following tools to maintain code quality:

- **Black**: For code formatting
- **isort**: For import sorting  
- **flake8**: For linting
- **yamllint**: For YAML validation and formatting

Before submitting a pull request, ensure your code passes all style checks:

```bash
make lint
```

If there are any issues, you can automatically fix most of them with:

```bash
make format
```

### Repository-Wide Quality Checks

From the repository root, you can run comprehensive quality checks:

```bash
# Run all pre-commit checks (includes YAML validation, security scanning, etc.)
make pre-commit-check

# Check GitHub workflow YAML files specifically
make github-workflow-yaml-lint  

# Fix YAML formatting and validation issues
make yaml-fix
```

These checks run automatically in CI/CD and include trailing whitespace removal, debug statement detection, JSON/YAML validation, security scanning, and more.

## Testing

### Unit Tests

Unit tests are located in the `tests/unit` directory. They test individual components of the code in isolation.

To run unit tests:

```bash
make unit-test
```

### Functional Tests

Functional tests are located in the `tests/functional` directory. They test the CLI commands as they would be used by actual users.

To run functional tests:

```bash
make functional-test
```

To see a report of functional test coverage:

```bash
make functional-test-report
```

### Test Requirements

- **Unit Tests**: Must maintain at least 90% code coverage
- **Functional Tests**: Must test all CLI commands and common error scenarios
- All tests must pass before merging code

## Adding New Features

When adding new features:

1. Create unit tests for all new code
2. Create functional tests that test the feature from a user's perspective
3. Update documentation in the README.md file
4. Update help text in the CLI commands

## Pull Request Process

### For External Contributors

1. Fork the repository on GitHub
2. Create a feature branch: `git checkout -b feat/my-change`
3. Implement your changes with appropriate tests
4. Ensure all tests pass and code meets style guidelines
5. Submit a pull request with a clear description of the changes

### For Caylent Internal Contributors

1. Pull `main`: `git checkout main && git pull`
2. Create a new branch: `git checkout -b feat/thing`
3. Implement your changes with appropriate tests
4. Ensure all tests pass: `make test`
5. Commit and push: `git add . && git commit -m "feat: update thing" && git push`
6. Open a PR to `main` and request review

## Release Process

### Automated Release

Releases are automatically published to PyPI when a new tag is pushed to GitHub.

1. Ensure all tests pass (`make test`)
2. Perform the [manual tests](MANUAL_TESTING.md) to verify functionality
3. Create and push a new tag following semantic versioning:
   ```bash
   git tag -a X.Y.Z -m "Release X.Y.Z"
   git push origin X.Y.Z
   ```

The GitHub Actions workflow will validate the tag format, build the package, and publish it to PyPI.

### Manual Release Process

Follow these steps for a manual release:

1. Start from the latest main branch:
   ```bash
   git checkout main
   git pull origin main
   ```

2. Create a release branch:
   ```bash
   git checkout -b release-X.Y.Z
   ```

3. Update version numbers in the following files:
   - `src/caylent_devcontainer_cli/__init__.py`: Update `__version__ = "X.Y.Z"`
   - `pyproject.toml`: Update `version = "X.Y.Z"`

4. Update the CHANGELOG.md with the new version and changes:
   ```markdown
   # CHANGELOG

   ## vX.Y.Z (YYYY-MM-DD)

   ### Category (Fix, Feature, etc.)

   * description of the change
   ```

5. Run tests to ensure everything passes:
   ```bash
   cd caylent-devcontainer-cli
   make test
   ```

7. Commit the version changes:
   ```bash
   git add src/caylent_devcontainer_cli/__init__.py pyproject.toml CHANGELOG.md
   git commit -m "chore(release): X.Y.Z"
   ```

8. Push the branch and create a pull request:
   ```bash
   git push -u origin release-X.Y.Z
   ```

   Create a PR from the release branch to main through the GitHub interface.

9. After the PR is reviewed and merged to main, checkout main and pull:
   ```bash
   git checkout main
   git pull origin main
   ```

10. Create and push a git tag:
    ```bash
    git tag -a "X.Y.Z" -m "Release X.Y.Z"
    git push origin X.Y.Z
    ```

11. Build the package:
    ```bash
    cd caylent-devcontainer-cli
    make clean
    make build
    make distcheck
    ```

12. Upload to PyPI (requires PyPI credentials):
    ```bash
    python -m twine upload dist/*
    ```

13. Verify the package is available on PyPI:
    ```bash
    pip install caylent-devcontainer-cli==X.Y.Z
    ```
