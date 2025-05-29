#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.cli import main


def test_main_with_version_flag():
    """Test main with version flag."""
    with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value = MagicMock(command="version", func=MagicMock())
        main()


def test_main_with_help_flag():
    """Test main with help flag."""
    with patch("argparse.ArgumentParser.parse_args") as mock_parse_args, patch(
        "argparse.ArgumentParser.print_help"
    ) as mock_print_help, patch("sys.exit") as mock_exit:
        # Create a mock that will raise SystemExit when sys.exit is called
        mock_exit.side_effect = SystemExit(1)

        # Create a mock args object without func attribute
        mock_args = MagicMock()
        delattr(mock_args, "func")
        mock_parse_args.return_value = mock_args

        # The function should raise SystemExit
        with pytest.raises(SystemExit):
            main()

        # Verify print_help was called
        mock_print_help.assert_called_once()


def test_main_with_command():
    """Test main with a valid command."""
    mock_func = MagicMock()
    with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value = MagicMock(command="code", func=mock_func, yes=False)
        main()
        mock_func.assert_called_once()


def test_main_with_yes_flag():
    """Test main with yes flag."""
    mock_func = MagicMock()
    with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value = MagicMock(command="code", func=mock_func, yes=True)
        with patch("caylent_devcontainer_cli.utils.ui.set_auto_yes") as mock_set_auto_yes:
            main()
            mock_set_auto_yes.assert_called_once_with(True)
            mock_func.assert_called_once()


def test_main_with_exception():
    """Test main when an exception occurs."""
    with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.side_effect = Exception("Test error")
        with pytest.raises(Exception):
            main()
