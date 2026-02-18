#!/usr/bin/env python3
"""Functional tests for validate_template() — Template Validation System (S1.2.1).

End-to-end tests that call validate_template() with real data
to verify the five validation phases work correctly together.
"""

from unittest.mock import MagicMock, patch

import pytest

from caylent_devcontainer_cli.utils.template import validate_template


def _full_template(**overrides):
    """Build a fully valid v2 template for functional testing."""
    template = {
        "containerEnv": {
            "AWS_CONFIG_ENABLED": "true",
            "AWS_DEFAULT_OUTPUT": "json",
            "DEFAULT_GIT_BRANCH": "main",
            "DEVELOPER_NAME": "Functional Test",
            "EXTRA_APT_PACKAGES": "",
            "GIT_AUTH_METHOD": "token",
            "GIT_PROVIDER_URL": "github.com",
            "GIT_TOKEN": "ghp_functional_test_token",
            "GIT_USER": "functest",
            "GIT_USER_EMAIL": "func@example.com",
            "HOST_PROXY": "false",
            "HOST_PROXY_URL": "",
            "PAGER": "cat",
        },
        "cli_version": "2.0.0",
        "template_name": "functional-test",
        "template_path": "/templates/functional.json",
        "aws_profile_map": {},
    }
    template.update(overrides)
    return template


class TestValidTemplatePassesAllPhases:
    """A fully valid template passes all five validation phases."""

    def test_complete_token_template(self):
        """Complete template with token auth passes end-to-end."""
        template = _full_template()
        result = validate_template(template)

        assert result["containerEnv"]["GIT_AUTH_METHOD"] == "token"
        assert result["containerEnv"]["GIT_TOKEN"] == "ghp_functional_test_token"
        assert result["cli_version"] == "2.0.0"
        assert result["template_name"] == "functional-test"
        assert result["aws_profile_map"] == {}

    def test_complete_ssh_template(self):
        """Complete template with SSH auth passes end-to-end."""
        template = _full_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "ssh"
        del template["containerEnv"]["GIT_TOKEN"]

        result = validate_template(template)

        assert result["containerEnv"]["GIT_AUTH_METHOD"] == "ssh"
        assert "GIT_TOKEN" not in result["containerEnv"]

    def test_proxy_enabled_template(self):
        """Template with proxy enabled and valid URL passes."""
        template = _full_template()
        template["containerEnv"]["HOST_PROXY"] = "true"
        template["containerEnv"]["HOST_PROXY_URL"] = "http://proxy.corp.local:8080"

        result = validate_template(template)

        assert result["containerEnv"]["HOST_PROXY"] == "true"
        assert result["containerEnv"]["HOST_PROXY_URL"] == "http://proxy.corp.local:8080"

    def test_custom_keys_preserved(self):
        """Custom user-defined keys survive all validation phases."""
        template = _full_template()
        template["containerEnv"]["MY_CUSTOM_DB_HOST"] = "db.internal.local"
        template["containerEnv"]["FEATURE_FLAG_X"] = "enabled"

        result = validate_template(template)

        assert result["containerEnv"]["MY_CUSTOM_DB_HOST"] == "db.internal.local"
        assert result["containerEnv"]["FEATURE_FLAG_X"] == "enabled"


class TestStructuralRejection:
    """Templates with structural issues are rejected immediately."""

    def test_rejects_v1_template(self):
        """v1.x template is rejected with migration message."""
        template = _full_template(cli_version="1.14.1")

        with pytest.raises(SystemExit) as exc_info:
            validate_template(template)

        assert exc_info.value.code == 1

    def test_rejects_missing_container_env(self):
        """Template without containerEnv is rejected."""
        template = _full_template()
        del template["containerEnv"]

        with pytest.raises(SystemExit):
            validate_template(template)

    def test_rejects_missing_template_name(self):
        """Template without template_name is rejected."""
        template = _full_template()
        del template["template_name"]

        with pytest.raises(SystemExit):
            validate_template(template)


class TestMissingKeysInteractive:
    """Missing keys trigger interactive prompts."""

    def test_single_missing_key_filled_by_prompt(self):
        """A single missing key is filled via interactive prompt."""
        template = _full_template()
        del template["containerEnv"]["DEVELOPER_NAME"]

        mock_question = MagicMock()
        mock_question.ask.return_value = "Jane Developer"
        with patch("questionary.text", return_value=mock_question):
            result = validate_template(template)

        assert result["containerEnv"]["DEVELOPER_NAME"] == "Jane Developer"

    def test_git_token_not_required_for_ssh(self):
        """When auth is SSH, missing GIT_TOKEN does not trigger a prompt."""
        template = _full_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "ssh"
        del template["containerEnv"]["GIT_TOKEN"]

        # No prompts should fire — all other keys present
        result = validate_template(template)
        assert "GIT_TOKEN" not in result["containerEnv"]


class TestInvalidValuesInteractive:
    """Invalid values trigger interactive correction prompts."""

    def test_invalid_pager_corrected(self):
        """Invalid PAGER value is corrected via select prompt."""
        template = _full_template()
        template["containerEnv"]["PAGER"] = "nano"

        mock_question = MagicMock()
        mock_question.ask.return_value = "less"
        with patch("questionary.select", return_value=mock_question):
            result = validate_template(template)

        assert result["containerEnv"]["PAGER"] == "less"

    def test_invalid_git_provider_url_corrected(self):
        """GIT_PROVIDER_URL with protocol is corrected via text prompt."""
        template = _full_template()
        template["containerEnv"]["GIT_PROVIDER_URL"] = "https://github.com"

        mock_question = MagicMock()
        mock_question.ask.return_value = "github.com"
        with patch("questionary.text", return_value=mock_question):
            result = validate_template(template)

        assert result["containerEnv"]["GIT_PROVIDER_URL"] == "github.com"

    def test_invalid_proxy_url_corrected_when_proxy_enabled(self):
        """Invalid HOST_PROXY_URL is corrected when proxy is enabled."""
        template = _full_template()
        template["containerEnv"]["HOST_PROXY"] = "true"
        template["containerEnv"]["HOST_PROXY_URL"] = "proxy.local"

        mock_question = MagicMock()
        mock_question.ask.return_value = "https://proxy.local:3128"
        with patch("questionary.text", return_value=mock_question):
            result = validate_template(template)

        assert result["containerEnv"]["HOST_PROXY_URL"] == "https://proxy.local:3128"


class TestAuthConsistencyEndToEnd:
    """Auth method consistency is enforced end-to-end."""

    def test_ssh_method_removes_leftover_git_token(self):
        """SSH auth method removes a leftover GIT_TOKEN."""
        template = _full_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "ssh"
        # GIT_TOKEN still present from before switching
        template["containerEnv"]["GIT_TOKEN"] = "old-token"

        result = validate_template(template)

        assert "GIT_TOKEN" not in result["containerEnv"]
        assert result["containerEnv"]["GIT_AUTH_METHOD"] == "ssh"

    def test_token_method_removes_ssh_private_key(self):
        """Token auth method removes ssh_private_key."""
        template = _full_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "token"
        template["ssh_private_key"] = "/path/to/key"

        result = validate_template(template)

        assert "ssh_private_key" not in result
        assert result["containerEnv"]["GIT_TOKEN"] == "ghp_functional_test_token"

    def test_empty_git_token_prompts_for_value(self):
        """Empty GIT_TOKEN with token auth prompts the user."""
        template = _full_template()
        template["containerEnv"]["GIT_TOKEN"] = ""

        mock_question = MagicMock()
        mock_question.ask.return_value = "new-token-value"
        with patch("questionary.text", return_value=mock_question):
            result = validate_template(template)

        assert result["containerEnv"]["GIT_TOKEN"] == "new-token-value"


class TestImmutability:
    """validate_template does not modify the original template."""

    def test_original_not_mutated(self):
        """The original template dict is not modified."""
        import copy

        template = _full_template()
        original = copy.deepcopy(template)

        validate_template(template)

        assert template == original

    def test_original_not_mutated_with_corrections(self):
        """Even when corrections are made, original is not mutated."""
        import copy

        template = _full_template()
        template["containerEnv"]["GIT_AUTH_METHOD"] = "ssh"
        template["containerEnv"]["GIT_TOKEN"] = "leftover"
        original = copy.deepcopy(template)

        result = validate_template(template)

        assert template == original
        assert "GIT_TOKEN" not in result["containerEnv"]
        assert "GIT_TOKEN" in template["containerEnv"]
