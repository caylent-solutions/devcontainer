#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.commands.setup_interactive import JsonValidator


def test_json_validator_with_json():
    """Test JsonValidator with valid JSON."""
    validator = JsonValidator()
    document = MagicMock()
    document.text = '{"test": "value"}'

    # Should not raise an exception for valid JSON
    validator.validate(document)
