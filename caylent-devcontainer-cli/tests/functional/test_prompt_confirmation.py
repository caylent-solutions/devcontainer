"""Functional tests for the universal input confirmation pattern (S1.3.1).

End-to-end tests verifying prompt_with_confirmation(), mask_password(),
ssh_fingerprint(), and standardized ask_or_exit() usage across the codebase.
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from caylent_devcontainer_cli.utils.ui import mask_password, prompt_with_confirmation, ssh_fingerprint


class TestPromptWithConfirmationEndToEnd:
    """End-to-end tests for the confirmation loop."""

    def test_text_input_confirmed_on_first_try(self, capsys):
        """Text input confirmed immediately returns value."""
        mock_text = MagicMock()
        mock_text.ask.return_value = "github.com"
        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(lambda: mock_text)

        assert result == "github.com"
        captured = capsys.readouterr()
        assert "github.com" in captured.err
        assert "You entered" in captured.err

    def test_password_input_masked_in_display(self, capsys):
        """Password input shows masked value, not raw password."""
        mock_password = MagicMock()
        mock_password.ask.return_value = "ghp_mySecretToken123"
        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(
                lambda: mock_password,
                display_fn=mask_password,
            )

        assert result == "ghp_mySecretToken123"
        captured = capsys.readouterr()
        # Password must NOT appear in output
        assert "ghp_mySecretToken123" not in captured.err
        # Length indicator must appear
        assert "20" in captured.err

    def test_reject_then_accept_flow(self, capsys):
        """User rejects first input, enters new value, accepts."""
        mock_text = MagicMock()
        mock_text.ask.side_effect = ["wrong-value", "correct-value"]
        mock_confirm = MagicMock()
        mock_confirm.ask.side_effect = [False, True]

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(lambda: mock_text)

        assert result == "correct-value"
        captured = capsys.readouterr()
        assert "wrong-value" in captured.err
        assert "correct-value" in captured.err

    def test_select_input_confirmed(self, capsys):
        """Select input displays chosen option and confirms."""
        mock_select = MagicMock()
        mock_select.ask.return_value = "ssh"
        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_with_confirmation(lambda: mock_select)

        assert result == "ssh"
        captured = capsys.readouterr()
        assert "ssh" in captured.err

    def test_cancel_at_input_exits_cleanly(self, capsys):
        """Ctrl+C at input prompt exits with code 0."""
        mock_text = MagicMock()
        mock_text.ask.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            prompt_with_confirmation(lambda: mock_text)

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "cancelled" in captured.err.lower()


class TestSshFingerprintEndToEnd:
    """End-to-end tests for SSH fingerprint display."""

    def test_real_key_fingerprint(self, tmp_path):
        """Generate a real key and verify fingerprint format."""
        key_file = tmp_path / "test_key"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file), "-N", "", "-q"],
            check=True,
        )

        result = ssh_fingerprint(str(key_file))
        # ed25519 fingerprints contain SHA256 and bit count
        assert "SHA256:" in result
        assert "256" in result

    def test_nonexistent_key_returns_error(self):
        """Non-existent key path returns error, not exception."""
        result = ssh_fingerprint("/tmp/nonexistent_key_12345")
        assert "error" in result.lower() or "no such file" in result.lower()


class TestMaskPasswordEndToEnd:
    """End-to-end tests for password masking."""

    def test_various_passwords_all_masked(self):
        """Multiple passwords of different lengths are all properly masked."""
        passwords = [
            "short-pwd",
            "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefg",
            "x" * 100,
        ]
        for pwd in passwords:
            result = mask_password(pwd)
            assert pwd not in result
            assert str(len(pwd)) in result

    def test_single_char_password_length_shown(self):
        """Single character password still shows correct length."""
        result = mask_password("z")
        assert "1" in result
        assert "******" in result


class TestAskOrExitStandardization:
    """Verify all questionary calls use ask_or_exit consistently."""

    def test_template_validate_uses_ask_or_exit(self):
        """template.py validation functions use ask_or_exit, not .ask()."""
        import inspect

        from caylent_devcontainer_cli.utils import template

        # Check that none of the validation functions call .ask() directly
        for func_name in [
            "_validate_base_key_completeness",
            "_validate_known_key_values",
            "_validate_git_provider_url",
            "_validate_host_proxy_url",
            "_validate_auth_consistency",
        ]:
            func = getattr(template, func_name)
            source = inspect.getsource(func)
            # Should use ask_or_exit, not .ask()
            assert ".ask()" not in source, f"{func_name} still uses .ask() directly"

    def test_code_command_uses_ask_or_exit(self):
        """code.py validation prompt functions use ask_or_exit, not .ask()."""
        import inspect

        from caylent_devcontainer_cli.commands import code

        # Check _handle_missing_metadata (replaced prompt_upgrade_or_continue)
        source = inspect.getsource(code._handle_missing_metadata)
        assert ".ask()" not in source
        assert "ask_or_exit" in source

        # Check _handle_missing_variables (Step 5 prompt)
        source = inspect.getsource(code._handle_missing_variables)
        assert ".ask()" not in source
        assert "ask_or_exit" in source

    def test_template_command_uses_ask_or_exit(self):
        """commands/template.py load_template uses ask_or_exit, not .ask()."""
        import inspect

        from caylent_devcontainer_cli.commands import template

        source = inspect.getsource(template.load_template)
        assert ".ask()" not in source
        assert "ask_or_exit" in source

    def test_setup_interactive_aws_profile_uses_ask_or_exit(self):
        """setup_interactive.py AWS profile prompts use ask_or_exit."""
        import inspect

        from caylent_devcontainer_cli.commands import setup_interactive

        source = inspect.getsource(setup_interactive.prompt_aws_profile_map)
        assert ".ask()" not in source
        assert "ask_or_exit" in source
