"""Pytest configuration for functional tests."""

import os
import shutil
import tempfile

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def temp_project_dir(temp_dir):
    """Create a temporary project directory for testing."""
    project_dir = os.path.join(temp_dir, "test-project")
    os.makedirs(project_dir)
    yield project_dir
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)


@pytest.fixture
def temp_home_dir(temp_dir, monkeypatch):
    """Create a temporary home directory for testing."""
    home_dir = os.path.join(temp_dir, "home")
    os.makedirs(home_dir)
    monkeypatch.setenv("HOME", home_dir)
    monkeypatch.setenv("USERPROFILE", home_dir)  # For Windows

    # Create templates directory
    templates_dir = os.path.join(home_dir, ".devcontainer-templates")
    os.makedirs(templates_dir)

    yield home_dir
    if os.path.exists(home_dir):
        shutil.rmtree(home_dir)
