#!/usr/bin/env python3
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.utils.ui import (
    AUTO_YES,
    COLORS,
    confirm_action,
    log,
    set_auto_yes,
    show_banner,
)


def test_colors():
    assert "RED" in COLORS
    assert "GREEN" in COLORS
    assert "YELLOW" in COLORS
    assert "BLUE" in COLORS
    assert "PURPLE" in COLORS
    assert "CYAN" in COLORS
    assert "RESET" in COLORS


def test_log_info(capsys):
    log("INFO", "Test message")
    captured = capsys.readouterr()
    assert "[INFO]" in captured.err
    assert "Test message" in captured.err


def test_log_ok(capsys):
    log("OK", "Test message")
    captured = capsys.readouterr()
    assert "[OK]" in captured.err
    assert "Test message" in captured.err


def test_log_warn(capsys):
    log("WARN", "Test message")
    captured = capsys.readouterr()
    assert "[WARN]" in captured.err
    assert "Test message" in captured.err


def test_log_err(capsys):
    log("ERR", "Test message")
    captured = capsys.readouterr()
    assert "[ERR]" in captured.err
    assert "Test message" in captured.err


def test_log_unknown(capsys):
    log("UNKNOWN", "Test message")
    captured = capsys.readouterr()
    assert "[UNKNOWN]" in captured.err
    assert "Test message" in captured.err


def test_set_auto_yes():
    # We need to use a different approach since AUTO_YES is a module-level variable
    from caylent_devcontainer_cli.utils.ui import AUTO_YES as current_auto_yes
    
    original = current_auto_yes
    try:
        set_auto_yes(True)
        from caylent_devcontainer_cli.utils.ui import AUTO_YES as new_auto_yes
        assert new_auto_yes is True
        
        set_auto_yes(False)
        from caylent_devcontainer_cli.utils.ui import AUTO_YES as new_auto_yes2
        assert new_auto_yes2 is False
    finally:
        # Restore original value
        set_auto_yes(original)


def test_show_banner(capsys):
    show_banner()
    captured = capsys.readouterr()
    assert "Caylent Devcontainer CLI" in captured.out


def test_confirm_action_yes(capsys):
    # Save original value
    from caylent_devcontainer_cli.utils.ui import AUTO_YES
    original = AUTO_YES
    
    try:
        # Set AUTO_YES to False for this test
        set_auto_yes(False)
        
        with patch("builtins.input", return_value="y"):
            result = confirm_action("Test prompt")
            assert result is True
            
            captured = capsys.readouterr()
            assert "Test prompt" in captured.out
    finally:
        # Restore original value
        set_auto_yes(original)


def test_confirm_action_no(capsys):
    # Save original value
    from caylent_devcontainer_cli.utils.ui import AUTO_YES
    original = AUTO_YES
    
    try:
        # Set AUTO_YES to False for this test
        set_auto_yes(False)
        
        with patch("builtins.input", return_value="n"):
            result = confirm_action("Test prompt")
            assert result is False
            
            captured = capsys.readouterr()
            assert "Test prompt" in captured.out
            assert "Operation cancelled" in captured.err
    finally:
        # Restore original value
        set_auto_yes(original)


def test_confirm_action_auto_yes(capsys):
    original = AUTO_YES
    try:
        set_auto_yes(True)
        result = confirm_action("Test prompt")
        assert result is True
        captured = capsys.readouterr()
        assert "Test prompt" in captured.out
        assert "Automatically confirmed" in captured.out
    finally:
        # Restore original value
        set_auto_yes(original)