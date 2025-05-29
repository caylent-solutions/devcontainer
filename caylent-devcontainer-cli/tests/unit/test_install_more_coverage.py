#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.commands.install import install_cli, uninstall_cli


def test_install_cli_script_not_found():
    """Test install_cli when script is not found."""
    with patch("os.path.exists", return_value=False):
        with pytest.raises(SystemExit):
            install_cli()
