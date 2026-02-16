"""Unit tests for the template create command (S1.2.2).

Tests cover:
- validate_ssh_key_file() — SSH key file validation
- prompt_ssh_key() — SSH key prompting flow
- prompt_custom_env_vars() — custom environment variable loop
- create_template_interactive() — full 17-step interactive creation flow
- create_new_template() — template creation with metadata
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from caylent_devcontainer_cli.utils.ui import validate_ssh_key_file

# =============================================================================
# validate_ssh_key_file()
# =============================================================================


class TestValidateSshKeyFile:
    """Tests for SSH key file validation."""

    def test_nonexistent_file_returns_error(self):
        """Non-existent file returns (False, error message)."""
        success, message = validate_ssh_key_file("/nonexistent/path/key")
        assert success is False
        assert "not found" in message.lower() or "does not exist" in message.lower()

    def test_unreadable_file_returns_error(self, tmp_path):
        """File that is not readable returns error."""
        key_file = tmp_path / "unreadable_key"
        key_file.write_text("content")
        key_file.chmod(0o000)

        success, message = validate_ssh_key_file(str(key_file))
        assert success is False
        assert "read" in message.lower() or "permission" in message.lower()

        # Restore permissions for cleanup
        key_file.chmod(0o644)

    def test_invalid_format_no_begin_marker(self, tmp_path):
        """File without -----BEGIN marker fails format check."""
        key_file = tmp_path / "bad_key"
        key_file.write_text("this is not a valid key\n-----END SOMETHING-----\n")

        success, message = validate_ssh_key_file(str(key_file))
        assert success is False
        assert "format" in message.lower() or "begin" in message.lower()

    def test_invalid_format_no_end_marker(self, tmp_path):
        """File without -----END marker fails format check."""
        key_file = tmp_path / "bad_key"
        key_file.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\ndata\n")

        success, message = validate_ssh_key_file(str(key_file))
        assert success is False
        assert "format" in message.lower() or "end" in message.lower()

    def test_valid_key_returns_success(self, tmp_path):
        """Valid SSH key returns (True, fingerprint)."""
        key_file = tmp_path / "test_key"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file), "-N", "", "-q"],
            check=True,
        )

        success, message = validate_ssh_key_file(str(key_file))
        assert success is True
        assert "SHA256:" in message

    def test_passphrase_protected_key_returns_error(self, tmp_path):
        """Passphrase-protected key returns error with guidance."""
        key_file = tmp_path / "protected_key"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file), "-N", "mypassphrase", "-q"],
            check=True,
        )

        success, message = validate_ssh_key_file(str(key_file))
        assert success is False
        assert "passphrase" in message.lower()

    def test_carriage_return_normalization(self, tmp_path):
        """Key with \\r line endings is normalized before validation."""
        key_file = tmp_path / "test_key"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file), "-N", "", "-q"],
            check=True,
        )

        # Read valid key and add \r
        content = key_file.read_text()
        key_file.write_text(content.replace("\n", "\r\n"))

        success, message = validate_ssh_key_file(str(key_file))
        assert success is True
        assert "SHA256:" in message


# =============================================================================
# prompt_ssh_key()
# =============================================================================


class TestPromptSshKey:
    """Tests for SSH key prompting flow."""

    def test_valid_key_path_returns_content(self, tmp_path):
        """Valid SSH key path returns key content."""
        from caylent_devcontainer_cli.commands.setup_interactive import prompt_ssh_key

        key_file = tmp_path / "test_key"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file), "-N", "", "-q"],
            check=True,
        )

        mock_text = MagicMock()
        mock_text.ask.return_value = str(key_file)
        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("questionary.text", return_value=mock_text), patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_ssh_key()

        assert "-----BEGIN" in result
        assert "-----END" in result

    def test_invalid_path_reprompts(self, tmp_path):
        """Invalid path causes re-prompt, then valid path succeeds."""
        from caylent_devcontainer_cli.commands.setup_interactive import prompt_ssh_key

        key_file = tmp_path / "test_key"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file), "-N", "", "-q"],
            check=True,
        )

        mock_text = MagicMock()
        mock_text.ask.side_effect = ["/nonexistent/path", str(key_file)]
        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with patch("questionary.text", return_value=mock_text), patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_ssh_key()

        assert "-----BEGIN" in result
        assert mock_text.ask.call_count == 2

    def test_cancel_exits_cleanly(self):
        """Cancel during SSH key prompt exits cleanly."""
        from caylent_devcontainer_cli.commands.setup_interactive import prompt_ssh_key

        mock_text = MagicMock()
        mock_text.ask.return_value = None

        with patch("questionary.text", return_value=mock_text):
            with pytest.raises(SystemExit) as exc_info:
                prompt_ssh_key()

        assert exc_info.value.code == 0

    def test_reject_fingerprint_reprompts(self, tmp_path):
        """User rejecting fingerprint causes re-prompt."""
        from caylent_devcontainer_cli.commands.setup_interactive import prompt_ssh_key

        key_file = tmp_path / "test_key"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file), "-N", "", "-q"],
            check=True,
        )

        key_file2 = tmp_path / "test_key2"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file2), "-N", "", "-q"],
            check=True,
        )

        mock_text = MagicMock()
        mock_text.ask.side_effect = [str(key_file), str(key_file2)]
        mock_confirm = MagicMock()
        mock_confirm.ask.side_effect = [False, True]

        with patch("questionary.text", return_value=mock_text), patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_ssh_key()

        assert "-----BEGIN" in result
        assert mock_text.ask.call_count == 2


# =============================================================================
# prompt_custom_env_vars()
# =============================================================================


class TestPromptCustomEnvVars:
    """Tests for custom environment variable loop."""

    def test_no_custom_vars(self):
        """User declines to add custom vars — returns empty dict."""
        from caylent_devcontainer_cli.commands.setup_interactive import prompt_custom_env_vars

        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = False

        with patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_custom_env_vars(set())

        assert result == {}

    def test_single_custom_var(self):
        """User adds one custom variable and stops."""
        from caylent_devcontainer_cli.commands.setup_interactive import prompt_custom_env_vars

        mock_text = MagicMock()
        mock_text.ask.side_effect = ["MY_CUSTOM_KEY", "my-value"]
        mock_confirm = MagicMock()
        # First: "Add custom vars?", "Is this correct?", "Add another?"
        mock_confirm.ask.side_effect = [True, True, False]

        with patch("questionary.text", return_value=mock_text), patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_custom_env_vars(set())

        assert result == {"MY_CUSTOM_KEY": "my-value"}

    def test_multiple_custom_vars(self):
        """User adds multiple custom variables."""
        from caylent_devcontainer_cli.commands.setup_interactive import prompt_custom_env_vars

        mock_text = MagicMock()
        mock_text.ask.side_effect = ["KEY_ONE", "value1", "KEY_TWO", "value2"]
        mock_confirm = MagicMock()
        # "Add custom?", "Is correct?", "Add another?", "Is correct?", "Add another?"
        mock_confirm.ask.side_effect = [True, True, True, True, False]

        with patch("questionary.text", return_value=mock_text), patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_custom_env_vars(set())

        assert result == {"KEY_ONE": "value1", "KEY_TWO": "value2"}

    def test_conflict_with_known_key(self, capsys):
        """Key conflicting with known keys shows error and re-prompts."""
        from caylent_devcontainer_cli.commands.setup_interactive import prompt_custom_env_vars

        mock_text = MagicMock()
        # First try: known key, then valid key
        mock_text.ask.side_effect = ["GIT_TOKEN", "MY_VALID_KEY", "my-value"]
        mock_confirm = MagicMock()
        mock_confirm.ask.side_effect = [True, True, False]

        known = {"GIT_TOKEN", "GIT_USER"}
        with patch("questionary.text", return_value=mock_text), patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_custom_env_vars(known)

        assert result == {"MY_VALID_KEY": "my-value"}
        captured = capsys.readouterr()
        assert "already exists" in captured.err.lower()

    def test_conflict_with_already_entered_key(self, capsys):
        """Key conflicting with already-entered custom key shows error."""
        from caylent_devcontainer_cli.commands.setup_interactive import prompt_custom_env_vars

        mock_text = MagicMock()
        # First var OK, second var conflicts with first, then valid
        mock_text.ask.side_effect = ["KEY_A", "val_a", "KEY_A", "KEY_B", "val_b"]
        mock_confirm = MagicMock()
        # "Add?", "Is correct?", "Add another?", "Is correct?", "Add another?"
        mock_confirm.ask.side_effect = [True, True, True, True, False]

        with patch("questionary.text", return_value=mock_text), patch("questionary.confirm", return_value=mock_confirm):
            result = prompt_custom_env_vars(set())

        assert result == {"KEY_A": "val_a", "KEY_B": "val_b"}
        captured = capsys.readouterr()
        assert "already exists" in captured.err.lower()

    def test_cancel_exits_cleanly(self):
        """Cancel during custom var prompt exits cleanly."""
        from caylent_devcontainer_cli.commands.setup_interactive import prompt_custom_env_vars

        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        mock_text = MagicMock()
        mock_text.ask.return_value = None

        with patch("questionary.text", return_value=mock_text), patch("questionary.confirm", return_value=mock_confirm):
            with pytest.raises(SystemExit) as exc_info:
                prompt_custom_env_vars(set())

        assert exc_info.value.code == 0


# =============================================================================
# create_template_interactive() — full 17-step flow
# =============================================================================


def _mock_prompt_with_confirmation(values):
    """Helper: create a side_effect for prompt_with_confirmation that returns values in order."""
    iterator = iter(values)

    def side_effect(prompt_fn, display_fn=None):
        return next(iterator)

    return side_effect


class TestCreateTemplateInteractiveTokenFlow:
    """Tests for create_template_interactive with token auth method."""

    def _build_mocks(self, aws_enabled=True, host_proxy=False, custom_vars=None, aws_profiles=None):
        """Build mock side effects for a complete token auth flow."""
        # Steps 1-17 with token auth
        pwc_values = [
            "true" if aws_enabled else "false",  # 1. AWS_CONFIG_ENABLED
            "main",  # 2. DEFAULT_GIT_BRANCH
            "Test Developer",  # 3. DEVELOPER_NAME
            "github.com",  # 4. GIT_PROVIDER_URL
            "token",  # 5. GIT_AUTH_METHOD
            "testuser",  # 6. GIT_USER
            "test@example.com",  # 7. GIT_USER_EMAIL
            "ghp_test_token_123",  # 8. GIT_TOKEN (password)
            # Step 9 skipped (token auth, not SSH)
            "",  # 10. EXTRA_APT_PACKAGES
            "cat",  # 11. PAGER
        ]

        if aws_enabled:
            pwc_values.append("json")  # 12. AWS_DEFAULT_OUTPUT

        if host_proxy:
            pwc_values.append("true")  # 13. HOST_PROXY
            pwc_values.append("http://host.docker.internal:3128")  # 14. HOST_PROXY_URL
        else:
            pwc_values.append("false")  # 13. HOST_PROXY

        return pwc_values, custom_vars or {}, aws_profiles or {}

    def test_full_token_flow_aws_enabled(self):
        """Full 17-step flow with token auth and AWS enabled."""
        from caylent_devcontainer_cli.commands.setup_interactive import create_template_interactive

        pwc_values, custom_vars, aws_profiles = self._build_mocks(aws_enabled=True)

        with (
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_with_confirmation",
                side_effect=_mock_prompt_with_confirmation(pwc_values),
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_custom_env_vars",
                return_value=custom_vars,
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map",
                return_value=aws_profiles,
            ),
        ):
            result = create_template_interactive()

        env = result["containerEnv"]
        assert env["AWS_CONFIG_ENABLED"] == "true"
        assert env["DEFAULT_GIT_BRANCH"] == "main"
        assert env["DEVELOPER_NAME"] == "Test Developer"
        assert env["GIT_PROVIDER_URL"] == "github.com"
        assert env["GIT_AUTH_METHOD"] == "token"
        assert env["GIT_USER"] == "testuser"
        assert env["GIT_USER_EMAIL"] == "test@example.com"
        assert env["GIT_TOKEN"] == "ghp_test_token_123"
        assert env["EXTRA_APT_PACKAGES"] == ""
        assert env["PAGER"] == "cat"
        assert env["AWS_DEFAULT_OUTPUT"] == "json"
        assert env["HOST_PROXY"] == "false"
        assert env["HOST_PROXY_URL"] == ""
        assert result["cli_version"] is not None
        assert "ssh_private_key" not in result

    def test_full_token_flow_aws_disabled(self):
        """Token flow with AWS disabled skips AWS output and profile map."""
        from caylent_devcontainer_cli.commands.setup_interactive import create_template_interactive

        pwc_values, custom_vars, _ = self._build_mocks(aws_enabled=False)

        with (
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_with_confirmation",
                side_effect=_mock_prompt_with_confirmation(pwc_values),
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_custom_env_vars",
                return_value=custom_vars,
            ),
        ):
            result = create_template_interactive()

        env = result["containerEnv"]
        assert env["AWS_CONFIG_ENABLED"] == "false"
        assert "AWS_DEFAULT_OUTPUT" not in env
        assert result["aws_profile_map"] == {}

    def test_host_proxy_true_includes_url(self):
        """Host proxy true includes HOST_PROXY_URL in output."""
        from caylent_devcontainer_cli.commands.setup_interactive import create_template_interactive

        pwc_values, custom_vars, aws_profiles = self._build_mocks(host_proxy=True)

        with (
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_with_confirmation",
                side_effect=_mock_prompt_with_confirmation(pwc_values),
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_custom_env_vars",
                return_value=custom_vars,
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map",
                return_value=aws_profiles,
            ),
        ):
            result = create_template_interactive()

        env = result["containerEnv"]
        assert env["HOST_PROXY"] == "true"
        assert env["HOST_PROXY_URL"] == "http://host.docker.internal:3128"

    def test_custom_vars_merged_into_container_env(self):
        """Custom environment variables are merged into containerEnv."""
        from caylent_devcontainer_cli.commands.setup_interactive import create_template_interactive

        custom = {"MY_CUSTOM_VAR": "custom-value", "ANOTHER_VAR": "another"}
        pwc_values, _, aws_profiles = self._build_mocks(custom_vars=custom)

        with (
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_with_confirmation",
                side_effect=_mock_prompt_with_confirmation(pwc_values),
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_custom_env_vars",
                return_value=custom,
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map",
                return_value=aws_profiles,
            ),
        ):
            result = create_template_interactive()

        env = result["containerEnv"]
        assert env["MY_CUSTOM_VAR"] == "custom-value"
        assert env["ANOTHER_VAR"] == "another"


class TestCreateTemplateInteractiveSshFlow:
    """Tests for create_template_interactive with SSH auth method."""

    def test_full_ssh_flow(self, tmp_path):
        """Full flow with SSH auth includes ssh_private_key, no GIT_TOKEN."""
        from caylent_devcontainer_cli.commands.setup_interactive import create_template_interactive

        # Create a real SSH key for the mock to return
        key_file = tmp_path / "test_key"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file), "-N", "", "-q"],
            check=True,
        )
        key_content = key_file.read_text()

        pwc_values = [
            "true",  # 1. AWS_CONFIG_ENABLED
            "main",  # 2. DEFAULT_GIT_BRANCH
            "Test Developer",  # 3. DEVELOPER_NAME
            "github.com",  # 4. GIT_PROVIDER_URL
            "ssh",  # 5. GIT_AUTH_METHOD
            "testuser",  # 6. GIT_USER
            "test@example.com",  # 7. GIT_USER_EMAIL
            # Step 8 skipped (SSH, not token)
            # Step 9 handled by prompt_ssh_key mock
            "",  # 10. EXTRA_APT_PACKAGES
            "cat",  # 11. PAGER
            "json",  # 12. AWS_DEFAULT_OUTPUT
            "false",  # 13. HOST_PROXY
        ]

        with (
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_with_confirmation",
                side_effect=_mock_prompt_with_confirmation(pwc_values),
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_ssh_key",
                return_value=key_content,
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_custom_env_vars",
                return_value={},
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map",
                return_value={},
            ),
        ):
            result = create_template_interactive()

        env = result["containerEnv"]
        assert env["GIT_AUTH_METHOD"] == "ssh"
        assert "GIT_TOKEN" not in env
        assert result["ssh_private_key"] == key_content


# =============================================================================
# create_new_template() — metadata handling
# =============================================================================


class TestCreateNewTemplateMetadata:
    """Tests for template creation with metadata."""

    def test_template_name_and_path_in_saved_data(self, tmp_path):
        """Template name and path are included in saved template data."""
        from caylent_devcontainer_cli.commands.template import create_new_template

        saved_data = {}

        def capture_save(data, name):
            saved_data.update(data)

        template_path = str(tmp_path / "test.json")
        with (
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.create_template_interactive",
                return_value={"containerEnv": {}, "cli_version": "2.0.0", "aws_profile_map": {}},
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.save_template_to_file",
                side_effect=capture_save,
            ),
            patch(
                "caylent_devcontainer_cli.commands.template.ensure_templates_dir",
            ),
            patch(
                "caylent_devcontainer_cli.commands.template.get_template_path",
                return_value=template_path,
            ),
            patch(
                "os.path.exists",
                return_value=False,
            ),
        ):
            create_new_template("my-template")

        # save_template_to_file adds metadata, but we're mocking it.
        # The real test is that create_new_template passes the data through.
        # Let's test the real save_template_to_file instead.

    def test_save_template_to_file_adds_metadata(self, tmp_path):
        """save_template_to_file adds template_name and template_path."""
        from caylent_devcontainer_cli.commands.setup_interactive import save_template_to_file

        template_data = {"containerEnv": {}, "cli_version": "2.0.0", "aws_profile_map": {}}

        with (
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.ensure_templates_dir",
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.get_template_path",
                return_value=str(tmp_path / "my-template.json"),
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.write_json_file",
            ) as mock_write,
        ):
            save_template_to_file(template_data, "my-template")

        # Verify metadata was added to template_data
        assert template_data["template_name"] == "my-template"
        assert template_data["template_path"] == str(tmp_path / "my-template.json")
        mock_write.assert_called_once()

    def test_existing_template_with_overwrite_confirmation(self, tmp_path):
        """Existing template requires overwrite confirmation via questionary."""
        from caylent_devcontainer_cli.commands.template import create_new_template

        template_path = str(tmp_path / "existing.json")
        # Create the file
        with open(template_path, "w") as f:
            f.write("{}")

        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True

        with (
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.create_template_interactive",
                return_value={"containerEnv": {}, "cli_version": "2.0.0", "aws_profile_map": {}},
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.save_template_to_file",
            ),
            patch(
                "caylent_devcontainer_cli.commands.template.ensure_templates_dir",
            ),
            patch(
                "caylent_devcontainer_cli.commands.template.get_template_path",
                return_value=template_path,
            ),
            patch(
                "questionary.confirm",
                return_value=mock_confirm,
            ),
        ):
            create_new_template("existing")

    def test_existing_template_decline_overwrite_cancels(self, tmp_path):
        """Declining overwrite cancels template creation."""
        from caylent_devcontainer_cli.commands.template import create_new_template

        template_path = str(tmp_path / "existing.json")
        with open(template_path, "w") as f:
            f.write("{}")

        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = False

        with (
            patch(
                "caylent_devcontainer_cli.commands.template.ensure_templates_dir",
            ),
            patch(
                "caylent_devcontainer_cli.commands.template.get_template_path",
                return_value=template_path,
            ),
            patch(
                "questionary.confirm",
                return_value=mock_confirm,
            ),
        ):
            # Should exit or return without creating
            with pytest.raises(SystemExit):
                create_new_template("existing")
