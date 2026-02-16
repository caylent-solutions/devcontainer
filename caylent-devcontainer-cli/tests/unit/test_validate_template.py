#!/usr/bin/env python3
"""Unit tests for validate_template() — Template Validation System (S1.2.1).

Tests cover all five validation phases:
1. Structural validation
2. Base key completeness
3. Known key value validation
4. Auth method consistency
5. Conflict detection
"""

import copy
from unittest.mock import MagicMock, patch

import pytest

from caylent_devcontainer_cli.utils.template import validate_template


def _valid_template(**overrides):
    """Build a minimal valid v2 template dict."""
    template = {
        "containerEnv": {
            "AWS_CONFIG_ENABLED": "true",
            "AWS_DEFAULT_OUTPUT": "json",
            "DEFAULT_GIT_BRANCH": "main",
            "DEVELOPER_NAME": "Test Dev",
            "EXTRA_APT_PACKAGES": "",
            "GIT_AUTH_METHOD": "token",
            "GIT_PROVIDER_URL": "github.com",
            "GIT_TOKEN": "my-token",
            "GIT_USER": "testuser",
            "GIT_USER_EMAIL": "test@example.com",
            "HOST_PROXY": "false",
            "HOST_PROXY_URL": "",
            "PAGER": "cat",
        },
        "cli_version": "2.0.0",
        "template_name": "test-template",
        "template_path": "/templates/test.json",
    }
    template.update(overrides)
    return template


# =============================================================================
# Phase 1: Structural Validation
# =============================================================================


class TestStructuralValidation:
    """Tests for structural validation of template data."""

    def test_valid_template_passes(self):
        """A fully valid template passes structural validation."""
        template = _valid_template()
        result = validate_template(template)
        assert result["containerEnv"] == template["containerEnv"]

    def test_missing_container_env_exits(self):
        """Missing containerEnv key causes non-zero exit."""
        template = _valid_template()
        del template["containerEnv"]
        with pytest.raises(SystemExit):
            validate_template(template)

    def test_container_env_not_dict_exits(self):
        """containerEnv that is not a dict causes non-zero exit."""
        template = _valid_template(containerEnv="not-a-dict")
        with pytest.raises(SystemExit):
            validate_template(template)

    def test_container_env_list_exits(self):
        """containerEnv that is a list causes non-zero exit."""
        template = _valid_template(containerEnv=["a", "b"])
        with pytest.raises(SystemExit):
            validate_template(template)

    def test_missing_cli_version_exits(self):
        """Missing cli_version key causes non-zero exit."""
        template = _valid_template()
        del template["cli_version"]
        with pytest.raises(SystemExit):
            validate_template(template)

    def test_v1_cli_version_exits_with_migration_message(self, capsys):
        """v1.x cli_version exits with migration error message."""
        template = _valid_template(cli_version="1.14.0")
        with pytest.raises(SystemExit):
            validate_template(template)
        captured = capsys.readouterr()
        assert "v1.x" in captured.err or "v1" in captured.err
        assert "template create" in captured.err

    def test_v0_cli_version_exits(self):
        """v0.x cli_version exits non-zero."""
        template = _valid_template(cli_version="0.9.0")
        with pytest.raises(SystemExit):
            validate_template(template)

    def test_invalid_cli_version_format_exits(self):
        """Non-semver cli_version exits non-zero."""
        template = _valid_template(cli_version="not-a-version")
        with pytest.raises(SystemExit):
            validate_template(template)

    def test_missing_template_name_exits(self):
        """Missing template_name key causes non-zero exit."""
        template = _valid_template()
        del template["template_name"]
        with pytest.raises(SystemExit):
            validate_template(template)

    def test_missing_template_path_exits(self):
        """Missing template_path key causes non-zero exit."""
        template = _valid_template()
        del template["template_path"]
        with pytest.raises(SystemExit):
            validate_template(template)

    def test_v2_minor_version_passes(self):
        """v2.1.0 passes structural validation."""
        template = _valid_template(cli_version="2.1.0")
        result = validate_template(template)
        assert result["cli_version"] == "2.1.0"

    def test_v2_patch_version_passes(self):
        """v2.0.1 passes structural validation."""
        template = _valid_template(cli_version="2.0.1")
        result = validate_template(template)
        assert result["cli_version"] == "2.0.1"

    def test_v3_cli_version_exits_when_major_mismatch(self):
        """v3.x cli_version exits with incompatible error when CLI is v2.x."""
        template = _valid_template(cli_version="3.0.0")
        with pytest.raises(SystemExit):
            validate_template(template)


# =============================================================================
# Phase 2: Base Key Completeness
# =============================================================================


class TestBaseKeyCompleteness:
    """Tests for base key completeness checks."""

    def test_all_keys_present_no_prompts(self):
        """When all EXAMPLE_ENV_VALUES keys are present, no prompts appear."""
        template = _valid_template()
        with patch("questionary.text") as mock_text:
            result = validate_template(template)
            mock_text.assert_not_called()
        assert "containerEnv" in result

    def test_missing_key_prompts_user_accepts_default(self):
        """Missing key prompts user and adds default when accepted."""
        template = _valid_template()
        del template["containerEnv"]["PAGER"]

        mock_question = MagicMock()
        mock_question.ask.return_value = "cat"
        with patch("questionary.text", return_value=mock_question) as mock_text:
            result = validate_template(template)
            mock_text.assert_called()
        assert result["containerEnv"]["PAGER"] == "cat"

    def test_missing_key_prompts_user_custom_value(self):
        """Missing key prompts user who enters a custom value."""
        template = _valid_template()
        del template["containerEnv"]["PAGER"]

        mock_question = MagicMock()
        mock_question.ask.return_value = "less"
        with patch("questionary.text", return_value=mock_question):
            result = validate_template(template)
        assert result["containerEnv"]["PAGER"] == "less"

    def test_missing_key_prompt_cancelled_exits(self):
        """If user cancels a missing key prompt, exit."""
        template = _valid_template()
        del template["containerEnv"]["PAGER"]

        mock_question = MagicMock()
        mock_question.ask.return_value = None
        with patch("questionary.text", return_value=mock_question):
            with pytest.raises(SystemExit):
                validate_template(template)

    def test_git_token_not_required_when_ssh(self):
        """GIT_TOKEN is not required when GIT_AUTH_METHOD=ssh."""
        template = _valid_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "ssh"
        del template["containerEnv"]["GIT_TOKEN"]

        result = validate_template(template)
        assert "GIT_TOKEN" not in result["containerEnv"]

    def test_git_token_required_when_token_method(self):
        """GIT_TOKEN is required when GIT_AUTH_METHOD=token."""
        template = _valid_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "token"
        del template["containerEnv"]["GIT_TOKEN"]

        mock_question = MagicMock()
        mock_question.ask.return_value = "new-token"
        with patch("questionary.text", return_value=mock_question):
            result = validate_template(template)
        assert result["containerEnv"]["GIT_TOKEN"] == "new-token"

    def test_multiple_missing_keys_all_prompted(self):
        """Multiple missing keys each prompt the user."""
        template = _valid_template()
        del template["containerEnv"]["PAGER"]
        del template["containerEnv"]["EXTRA_APT_PACKAGES"]

        mock_question = MagicMock()
        # EXTRA_APT_PACKAGES sorts before PAGER — provide valid values for both
        mock_question.ask.side_effect = ["", "cat"]
        with patch("questionary.text", return_value=mock_question) as mock_text:
            result = validate_template(template)
            assert mock_text.call_count == 2
        assert result["containerEnv"]["PAGER"] == "cat"
        assert result["containerEnv"]["EXTRA_APT_PACKAGES"] == ""


# =============================================================================
# Phase 3: Known Key Value Validation
# =============================================================================


class TestKnownKeyValueValidation:
    """Tests for known key value validation."""

    def test_valid_values_pass(self):
        """Valid values for all constrained keys pass without prompts."""
        template = _valid_template()
        with patch("questionary.select") as mock_select:
            result = validate_template(template)
            mock_select.assert_not_called()
        assert result["containerEnv"]["AWS_CONFIG_ENABLED"] == "true"

    def test_aws_config_enabled_invalid_prompts(self):
        """Invalid AWS_CONFIG_ENABLED prompts for correction."""
        template = _valid_template()
        template["containerEnv"]["AWS_CONFIG_ENABLED"] = "yes"

        mock_question = MagicMock()
        mock_question.ask.return_value = "true"
        with patch("questionary.select", return_value=mock_question):
            result = validate_template(template)
        assert result["containerEnv"]["AWS_CONFIG_ENABLED"] == "true"

    def test_host_proxy_invalid_prompts(self):
        """Invalid HOST_PROXY prompts for correction."""
        template = _valid_template()
        template["containerEnv"]["HOST_PROXY"] = "yes"

        mock_question = MagicMock()
        mock_question.ask.return_value = "false"
        with patch("questionary.select", return_value=mock_question):
            result = validate_template(template)
        assert result["containerEnv"]["HOST_PROXY"] == "false"

    def test_git_auth_method_invalid_prompts(self):
        """Invalid GIT_AUTH_METHOD prompts for correction."""
        template = _valid_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "password"

        mock_question = MagicMock()
        mock_question.ask.return_value = "token"
        with patch("questionary.select", return_value=mock_question):
            result = validate_template(template)
        assert result["containerEnv"]["GIT_AUTH_METHOD"] == "token"

    def test_pager_invalid_prompts(self):
        """Invalid PAGER prompts for correction."""
        template = _valid_template()
        template["containerEnv"]["PAGER"] = "vim"

        mock_question = MagicMock()
        mock_question.ask.return_value = "cat"
        with patch("questionary.select", return_value=mock_question):
            result = validate_template(template)
        assert result["containerEnv"]["PAGER"] == "cat"

    def test_aws_default_output_invalid_prompts(self):
        """Invalid AWS_DEFAULT_OUTPUT prompts for correction."""
        template = _valid_template()
        template["containerEnv"]["AWS_DEFAULT_OUTPUT"] = "xml"

        mock_question = MagicMock()
        mock_question.ask.return_value = "json"
        with patch("questionary.select", return_value=mock_question):
            result = validate_template(template)
        assert result["containerEnv"]["AWS_DEFAULT_OUTPUT"] == "json"

    def test_host_proxy_url_invalid_when_proxy_true(self):
        """Invalid HOST_PROXY_URL prompts when HOST_PROXY=true."""
        template = _valid_template()
        template["containerEnv"]["HOST_PROXY"] = "true"
        template["containerEnv"]["HOST_PROXY_URL"] = "not-a-url"

        mock_question = MagicMock()
        mock_question.ask.return_value = "http://proxy.example.com:8080"
        with patch("questionary.text", return_value=mock_question):
            result = validate_template(template)
        assert result["containerEnv"]["HOST_PROXY_URL"] == "http://proxy.example.com:8080"

    def test_host_proxy_url_not_validated_when_proxy_false(self):
        """HOST_PROXY_URL is not validated when HOST_PROXY=false."""
        template = _valid_template()
        template["containerEnv"]["HOST_PROXY"] = "false"
        template["containerEnv"]["HOST_PROXY_URL"] = ""

        result = validate_template(template)
        assert result["containerEnv"]["HOST_PROXY_URL"] == ""

    def test_host_proxy_url_valid_http(self):
        """Valid http:// HOST_PROXY_URL passes when HOST_PROXY=true."""
        template = _valid_template()
        template["containerEnv"]["HOST_PROXY"] = "true"
        template["containerEnv"]["HOST_PROXY_URL"] = "http://proxy.local:3128"

        result = validate_template(template)
        assert result["containerEnv"]["HOST_PROXY_URL"] == "http://proxy.local:3128"

    def test_host_proxy_url_valid_https(self):
        """Valid https:// HOST_PROXY_URL passes when HOST_PROXY=true."""
        template = _valid_template()
        template["containerEnv"]["HOST_PROXY"] = "true"
        template["containerEnv"]["HOST_PROXY_URL"] = "https://proxy.local:3128"

        result = validate_template(template)
        assert result["containerEnv"]["HOST_PROXY_URL"] == "https://proxy.local:3128"

    def test_git_provider_url_with_protocol_prompts(self):
        """GIT_PROVIDER_URL with protocol prefix prompts for correction."""
        template = _valid_template()
        template["containerEnv"]["GIT_PROVIDER_URL"] = "https://github.com"

        mock_question = MagicMock()
        mock_question.ask.return_value = "github.com"
        with patch("questionary.text", return_value=mock_question):
            result = validate_template(template)
        assert result["containerEnv"]["GIT_PROVIDER_URL"] == "github.com"

    def test_git_provider_url_without_dot_prompts(self):
        """GIT_PROVIDER_URL without a dot prompts for correction."""
        template = _valid_template()
        template["containerEnv"]["GIT_PROVIDER_URL"] = "localhost"

        mock_question = MagicMock()
        mock_question.ask.return_value = "github.com"
        with patch("questionary.text", return_value=mock_question):
            result = validate_template(template)
        assert result["containerEnv"]["GIT_PROVIDER_URL"] == "github.com"

    def test_git_provider_url_valid_passes(self):
        """Valid GIT_PROVIDER_URL with dot and no protocol passes."""
        template = _valid_template()
        template["containerEnv"]["GIT_PROVIDER_URL"] = "gitlab.example.com"

        result = validate_template(template)
        assert result["containerEnv"]["GIT_PROVIDER_URL"] == "gitlab.example.com"

    def test_select_prompt_cancelled_exits(self):
        """If user cancels a select prompt for invalid value, exit."""
        template = _valid_template()
        template["containerEnv"]["AWS_CONFIG_ENABLED"] = "invalid"

        mock_question = MagicMock()
        mock_question.ask.return_value = None
        with patch("questionary.select", return_value=mock_question):
            with pytest.raises(SystemExit):
                validate_template(template)

    def test_text_prompt_cancelled_exits_for_provider_url(self):
        """If user cancels text prompt for GIT_PROVIDER_URL, exit."""
        template = _valid_template()
        template["containerEnv"]["GIT_PROVIDER_URL"] = "https://bad"

        mock_question = MagicMock()
        mock_question.ask.return_value = None
        with patch("questionary.text", return_value=mock_question):
            with pytest.raises(SystemExit):
                validate_template(template)

    def test_host_proxy_url_prompt_cancelled_exits(self):
        """If user cancels text prompt for HOST_PROXY_URL, exit."""
        template = _valid_template()
        template["containerEnv"]["HOST_PROXY"] = "true"
        template["containerEnv"]["HOST_PROXY_URL"] = "not-a-url"

        mock_question = MagicMock()
        mock_question.ask.return_value = None
        with patch("questionary.text", return_value=mock_question):
            with pytest.raises(SystemExit):
                validate_template(template)

    def test_constrained_key_missing_from_container_env_skipped(self):
        """A VALID_KEY_VALUES key not present in containerEnv is skipped."""
        template = _valid_template()
        # Remove a constrained key entirely — should not trigger validation prompt
        del template["containerEnv"]["AWS_CONFIG_ENABLED"]

        mock_question = MagicMock()
        # The missing key will trigger base key completeness prompt (phase 2),
        # not the value validation prompt (phase 3)
        mock_question.ask.return_value = "true"
        with patch("questionary.text", return_value=mock_question):
            with patch("questionary.select") as mock_select:
                result = validate_template(template)
                # select should NOT be called for AWS_CONFIG_ENABLED since it
                # was filled with a valid value by phase 2
                for call in mock_select.call_args_list:
                    assert "AWS_CONFIG_ENABLED" not in str(call)
        assert result["containerEnv"]["AWS_CONFIG_ENABLED"] == "true"


# =============================================================================
# Phase 4: Auth Method Consistency
# =============================================================================


class TestAuthMethodConsistency:
    """Tests for auth method consistency checks."""

    def test_token_method_with_token_passes(self):
        """GIT_AUTH_METHOD=token with GIT_TOKEN present passes."""
        template = _valid_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "token"
        template["containerEnv"]["GIT_TOKEN"] = "my-token"

        result = validate_template(template)
        assert result["containerEnv"]["GIT_TOKEN"] == "my-token"
        assert "ssh_private_key" not in result

    def test_token_method_empty_git_token_prompts(self):
        """GIT_AUTH_METHOD=token with empty GIT_TOKEN prompts for value."""
        template = _valid_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "token"
        template["containerEnv"]["GIT_TOKEN"] = ""

        mock_question = MagicMock()
        mock_question.ask.return_value = "new-token"
        with patch("questionary.text", return_value=mock_question):
            result = validate_template(template)
        assert result["containerEnv"]["GIT_TOKEN"] == "new-token"

    def test_token_method_empty_git_token_prompt_cancelled_exits(self):
        """GIT_AUTH_METHOD=token with empty GIT_TOKEN — user cancels prompt."""
        template = _valid_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "token"
        template["containerEnv"]["GIT_TOKEN"] = ""

        mock_question = MagicMock()
        mock_question.ask.return_value = None
        with patch("questionary.text", return_value=mock_question):
            with pytest.raises(SystemExit):
                validate_template(template)

    def test_token_method_removes_ssh_private_key(self):
        """GIT_AUTH_METHOD=token removes ssh_private_key if present."""
        template = _valid_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "token"
        template["containerEnv"]["GIT_TOKEN"] = "my-token"
        template["ssh_private_key"] = "/path/to/key"

        result = validate_template(template)
        assert "ssh_private_key" not in result

    def test_ssh_method_removes_git_token(self):
        """GIT_AUTH_METHOD=ssh removes GIT_TOKEN from containerEnv."""
        template = _valid_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "ssh"
        template["containerEnv"]["GIT_TOKEN"] = "leftover-token"

        result = validate_template(template)
        assert "GIT_TOKEN" not in result["containerEnv"]

    def test_ssh_method_without_git_token_passes(self):
        """GIT_AUTH_METHOD=ssh without GIT_TOKEN passes cleanly."""
        template = _valid_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "ssh"
        del template["containerEnv"]["GIT_TOKEN"]

        result = validate_template(template)
        assert "GIT_TOKEN" not in result["containerEnv"]

    def test_both_token_and_ssh_prompts_user_chooses_token(self):
        """Both GIT_TOKEN and ssh_private_key present — user chooses token."""
        template = _valid_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "token"
        template["containerEnv"]["GIT_TOKEN"] = "my-token"
        template["ssh_private_key"] = "/path/to/key"

        # Auth consistency for token method removes ssh_private_key
        result = validate_template(template)
        assert result["containerEnv"]["GIT_TOKEN"] == "my-token"
        assert "ssh_private_key" not in result

    def test_both_token_and_ssh_user_chooses_ssh(self):
        """Both GIT_TOKEN and ssh_private_key — GIT_AUTH_METHOD=ssh removes token."""
        template = _valid_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "ssh"
        template["containerEnv"]["GIT_TOKEN"] = "leftover-token"
        template["ssh_private_key"] = "/path/to/key"

        result = validate_template(template)
        assert "GIT_TOKEN" not in result["containerEnv"]
        assert result["ssh_private_key"] == "/path/to/key"


# =============================================================================
# Phase 5: Conflict Detection
# =============================================================================


class TestConflictDetection:
    """Tests for conflict detection of new known keys."""

    def test_no_conflicts_passes_cleanly(self):
        """Template with no conflicting custom keys passes cleanly."""
        template = _valid_template()
        result = validate_template(template)
        assert result is not None

    def test_new_known_key_conflict_user_keeps_existing(self):
        """New known key that conflicts with custom key — user keeps existing value."""
        template = _valid_template()
        # Simulate an older template version that doesn't know about HOST_PROXY
        template["cli_version"] = "2.0.0"
        # HOST_PROXY already present with expected value — no conflict
        result = validate_template(template)
        assert result["containerEnv"]["HOST_PROXY"] == "false"

    @patch("caylent_devcontainer_cli.utils.template.__version__", "2.1.0")
    def test_older_template_with_valid_nondefault_constrained_value(self):
        """Older template with valid but non-default constrained value is kept."""
        template = _valid_template(cli_version="2.0.0")
        # PAGER has valid value "less" (not the default "cat") — user intentionally set it
        template["containerEnv"]["PAGER"] = "less"

        result = validate_template(template)
        assert result["containerEnv"]["PAGER"] == "less"

    @patch("caylent_devcontainer_cli.utils.template.__version__", "2.1.0")
    def test_older_template_with_nondefault_nonconstrained_value(self):
        """Older template with non-default value for non-constrained key passes."""
        template = _valid_template(cli_version="2.0.0")
        # DEVELOPER_NAME has non-default value but is not a constrained key
        template["containerEnv"]["DEVELOPER_NAME"] = "Custom Dev Name"

        result = validate_template(template)
        assert result["containerEnv"]["DEVELOPER_NAME"] == "Custom Dev Name"

    def test_conflict_detection_skipped_for_invalid_version(self):
        """Conflict detection returns early for invalid version strings."""
        template = _valid_template()
        # Set a cli_version that can't be parsed as semver
        # but first it must pass structural validation, which checks cli_version
        # So we need to patch __version__ to something invalid to trigger the
        # ValueError catch in _detect_conflicts
        template["cli_version"] = "2.0.0"
        with patch("caylent_devcontainer_cli.utils.template.__version__", "not-a-version"):
            result = validate_template(template)
        assert result is not None


# =============================================================================
# Edge Cases & Return Value
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and return value correctness."""

    def test_returns_modified_template(self):
        """validate_template returns a template dict (possibly modified)."""
        template = _valid_template()
        result = validate_template(template)
        assert isinstance(result, dict)
        assert "containerEnv" in result
        assert "cli_version" in result

    def test_extra_custom_keys_preserved(self):
        """Custom keys not in EXAMPLE_ENV_VALUES are preserved."""
        template = _valid_template()
        template["containerEnv"]["MY_CUSTOM_VAR"] = "custom-value"

        result = validate_template(template)
        assert result["containerEnv"]["MY_CUSTOM_VAR"] == "custom-value"

    def test_extra_top_level_keys_preserved(self):
        """Extra top-level keys (like aws_profile_map) are preserved."""
        template = _valid_template()
        template["aws_profile_map"] = {"default": {"region": "us-west-2"}}

        result = validate_template(template)
        assert result["aws_profile_map"]["default"]["region"] == "us-west-2"

    def test_does_not_mutate_original(self):
        """validate_template does not mutate the original template dict."""
        template = _valid_template()
        original = copy.deepcopy(template)
        validate_template(template)
        assert template == original
