"""Unit tests for template upgrade enhancements."""

from unittest.mock import patch

from caylent_devcontainer_cli.utils.env import get_missing_env_vars, is_single_line_env_var


class TestSingleLineEnvVar:
    """Test single line environment variable detection."""

    def test_is_single_line_env_var_string(self):
        """Test single line string detection."""
        assert is_single_line_env_var("simple_string") is True
        assert is_single_line_env_var("value with spaces") is True
        assert is_single_line_env_var("") is True

    def test_is_single_line_env_var_multiline(self):
        """Test multiline string detection."""
        assert is_single_line_env_var("line1\nline2") is False
        assert is_single_line_env_var("line1\n") is False

    def test_is_single_line_env_var_complex_types(self):
        """Test complex type detection."""
        assert is_single_line_env_var({"key": "value"}) is False
        assert is_single_line_env_var(["item1", "item2"]) is False
        assert is_single_line_env_var(123) is False
        assert is_single_line_env_var(True) is False


class TestMissingVarsDetection:
    """Test missing variables detection."""

    @patch(
        "caylent_devcontainer_cli.utils.env.EXAMPLE_ENV_VALUES",
        {"VAR1": "value1", "VAR2": "value2", "VAR3": {"complex": "object"}, "VAR4": "multiline\nvalue"},
    )
    def test_get_missing_env_vars(self):
        """Test getting missing single line variables."""
        container_env = {"VAR1": "existing_value"}

        missing = get_missing_env_vars(container_env)

        # Should only include VAR2 (single line, missing)
        # VAR3 is complex object, VAR4 is multiline
        assert missing == {"VAR2": "value2"}

    @patch("caylent_devcontainer_cli.utils.env.EXAMPLE_ENV_VALUES", {"VAR1": "value1", "VAR2": "value2"})
    def test_get_missing_env_vars_none_missing(self):
        """Test when no variables are missing."""
        container_env = {"VAR1": "existing1", "VAR2": "existing2"}

        missing = get_missing_env_vars(container_env)

        assert missing == {}


class TestCodeCommandMissingVars:
    """Test code command missing variables detection."""

    def test_get_missing_env_vars_from_container_env(self):
        """Test checking for missing environment variables using shared utility."""
        container_env = {"EXISTING_VAR": "value"}

        with patch(
            "caylent_devcontainer_cli.utils.env.EXAMPLE_ENV_VALUES",
            {"EXISTING_VAR": "default1", "MISSING_VAR": "default2", "COMPLEX_VAR": {"key": "value"}},
        ):
            missing = get_missing_env_vars(container_env)

        # Should only detect MISSING_VAR (single line, missing)
        assert missing == {"MISSING_VAR": "default2"}

    # prompt_upgrade_or_continue tests removed — function replaced by
    # _handle_missing_variables() in S1.3.3 validation rewrite
