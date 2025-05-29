#!/usr/bin/env python3
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.commands.setup import copy_devcontainer_files


def test_copy_devcontainer_files_with_examples():
    """Test that copy_devcontainer_files keeps example files when keep_examples is True."""
    with patch("os.path.exists", return_value=True), patch("shutil.copytree") as mock_copytree, patch(
        "os.remove"
    ) as mock_remove, patch("caylent_devcontainer_cli.commands.setup.confirm_action", return_value=True):

        copy_devcontainer_files("/source", "/target", keep_examples=True)

        # Check that copytree was called
        mock_copytree.assert_called_once()

        # Check that remove was not called
        mock_remove.assert_not_called()


def test_copy_devcontainer_files_without_examples():
    """Test that copy_devcontainer_files removes example files when keep_examples is False."""
    with patch("os.path.exists", side_effect=[True, True, True]), patch("shutil.copytree") as mock_copytree, patch(
        "os.remove"
    ) as mock_remove, patch("caylent_devcontainer_cli.commands.setup.confirm_action", return_value=True):

        copy_devcontainer_files("/source", "/target", keep_examples=False)

        # Check that copytree was called
        mock_copytree.assert_called_once()

        # Check that remove was called twice (once for each example file)
        assert mock_remove.call_count == 2

        # Check that the correct files were removed
        mock_remove.assert_any_call(os.path.join("/target/.devcontainer", "example-container-env-values.json"))
        mock_remove.assert_any_call(os.path.join("/target/.devcontainer", "example-aws-profile-map.json"))


def test_copy_devcontainer_files_confirm_overwrite():
    """Test that copy_devcontainer_files asks for confirmation when target exists."""
    with patch("os.path.exists", return_value=True), patch("shutil.copytree") as mock_copytree, patch(
        "os.remove"
    ), patch("caylent_devcontainer_cli.commands.setup.confirm_action", return_value=True) as mock_confirm:

        copy_devcontainer_files("/source", "/target", keep_examples=False)

        # Check that confirmation was requested
        mock_confirm.assert_called_once()
        mock_copytree.assert_called_once()


def test_copy_devcontainer_files_cancel_overwrite():
    """Test that copy_devcontainer_files exits when overwrite is cancelled."""
    with patch("os.path.exists", return_value=True), patch("shutil.copytree") as mock_copytree, patch(
        "os.remove"
    ), patch("caylent_devcontainer_cli.commands.setup.confirm_action", return_value=False):

        with pytest.raises(SystemExit):
            copy_devcontainer_files("/source", "/target", keep_examples=False)

        # Check that copytree was not called
        mock_copytree.assert_not_called()
