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

3. Launch VS Code with the devcontainer:
   ```bash
   # If you already have the CLI installed
   cdevcontainer code .
   
   # Or open VS Code manually and reopen in container when prompted
   code .
   ```

4. For CLI development, install the package in development mode:
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

Before submitting a pull request, ensure your code passes all style checks:

```bash
make lint
```

If there are any issues, you can automatically fix most of them with:

```bash
make format
```

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

Releases are automatically published to PyPI when a new tag is pushed to GitHub.

1. Ensure all tests pass (`make test`)
2. Perform the [manual tests](MANUAL_TESTING.md) to verify functionality
3. Create and push a new tag following semantic versioning:
   ```bash
   git tag -a X.Y.Z -m "Release X.Y.Z"
   git push origin X.Y.Z
   ```

The GitHub Actions workflow will validate the tag format, build the package, and publish it to PyPI.