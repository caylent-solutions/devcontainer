#!/usr/bin/env python3
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from caylent_devcontainer_cli.utils.ui import COLORS, confirm_action, log


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


def test_confirm_action_yes(capsys):
    with patch("builtins.input", return_value="y"):
        result = confirm_action("Test prompt")
        assert result is True

        captured = capsys.readouterr()
        assert "Test prompt" in captured.out


def test_confirm_action_no(capsys):
    with patch("builtins.input", return_value="n"):
        result = confirm_action("Test prompt")
        assert result is False

        captured = capsys.readouterr()
        assert "Test prompt" in captured.out
        assert "Operation cancelled" in captured.err
