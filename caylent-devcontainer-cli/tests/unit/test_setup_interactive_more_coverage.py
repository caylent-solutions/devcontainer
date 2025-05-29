#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.setup_interactive import JsonValidator


def test_json_validator_empty():
    """Test JsonValidator with empty string."""
    validator = JsonValidator()
    document = MagicMock()
    document.text = ""

    # Should not raise an exception for empty string
    validator.validate(document)
