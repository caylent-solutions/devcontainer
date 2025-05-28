#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli import cli
from caylent_devcontainer_cli.utils.ui import set_auto_yes


def test_main_with_auto_yes():
    mock_args = MagicMock()
    mock_args.command = "test"
    mock_args.yes = True
    mock_args.func = MagicMock()
    
    with patch("argparse.ArgumentParser.parse_args", return_value=mock_args):
        with patch("caylent_devcontainer_cli.utils.ui.log"):
            with patch("caylent_devcontainer_cli.utils.ui.set_auto_yes") as mock_set_auto_yes:
                cli.main()
                
                mock_set_auto_yes.assert_called_once_with(True)
                mock_args.func.assert_called_once_with(mock_args)


def test_main_with_command():
    mock_args = MagicMock()
    mock_args.command = "test"
    mock_args.yes = False
    mock_args.func = MagicMock()
    
    with patch("argparse.ArgumentParser.parse_args", return_value=mock_args):
        with patch("caylent_devcontainer_cli.utils.ui.log"):
            cli.main()
            
            mock_args.func.assert_called_once_with(mock_args)