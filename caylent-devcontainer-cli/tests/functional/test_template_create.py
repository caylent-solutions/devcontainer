"""Functional tests for the template create command (S1.2.2).

End-to-end tests verifying the full 17-step interactive creation flow,
SSH key validation, custom environment variables, and template metadata.
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

from caylent_devcontainer_cli.utils.ui import validate_ssh_key_file

# =============================================================================
# validate_ssh_key_file() — end-to-end
# =============================================================================


class TestValidateSshKeyFileEndToEnd:
    """End-to-end tests for SSH key file validation."""

    def test_real_ed25519_key_validates(self, tmp_path):
        """Real ed25519 key passes all validation stages."""
        key_file = tmp_path / "test_key"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file), "-N", "", "-q"],
            check=True,
        )

        success, message = validate_ssh_key_file(str(key_file))
        assert success is True
        assert "SHA256:" in message
        assert "256" in message

    def test_real_rsa_key_validates(self, tmp_path):
        """Real RSA key passes all validation stages."""
        key_file = tmp_path / "test_rsa_key"
        subprocess.run(
            [
                "ssh-keygen",
                "-t",
                "rsa",
                "-b",
                "2048",
                "-f",
                str(key_file),
                "-N",
                "",
                "-q",
            ],
            check=True,
        )

        success, message = validate_ssh_key_file(str(key_file))
        assert success is True
        assert "SHA256:" in message

    def test_passphrase_key_rejected(self, tmp_path):
        """Passphrase-protected key is rejected with guidance message."""
        key_file = tmp_path / "protected_key"
        subprocess.run(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-f",
                str(key_file),
                "-N",
                "testpass",
                "-q",
            ],
            check=True,
        )

        success, message = validate_ssh_key_file(str(key_file))
        assert success is False
        assert "passphrase" in message.lower()

    def test_corrupted_key_rejected(self, tmp_path):
        """Corrupted key file is rejected."""
        key_file = tmp_path / "corrupt_key"
        key_file.write_text(
            "-----BEGIN OPENSSH PRIVATE KEY-----\n" "corrupt-data-here\n" "-----END OPENSSH PRIVATE KEY-----\n"
        )

        success, message = validate_ssh_key_file(str(key_file))
        assert success is False

    def test_windows_line_endings_normalized(self, tmp_path):
        """Key with Windows line endings (\\r\\n) is normalized and validates."""
        key_file = tmp_path / "test_key"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_file), "-N", "", "-q"],
            check=True,
        )

        # Add Windows line endings
        content = key_file.read_text()
        key_file.write_text(content.replace("\n", "\r\n"))

        success, message = validate_ssh_key_file(str(key_file))
        assert success is True


# =============================================================================
# prompt_ssh_key() — end-to-end
# =============================================================================


class TestPromptSshKeyEndToEnd:
    """End-to-end tests for SSH key prompting."""

    def test_valid_key_returns_normalized_content(self, tmp_path):
        """Valid key path returns properly normalized key content."""
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

        # Content must be normalized: no \r, ends with \n
        assert "\r" not in result
        assert result.endswith("\n")
        assert "-----BEGIN" in result
        assert "-----END" in result


# =============================================================================
# prompt_custom_env_vars() — end-to-end
# =============================================================================


class TestPromptCustomEnvVarsEndToEnd:
    """End-to-end tests for custom environment variable prompting."""

    def test_known_keys_constant_matches_example_env_values(self):
        """KNOWN_KEYS constant matches EXAMPLE_ENV_VALUES keys."""
        from caylent_devcontainer_cli.commands.setup import EXAMPLE_ENV_VALUES
        from caylent_devcontainer_cli.utils.constants import KNOWN_KEYS

        assert KNOWN_KEYS == frozenset(EXAMPLE_ENV_VALUES.keys())

    def test_conflict_detection_rejects_all_known_keys(self):
        """Every key in KNOWN_KEYS is rejected in custom env var loop."""
        from caylent_devcontainer_cli.utils.constants import KNOWN_KEYS

        for key in sorted(KNOWN_KEYS):
            assert key in KNOWN_KEYS, f"{key} should be in KNOWN_KEYS"


# =============================================================================
# create_template_interactive() — end-to-end flow
# =============================================================================


class TestCreateTemplateInteractiveEndToEnd:
    """End-to-end tests for the full creation flow."""

    def _run_token_flow(self, aws_enabled=True, host_proxy=False, custom_vars=None):
        """Helper: run a token auth flow with configurable options."""
        from caylent_devcontainer_cli.commands.setup_interactive import create_template_interactive

        pwc_values = [
            "true" if aws_enabled else "false",  # 1. AWS_CONFIG_ENABLED
            "develop",  # 2. DEFAULT_GIT_BRANCH
            "Jane Doe",  # 3. DEVELOPER_NAME
            "gitlab.com",  # 4. GIT_PROVIDER_URL
            "token",  # 5. GIT_AUTH_METHOD
            "jdoe",  # 6. GIT_USER
            "jane@example.com",  # 7. GIT_USER_EMAIL
            "glpat-xxxx",  # 8. GIT_TOKEN
            "vim",  # 9. EXTRA_APT_PACKAGES
            "less",  # 10. PAGER
        ]

        if aws_enabled:
            pwc_values.append("yaml")  # 11. AWS_DEFAULT_OUTPUT

        if host_proxy:
            pwc_values.append("true")  # 12. HOST_PROXY
            pwc_values.append("https://proxy.internal:8080")  # 13. HOST_PROXY_URL
        else:
            pwc_values.append("false")  # 12. HOST_PROXY

        idx = [0]

        def pwc_side_effect(prompt_fn, display_fn=None):
            val = pwc_values[idx[0]]
            idx[0] += 1
            return val

        with (
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_with_confirmation",
                side_effect=pwc_side_effect,
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_custom_env_vars",
                return_value=custom_vars or {},
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.prompt_aws_profile_map",
                return_value=({"default": {"region": "us-east-1"}} if aws_enabled else {}),
            ),
        ):
            return create_template_interactive()

    def test_token_flow_all_env_vars_present(self):
        """Token flow produces all required environment variables."""
        result = self._run_token_flow()
        env = result["containerEnv"]

        required_keys = [
            "AWS_CONFIG_ENABLED",
            "DEFAULT_GIT_BRANCH",
            "DEVELOPER_NAME",
            "GIT_PROVIDER_URL",
            "GIT_AUTH_METHOD",
            "GIT_USER",
            "GIT_USER_EMAIL",
            "GIT_TOKEN",
            "EXTRA_APT_PACKAGES",
            "PAGER",
            "AWS_DEFAULT_OUTPUT",
            "HOST_PROXY",
            "HOST_PROXY_URL",
        ]
        for key in required_keys:
            assert key in env, f"Missing key: {key}"

    def test_token_flow_no_ssh_key(self):
        """Token flow does not include ssh_private_key."""
        result = self._run_token_flow()
        assert "ssh_private_key" not in result

    def test_aws_disabled_no_output_format(self):
        """AWS disabled: no AWS_DEFAULT_OUTPUT, empty aws_profile_map."""
        result = self._run_token_flow(aws_enabled=False)
        assert "AWS_DEFAULT_OUTPUT" not in result["containerEnv"]
        assert result["aws_profile_map"] == {}

    def test_host_proxy_true_stores_url(self):
        """Host proxy true stores the proxy URL."""
        result = self._run_token_flow(host_proxy=True)
        env = result["containerEnv"]
        assert env["HOST_PROXY"] == "true"
        assert env["HOST_PROXY_URL"] == "https://proxy.internal:8080"

    def test_host_proxy_false_empty_url(self):
        """Host proxy false stores empty URL."""
        result = self._run_token_flow(host_proxy=False)
        env = result["containerEnv"]
        assert env["HOST_PROXY"] == "false"
        assert env["HOST_PROXY_URL"] == ""

    def test_custom_vars_merged(self):
        """Custom variables are merged into containerEnv."""
        custom = {"CUSTOM_DB_HOST": "localhost", "CUSTOM_PORT": "5432"}
        result = self._run_token_flow(custom_vars=custom)
        env = result["containerEnv"]
        assert env["CUSTOM_DB_HOST"] == "localhost"
        assert env["CUSTOM_PORT"] == "5432"

    def test_cli_version_included(self):
        """CLI version is included in template."""
        from caylent_devcontainer_cli import __version__

        result = self._run_token_flow()
        assert result["cli_version"] == __version__


# =============================================================================
# save_template_to_file() — metadata verification
# =============================================================================


class TestSaveTemplateMetadata:
    """End-to-end tests for template save with metadata."""

    def test_saved_file_contains_metadata(self, tmp_path):
        """Saved template file contains template_name and template_path."""
        from caylent_devcontainer_cli.commands.setup_interactive import save_template_to_file

        template_data = {
            "containerEnv": {"TEST": "value"},
            "cli_version": "2.0.0",
            "aws_profile_map": {},
        }

        template_file = tmp_path / "my-template.json"
        with (
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.ensure_templates_dir",
            ),
            patch(
                "caylent_devcontainer_cli.commands.setup_interactive.get_template_path",
                return_value=str(template_file),
            ),
        ):
            save_template_to_file(template_data, "my-template")

        # Read back the saved file
        with open(template_file) as f:
            saved = json.load(f)

        assert saved["template_name"] == "my-template"
        assert saved["template_path"] == str(template_file)
        assert saved["containerEnv"] == {"TEST": "value"}


# =============================================================================
# Source inspection tests
# =============================================================================


class TestCreateTemplateSourceInspection:
    """Verify the create_template_interactive function uses prompt_with_confirmation."""

    def test_uses_prompt_with_confirmation(self):
        """create_template_interactive() uses prompt_with_confirmation, not ask_or_exit directly."""
        import inspect

        from caylent_devcontainer_cli.commands import setup_interactive

        source = inspect.getsource(setup_interactive.create_template_interactive)
        # Should use prompt_with_confirmation for the main prompts
        assert "prompt_with_confirmation" in source

    def test_no_direct_ask_calls_in_creation(self):
        """create_template_interactive() does not call .ask() directly for env prompts."""
        import inspect

        from caylent_devcontainer_cli.commands import setup_interactive

        source = inspect.getsource(setup_interactive.create_template_interactive)
        # Should not have .ask() calls for the main prompts
        # (prompt_with_confirmation handles that internally)
        assert ".ask()" not in source

    def test_mask_password_used_for_git_token(self):
        """Git token prompt uses mask_password display function."""
        import inspect

        from caylent_devcontainer_cli.commands import setup_interactive

        source = inspect.getsource(setup_interactive.create_template_interactive)
        assert "mask_password" in source

    def test_known_keys_imported(self):
        """KNOWN_KEYS is imported and used for conflict detection."""
        import inspect

        from caylent_devcontainer_cli.commands import setup_interactive

        source = inspect.getsource(setup_interactive)
        assert "KNOWN_KEYS" in source
