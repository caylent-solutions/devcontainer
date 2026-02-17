"""Functional tests for UI utility functions (S1.1.3).

Tests verify end-to-end behavior of ask_or_exit, exit_cancelled,
exit_with_error, and confirm_action — including their integration
with the logging system and exit codes.
"""

from unittest.mock import MagicMock, patch

import pytest

from caylent_devcontainer_cli.utils.ui import ask_or_exit, confirm_action, exit_cancelled, exit_with_error


class TestExitWithErrorEndToEnd:
    """Functional tests for exit_with_error end-to-end behavior."""

    def test_exits_with_code_1_and_logs_to_stderr(self, capsys):
        """Test full flow: logs error to stderr and exits with code 1."""
        with pytest.raises(SystemExit) as exc_info:
            exit_with_error("Database connection failed")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "[ERR]" in captured.err
        assert "Database connection failed" in captured.err
        # stdout should be empty — errors go to stderr
        assert captured.out == ""

    def test_called_from_utility_function(self, capsys):
        """Test exit_with_error when called from another utility (fs.py pattern)."""
        from caylent_devcontainer_cli.utils.fs import load_json_config

        with pytest.raises(SystemExit) as exc_info:
            load_json_config("/nonexistent/path/config.json")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "[ERR]" in captured.err


class TestExitCancelledEndToEnd:
    """Functional tests for exit_cancelled end-to-end behavior."""

    def test_exits_with_code_0_and_default_message(self, capsys):
        """Test full flow: logs cancellation to stderr and exits with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            exit_cancelled()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "[INFO]" in captured.err
        assert "Operation cancelled by user" in captured.err

    def test_exits_with_custom_message(self, capsys):
        """Test exit_cancelled with a custom message."""
        with pytest.raises(SystemExit) as exc_info:
            exit_cancelled("Setup cancelled by user.")

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Setup cancelled by user." in captured.err


class TestAskOrExitEndToEnd:
    """Functional tests for ask_or_exit end-to-end behavior."""

    def test_returns_answer_when_user_responds(self):
        """Test full flow: user provides an answer, it is returned."""
        mock_question = MagicMock()
        mock_question.ask.return_value = "my-template"

        result = ask_or_exit(mock_question)
        assert result == "my-template"

    def test_exits_gracefully_on_cancel(self, capsys):
        """Test full flow: user cancels (None), exits with code 0 and message."""
        mock_question = MagicMock()
        mock_question.ask.return_value = None

        with pytest.raises(SystemExit) as exc_info:
            ask_or_exit(mock_question)

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Operation cancelled by user" in captured.err

    def test_exits_gracefully_on_keyboard_interrupt(self, capsys):
        """Test full flow: user presses Ctrl+C, exits with code 0."""
        mock_question = MagicMock()
        mock_question.ask.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            ask_or_exit(mock_question)

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Operation cancelled by user" in captured.err

    def test_returns_falsy_values_without_exiting(self):
        """Test that falsy values (False, '', 0) are returned, not treated as cancel."""
        for falsy_value in [False, "", 0]:
            mock_question = MagicMock()
            mock_question.ask.return_value = falsy_value

            result = ask_or_exit(mock_question)
            assert result == falsy_value


class TestConfirmActionEndToEnd:
    """Functional tests for confirm_action end-to-end behavior."""

    def test_returns_true_on_yes(self):
        """Test full flow: user confirms with 'y', returns True."""
        with patch("builtins.input", return_value="y"):
            result = confirm_action("Overwrite existing file?")
            assert result is True

    def test_returns_false_on_no(self, capsys):
        """Test full flow: user declines with 'n', returns False and logs."""
        with patch("builtins.input", return_value="n"):
            result = confirm_action("Overwrite existing file?")
            assert result is False

        captured = capsys.readouterr()
        assert "[ERR]" in captured.err
        assert "Operation cancelled by user" in captured.err

    def test_returns_false_on_empty_input(self):
        """Test that empty input (just Enter) defaults to No."""
        with patch("builtins.input", return_value=""):
            result = confirm_action("Continue?")
            assert result is False

    def test_displays_warning_prompt(self, capsys):
        """Test that confirm_action displays the message to stdout."""
        with patch("builtins.input", return_value="y"):
            confirm_action("This will delete all data")

        captured = capsys.readouterr()
        assert "This will delete all data" in captured.out


class TestAutoYesRemovedEndToEnd:
    """Functional tests verifying AUTO_YES removal is complete."""

    def test_no_auto_yes_in_ui_module(self):
        """Test that AUTO_YES global no longer exists in ui module."""
        import caylent_devcontainer_cli.utils.ui as ui_module

        assert not hasattr(ui_module, "AUTO_YES")
        assert not hasattr(ui_module, "set_auto_yes")

    def test_confirm_action_cannot_be_bypassed(self):
        """Test that confirm_action always requires user input."""
        with patch("builtins.input", return_value="y") as mock_input:
            confirm_action("Test prompt")
            mock_input.assert_called_once()

    def test_confirm_overwrite_removed_from_setup(self):
        """Test that confirm_overwrite no longer exists in setup module."""
        import caylent_devcontainer_cli.commands.setup as setup_module

        assert not hasattr(setup_module, "confirm_overwrite")
