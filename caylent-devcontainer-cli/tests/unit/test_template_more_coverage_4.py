#!/usr/bin/env python3
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.template import delete_template


def test_delete_template_with_exception():
    """Test delete_template when an exception occurs."""
    with patch("os.path.exists", return_value=True):
        with patch("caylent_devcontainer_cli.commands.template.confirm_action", return_value=True):
            with patch("os.remove", side_effect=Exception("Test error")):
                delete_template("test-template")
