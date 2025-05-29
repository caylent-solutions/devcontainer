#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from caylent_devcontainer_cli.commands.template import list_templates

def test_list_templates_with_exception():
    """Test list_templates when an exception occurs reading a template file."""
    with patch("os.path.exists", return_value=True):
        with patch("os.listdir", return_value=["template1.json"]):
            with patch("builtins.open", mock_open()):
                with patch("json.load", side_effect=Exception("Test error")):
                    with patch("caylent_devcontainer_cli.utils.ui.COLORS", {"CYAN": "", "GREEN": "", "RESET": ""}):
                        with patch("builtins.print") as mock_print:
                            list_templates()
                            mock_print.assert_any_call("Available templates:")