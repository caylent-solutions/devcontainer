#!/usr/bin/env python3
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.commands.install import install_cli


def test_install_cli_with_path_in_env():
    """Test install_cli when INSTALL_DIR is already in PATH."""
    with patch("os.path.exists", side_effect=[True, True, True]):
        with patch("caylent_devcontainer_cli.commands.install.confirm_action", return_value=True):
            with patch("shutil.copy2"):
                with patch("os.chmod"):
                    with patch("os.makedirs"):
                        with patch("os.environ.get") as mock_env_get:
                            # Mock PATH to include INSTALL_DIR
                            mock_env_get.return_value = "/usr/local/bin:/usr/bin:/bin"
                            with patch("caylent_devcontainer_cli.commands.install.INSTALL_DIR", "/usr/local/bin"):
                                install_cli()
