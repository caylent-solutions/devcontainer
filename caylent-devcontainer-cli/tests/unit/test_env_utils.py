"""Unit tests for environment variable utilities (utils/env.py)."""

from unittest.mock import patch

from caylent_devcontainer_cli.utils.env import is_single_line_env_var


class TestGetMissingEnvVars:
    """Tests for get_missing_env_vars()."""

    def test_returns_dict_of_missing_single_line_vars(self):
        """Test that missing single-line env vars are returned as dict."""
        from caylent_devcontainer_cli.utils.env import get_missing_env_vars

        container_env = {"EXISTING_KEY": "value"}
        example_values = {
            "EXISTING_KEY": "default1",
            "MISSING_KEY": "default2",
        }

        with patch("caylent_devcontainer_cli.utils.env.EXAMPLE_ENV_VALUES", example_values):
            result = get_missing_env_vars(container_env)

        assert isinstance(result, dict)
        assert "MISSING_KEY" in result
        assert result["MISSING_KEY"] == "default2"
        assert "EXISTING_KEY" not in result

    def test_excludes_non_single_line_vars(self):
        """Test that multi-line/complex vars are excluded."""
        from caylent_devcontainer_cli.utils.env import get_missing_env_vars

        container_env = {}
        example_values = {
            "SIMPLE_VAR": "simple_value",
            "COMPLEX_VAR": {"nested": "object"},
            "MULTILINE_VAR": "line1\nline2",
        }

        with patch("caylent_devcontainer_cli.utils.env.EXAMPLE_ENV_VALUES", example_values):
            result = get_missing_env_vars(container_env)

        assert "SIMPLE_VAR" in result
        assert "COMPLEX_VAR" not in result
        assert "MULTILINE_VAR" not in result

    def test_returns_empty_dict_when_all_present(self):
        """Test returns empty dict when all vars are present."""
        from caylent_devcontainer_cli.utils.env import get_missing_env_vars

        example_values = {"KEY1": "val1", "KEY2": "val2"}
        container_env = {"KEY1": "custom1", "KEY2": "custom2"}

        with patch("caylent_devcontainer_cli.utils.env.EXAMPLE_ENV_VALUES", example_values):
            result = get_missing_env_vars(container_env)

        assert result == {}

    def test_returns_empty_dict_when_no_example_values(self):
        """Test returns empty dict when EXAMPLE_ENV_VALUES is empty."""
        from caylent_devcontainer_cli.utils.env import get_missing_env_vars

        with patch("caylent_devcontainer_cli.utils.env.EXAMPLE_ENV_VALUES", {}):
            result = get_missing_env_vars({"KEY": "value"})

        assert result == {}

    def test_uses_is_single_line_env_var(self):
        """Test that it uses is_single_line_env_var for filtering."""
        from caylent_devcontainer_cli.utils.env import get_missing_env_vars

        example_values = {"VAR1": "value1", "VAR2": [1, 2, 3]}
        container_env = {}

        with patch("caylent_devcontainer_cli.utils.env.EXAMPLE_ENV_VALUES", example_values):
            result = get_missing_env_vars(container_env)

        # Only string values without newlines should be included
        assert "VAR1" in result
        assert "VAR2" not in result


class TestIsSingleLineEnvVar:
    """Tests for existing is_single_line_env_var function."""

    def test_single_line_string_returns_true(self):
        assert is_single_line_env_var("simple_value") is True

    def test_multiline_string_returns_false(self):
        assert is_single_line_env_var("line1\nline2") is False

    def test_dict_returns_false(self):
        assert is_single_line_env_var({"key": "value"}) is False

    def test_list_returns_false(self):
        assert is_single_line_env_var([1, 2, 3]) is False

    def test_empty_string_returns_true(self):
        assert is_single_line_env_var("") is True
