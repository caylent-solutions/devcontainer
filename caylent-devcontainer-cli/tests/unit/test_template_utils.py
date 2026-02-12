"""Unit tests for template utility functions (utils/template.py)."""

import os
from unittest.mock import patch

import pytest

from caylent_devcontainer_cli.utils.constants import TEMPLATES_DIR


class TestGetTemplatePath:
    """Tests for get_template_path()."""

    def test_returns_correct_path_for_template_name(self):
        """Test that get_template_path returns TEMPLATES_DIR/name.json."""
        from caylent_devcontainer_cli.utils.template import get_template_path

        result = get_template_path("my-template")
        expected = os.path.join(TEMPLATES_DIR, "my-template.json")
        assert result == expected

    def test_handles_name_with_special_chars(self):
        """Test template name with hyphens and underscores."""
        from caylent_devcontainer_cli.utils.template import get_template_path

        result = get_template_path("my_project-v2")
        expected = os.path.join(TEMPLATES_DIR, "my_project-v2.json")
        assert result == expected

    def test_uses_templates_dir_constant(self):
        """Test that get_template_path uses TEMPLATES_DIR from constants."""
        from caylent_devcontainer_cli.utils.template import get_template_path

        result = get_template_path("test")
        assert result.startswith(TEMPLATES_DIR)
        assert result.endswith(".json")


class TestGetTemplateNames:
    """Tests for get_template_names()."""

    def test_returns_empty_list_when_dir_not_exists(self):
        """Test returns empty list when TEMPLATES_DIR doesn't exist."""
        from caylent_devcontainer_cli.utils.template import get_template_names

        with patch("os.path.exists", return_value=False):
            result = get_template_names()
            assert result == []

    def test_returns_template_names_without_extension(self):
        """Test returns template names stripped of .json extension."""
        from caylent_devcontainer_cli.utils.template import get_template_names

        with (
            patch("os.path.exists", return_value=True),
            patch(
                "os.listdir",
                return_value=["template1.json", "template2.json", "readme.txt"],
            ),
        ):
            result = get_template_names()
            assert "template1" in result
            assert "template2" in result
            assert "readme" not in result
            assert "readme.txt" not in result

    def test_returns_empty_list_when_no_json_files(self):
        """Test returns empty list when no .json files in dir."""
        from caylent_devcontainer_cli.utils.template import get_template_names

        with (
            patch("os.path.exists", return_value=True),
            patch("os.listdir", return_value=["readme.txt", "config.yaml"]),
        ):
            result = get_template_names()
            assert result == []

    def test_returns_sorted_names(self):
        """Test that returned names are sorted alphabetically."""
        from caylent_devcontainer_cli.utils.template import get_template_names

        with (
            patch("os.path.exists", return_value=True),
            patch(
                "os.listdir",
                return_value=["zebra.json", "alpha.json", "mid.json"],
            ),
        ):
            result = get_template_names()
            assert result == sorted(result)


class TestEnsureTemplatesDir:
    """Tests for ensure_templates_dir()."""

    def test_creates_directory_with_exist_ok(self):
        """Test that ensure_templates_dir calls makedirs with exist_ok=True."""
        from caylent_devcontainer_cli.utils.template import ensure_templates_dir

        with patch("os.makedirs") as mock_makedirs:
            ensure_templates_dir()
            mock_makedirs.assert_called_once_with(TEMPLATES_DIR, exist_ok=True)

    def test_uses_templates_dir_constant(self):
        """Test that ensure_templates_dir uses the TEMPLATES_DIR constant."""
        from caylent_devcontainer_cli.utils.template import ensure_templates_dir

        with patch("os.makedirs") as mock_makedirs:
            ensure_templates_dir()
            call_args = mock_makedirs.call_args[0][0]
            assert call_args == TEMPLATES_DIR


class TestValidateTemplate:
    """Tests for validate_template()."""

    def test_valid_template_returns_data_with_all_keys(self):
        """Test that validate_template returns data for a fully valid template."""
        from caylent_devcontainer_cli.utils.template import validate_template

        data = {
            "containerEnv": {
                "AWS_CONFIG_ENABLED": "true",
                "AWS_DEFAULT_OUTPUT": "json",
                "DEFAULT_GIT_BRANCH": "main",
                "DEFAULT_PYTHON_VERSION": "3.12.9",
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
        result = validate_template(data)
        assert result["containerEnv"]["AWS_CONFIG_ENABLED"] == "true"
        assert result["cli_version"] == "2.0.0"

    def test_rejects_empty_dict(self):
        """Test validate_template rejects empty dict (missing required keys)."""
        from caylent_devcontainer_cli.utils.template import validate_template

        with pytest.raises(SystemExit):
            validate_template({})
