"""Unit tests for UI utility functions (S1.1.3): ask_or_exit, exit_cancelled, exit_with_error."""

from unittest.mock import MagicMock, patch

import pytest


class TestExitWithError:
    """Tests for exit_with_error()."""

    def test_logs_error_and_exits(self, capsys):
        """Test that exit_with_error logs at ERR level and exits with code 1."""
        from caylent_devcontainer_cli.utils.ui import exit_with_error

        with pytest.raises(SystemExit) as exc_info:
            exit_with_error("something went wrong")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "[ERR]" in captured.err
        assert "something went wrong" in captured.err

    def test_exits_with_code_1(self):
        """Test that exit_with_error always exits with code 1."""
        from caylent_devcontainer_cli.utils.ui import exit_with_error

        with pytest.raises(SystemExit) as exc_info:
            exit_with_error("error")

        assert exc_info.value.code == 1

    def test_logs_custom_message(self, capsys):
        """Test that exit_with_error logs the provided message."""
        from caylent_devcontainer_cli.utils.ui import exit_with_error

        with pytest.raises(SystemExit):
            exit_with_error("Custom error: file not found")

        captured = capsys.readouterr()
        assert "Custom error: file not found" in captured.err


class TestExitCancelled:
    """Tests for exit_cancelled()."""

    def test_default_message(self, capsys):
        """Test that exit_cancelled uses default message when none provided."""
        from caylent_devcontainer_cli.utils.ui import exit_cancelled

        with pytest.raises(SystemExit) as exc_info:
            exit_cancelled()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Operation cancelled by user" in captured.err

    def test_custom_message(self, capsys):
        """Test that exit_cancelled uses a custom message when provided."""
        from caylent_devcontainer_cli.utils.ui import exit_cancelled

        with pytest.raises(SystemExit) as exc_info:
            exit_cancelled("Setup cancelled by user.")

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Setup cancelled by user." in captured.err

    def test_exits_with_code_0(self):
        """Test that exit_cancelled always exits with code 0."""
        from caylent_devcontainer_cli.utils.ui import exit_cancelled

        with pytest.raises(SystemExit) as exc_info:
            exit_cancelled()

        assert exc_info.value.code == 0

    def test_logs_at_info_level(self, capsys):
        """Test that exit_cancelled logs at INFO level."""
        from caylent_devcontainer_cli.utils.ui import exit_cancelled

        with pytest.raises(SystemExit):
            exit_cancelled()

        captured = capsys.readouterr()
        assert "[INFO]" in captured.err


class TestAskOrExit:
    """Tests for ask_or_exit()."""

    def test_returns_value_on_success(self):
        """Test that ask_or_exit returns the answer when .ask() returns a value."""
        from caylent_devcontainer_cli.utils.ui import ask_or_exit

        mock_question = MagicMock()
        mock_question.ask.return_value = "user_answer"

        result = ask_or_exit(mock_question)
        assert result == "user_answer"
        mock_question.ask.assert_called_once()

    def test_exits_on_none(self):
        """Test that ask_or_exit calls exit_cancelled when .ask() returns None."""
        from caylent_devcontainer_cli.utils.ui import ask_or_exit

        mock_question = MagicMock()
        mock_question.ask.return_value = None

        with pytest.raises(SystemExit) as exc_info:
            ask_or_exit(mock_question)

        assert exc_info.value.code == 0

    def test_exits_on_keyboard_interrupt(self):
        """Test that ask_or_exit calls exit_cancelled on KeyboardInterrupt."""
        from caylent_devcontainer_cli.utils.ui import ask_or_exit

        mock_question = MagicMock()
        mock_question.ask.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            ask_or_exit(mock_question)

        assert exc_info.value.code == 0

    def test_returns_false_value(self):
        """Test that ask_or_exit returns False (not treated as None)."""
        from caylent_devcontainer_cli.utils.ui import ask_or_exit

        mock_question = MagicMock()
        mock_question.ask.return_value = False

        result = ask_or_exit(mock_question)
        assert result is False

    def test_returns_empty_string(self):
        """Test that ask_or_exit returns empty string (not treated as None)."""
        from caylent_devcontainer_cli.utils.ui import ask_or_exit

        mock_question = MagicMock()
        mock_question.ask.return_value = ""

        result = ask_or_exit(mock_question)
        assert result == ""

    def test_custom_cancel_message(self, capsys):
        """Test that ask_or_exit uses default cancel message on None."""
        from caylent_devcontainer_cli.utils.ui import ask_or_exit

        mock_question = MagicMock()
        mock_question.ask.return_value = None

        with pytest.raises(SystemExit):
            ask_or_exit(mock_question)

        captured = capsys.readouterr()
        assert "Operation cancelled by user" in captured.err


class TestAutoYesRemoved:
    """Tests verifying AUTO_YES and set_auto_yes are removed."""

    def test_auto_yes_not_in_module(self):
        """Test that AUTO_YES global is no longer in utils/ui.py."""
        import caylent_devcontainer_cli.utils.ui as ui_module

        assert not hasattr(ui_module, "AUTO_YES")

    def test_set_auto_yes_not_in_module(self):
        """Test that set_auto_yes function is no longer in utils/ui.py."""
        import caylent_devcontainer_cli.utils.ui as ui_module

        assert not hasattr(ui_module, "set_auto_yes")


class TestConfirmActionWithoutAutoYes:
    """Tests for confirm_action after AUTO_YES removal."""

    def test_confirm_action_yes(self, capsys):
        """Test confirm_action returns True when user enters 'y'."""
        from caylent_devcontainer_cli.utils.ui import confirm_action

        with patch("builtins.input", return_value="y"):
            result = confirm_action("Test prompt")
            assert result is True

    def test_confirm_action_no(self, capsys):
        """Test confirm_action returns False when user enters 'n'."""
        from caylent_devcontainer_cli.utils.ui import confirm_action

        with patch("builtins.input", return_value="n"):
            result = confirm_action("Test prompt")
            assert result is False

    def test_confirm_action_always_prompts(self):
        """Test confirm_action always prompts, never auto-confirms."""
        from caylent_devcontainer_cli.utils.ui import confirm_action

        # Even if someone tried to set AUTO_YES somehow, it should not exist
        with patch("builtins.input", return_value="y") as mock_input:
            confirm_action("Test prompt")
            mock_input.assert_called_once()


class TestConfirmOverwriteRemoved:
    """Tests verifying confirm_overwrite is removed from setup.py."""

    def test_confirm_overwrite_not_in_setup(self):
        """Test that confirm_overwrite function is no longer in setup.py."""
        import caylent_devcontainer_cli.commands.setup as setup_module

        assert not hasattr(setup_module, "confirm_overwrite")
