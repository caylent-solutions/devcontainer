"""Unit tests for the universal input confirmation pattern (S1.3.1).

Tests cover:
- prompt_with_confirmation() — reusable prompt-and-confirm loop
- mask_password() — password masking display
- ssh_fingerprint() — SSH key fingerprint display
- All input types: text, password, select, multi-line, file path
"""

from unittest.mock import MagicMock, patch

import pytest

from caylent_devcontainer_cli.utils.ui import mask_password, prompt_with_confirmation, ssh_fingerprint

# =============================================================================
# mask_password()
# =============================================================================


class TestMaskPassword:
    """Tests for mask_password() display helper."""

    def test_masks_short_password(self):
        """Short password is fully masked with length indicator."""
        result = mask_password("abc")
        assert "abc" not in result
        assert "3" in result

    def test_masks_long_password(self):
        """Long password is masked with length indicator."""
        result = mask_password("my-super-secret-token-12345")
        assert "my-super-secret-token-12345" not in result
        assert "27" in result

    def test_masks_empty_string(self):
        """Empty string returns appropriate message."""
        result = mask_password("")
        assert "0" in result or "empty" in result.lower()

    def test_never_reveals_password_content(self):
        """The original password content must never appear in the output."""
        secret = "ghp_ABCDEFghijklmn1234567890"
        result = mask_password(secret)
        assert secret not in result
        # First 4 and last 4 chars must not appear
        assert secret[:4] not in result
        assert secret[-4:] not in result


# =============================================================================
# ssh_fingerprint()
# =============================================================================


class TestSshFingerprint:
    """Tests for ssh_fingerprint() display helper."""

    def test_returns_fingerprint_for_valid_key(self, tmp_path):
        """Valid SSH key returns a fingerprint string."""
        # Create a real SSH key for testing
        key_file = tmp_path / "test_key"
        import subprocess

        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file), "-N", "", "-q"],
            check=True,
        )

        result = ssh_fingerprint(str(key_file))
        assert "SHA256:" in result or "MD5:" in result

    def test_returns_error_for_nonexistent_file(self):
        """Non-existent file returns an error message."""
        result = ssh_fingerprint("/nonexistent/path/key")
        assert "error" in result.lower() or "not found" in result.lower()

    def test_returns_error_for_invalid_key(self, tmp_path):
        """Invalid key file returns an error message."""
        bad_key = tmp_path / "bad_key"
        bad_key.write_text("this is not a valid key")

        result = ssh_fingerprint(str(bad_key))
        assert "error" in result.lower() or "invalid" in result.lower()


# =============================================================================
# prompt_with_confirmation() — basic behavior
# =============================================================================


class TestPromptWithConfirmation:
    """Tests for prompt_with_confirmation() reusable pattern."""

    def test_returns_answer_when_confirmed(self):
        """User enters value and confirms — value is returned."""
        mock_text = MagicMock()
        mock_text.ask.return_value = "my-value"
        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(lambda: mock_text)

        assert result == "my-value"

    def test_reprompts_when_not_confirmed(self):
        """User enters value, says no, then re-enters and confirms."""
        mock_text = MagicMock()
        mock_text.ask.side_effect = ["first-value", "second-value"]

        mock_confirm = MagicMock()
        mock_confirm.ask.side_effect = [False, True]

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(lambda: mock_text)

        assert result == "second-value"
        assert mock_text.ask.call_count == 2

    def test_multiple_rejections_before_confirm(self):
        """User rejects multiple times before confirming."""
        mock_text = MagicMock()
        mock_text.ask.side_effect = ["v1", "v2", "v3"]

        mock_confirm = MagicMock()
        mock_confirm.ask.side_effect = [False, False, True]

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(lambda: mock_text)

        assert result == "v3"
        assert mock_text.ask.call_count == 3

    def test_exits_on_cancel_during_input(self):
        """User cancels during input prompt — exits cleanly."""
        mock_text = MagicMock()
        mock_text.ask.return_value = None

        with pytest.raises(SystemExit) as exc_info:
            prompt_with_confirmation(lambda: mock_text)

        assert exc_info.value.code == 0

    def test_exits_on_cancel_during_confirmation(self):
        """User cancels during confirmation prompt — exits cleanly."""
        mock_text = MagicMock()
        mock_text.ask.return_value = "my-value"

        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = None

        with patch("questionary.confirm", return_value=mock_confirm):
            with pytest.raises(SystemExit) as exc_info:
                prompt_with_confirmation(lambda: mock_text)

        assert exc_info.value.code == 0

    def test_exits_on_keyboard_interrupt(self):
        """Ctrl+C during input exits cleanly."""
        mock_text = MagicMock()
        mock_text.ask.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            prompt_with_confirmation(lambda: mock_text)

        assert exc_info.value.code == 0


# =============================================================================
# prompt_with_confirmation() — display functions
# =============================================================================


class TestPromptWithConfirmationDisplay:
    """Tests for display_fn parameter behavior."""

    def test_custom_display_fn_used(self, capsys):
        """Custom display_fn formats the value for display."""
        mock_text = MagicMock()
        mock_text.ask.return_value = "secret123"

        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(
                lambda: mock_text,
                display_fn=lambda v: f"MASKED({len(v)} chars)",
            )

        assert result == "secret123"
        captured = capsys.readouterr()
        assert "MASKED(9 chars)" in captured.err

    def test_default_display_shows_raw_value(self, capsys):
        """Without display_fn, the raw value is shown."""
        mock_text = MagicMock()
        mock_text.ask.return_value = "hello-world"

        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(lambda: mock_text)

        assert result == "hello-world"
        captured = capsys.readouterr()
        assert "hello-world" in captured.err

    def test_password_display_fn_masks_value(self, capsys):
        """Using mask_password as display_fn hides the password."""
        mock_text = MagicMock()
        mock_text.ask.return_value = "ghp_secret_token"

        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(
                lambda: mock_text,
                display_fn=mask_password,
            )

        assert result == "ghp_secret_token"
        captured = capsys.readouterr()
        assert "ghp_secret_token" not in captured.err

    def test_display_fn_called_on_each_attempt(self, capsys):
        """display_fn is called every time the user enters a value."""
        mock_text = MagicMock()
        mock_text.ask.side_effect = ["first", "second"]

        mock_confirm = MagicMock()
        mock_confirm.ask.side_effect = [False, True]

        display_calls = []

        def tracking_display(v):
            display_calls.append(v)
            return f"[{v}]"

        with patch("questionary.confirm", return_value=mock_confirm):
            prompt_with_confirmation(lambda: mock_text, display_fn=tracking_display)

        assert display_calls == ["first", "second"]


# =============================================================================
# prompt_with_confirmation() — falsy values
# =============================================================================


class TestPromptWithConfirmationFalsyValues:
    """Tests that falsy values are handled correctly (not treated as cancel)."""

    def test_empty_string_returned_when_confirmed(self):
        """Empty string is a valid value when confirmed."""
        mock_text = MagicMock()
        mock_text.ask.return_value = ""

        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(lambda: mock_text)

        assert result == ""

    def test_false_returned_when_confirmed(self):
        """Boolean False is a valid value when confirmed."""
        mock_question = MagicMock()
        mock_question.ask.return_value = False

        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(lambda: mock_question)

        assert result is False
