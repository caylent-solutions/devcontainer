#!/usr/bin/env python3
import pytest
import os
import sys

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

@pytest.fixture
def temp_dir(tmpdir):
    """Fixture to provide a temporary directory."""
    return tmpdir

@pytest.fixture
def mock_project_dir(temp_dir):
    """Fixture to create a mock project directory with .devcontainer folder."""
    project_dir = temp_dir.mkdir("test-project")
    devcontainer_dir = project_dir.mkdir(".devcontainer")
    return project_dir

@pytest.fixture
def mock_env_file(mock_project_dir):
    """Fixture to create a mock environment variables JSON file."""
    env_file = mock_project_dir.join("devcontainer-environment-variables.json")
    env_file.write('''
    {
        "containerEnv": {
            "TEST_VAR": "test_value",
            "ANOTHER_VAR": "another_value"
        }
    }
    ''')
    return env_file