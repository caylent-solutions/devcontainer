# Testing the Caylent Devcontainer CLI

This directory contains tests for the Caylent Devcontainer CLI.

## Test Structure

The tests are organized into two main categories:

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
- **Functional Tests** (`tests/functional/`): Test CLI commands as they would be used by actual users

## Running Tests

### Unit Tests

Unit tests verify that individual components work correctly in isolation.

```bash
make unit-test
```

### Functional Tests

Functional tests verify that the CLI commands work correctly from a user's perspective.

```bash
make functional-test
```

### All Tests

Run both unit and functional tests:

```bash
make test
```

## Test Coverage

We aim to maintain at least 90% code coverage for unit tests.

To generate a coverage report:

```bash
make coverage
```

This will create an HTML report in the `htmlcov/` directory.

For a text-based coverage report:

```bash
make coverage-text
```

## Functional Test Coverage

To see a report of which CLI commands are covered by functional tests:

```bash
make functional-test-report
```

## Writing Tests

### Unit Tests

- Place unit tests in the `tests/unit/` directory
- Name test files with the prefix `test_`
- Use pytest fixtures for common setup
- Mock external dependencies

### Functional Tests

- Place functional tests in the `tests/functional/` directory
- Name test files with the prefix `test_`
- Test the CLI commands as they would be used by actual users
- Use the `run_command` function to execute CLI commands
- Verify both successful and error scenarios

## Test Requirements

- All tests must pass before merging code
- Unit tests must maintain at least 90% code coverage
- Functional tests must cover all CLI commands and common error scenarios
- Tests should be fast and not depend on external services

## Example Test

```python
def test_help_command():
    """Test the help command."""
    result = run_command(["cdevcontainer", "--help"])

    # Check that the command succeeded
    assert result.returncode == 0

    # Check that the output contains expected commands
    assert "setup-devcontainer" in result.stdout
    assert "code" in result.stdout
    assert "template" in result.stdout
```
