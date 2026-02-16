"""Functional tests for template utility functions (S1.1.2)."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from caylent_devcontainer_cli.utils.constants import TEMPLATES_DIR
from caylent_devcontainer_cli.utils.fs import resolve_project_root
from caylent_devcontainer_cli.utils.template import (
    ensure_templates_dir,
    get_template_names,
    get_template_path,
    validate_template,
)


class TestGetTemplatePathEndToEnd:
    """Functional tests for get_template_path."""

    def test_path_matches_templates_dir(self):
        """Test that get_template_path returns path under TEMPLATES_DIR."""
        result = get_template_path("my-template")
        assert result == os.path.join(TEMPLATES_DIR, "my-template.json")

    def test_path_has_json_extension(self):
        """Test that result always has .json extension."""
        result = get_template_path("test")
        assert result.endswith(".json")


class TestGetTemplateNamesEndToEnd:
    """Functional tests for get_template_names."""

    def test_returns_names_from_real_directory(self):
        """Test scanning a real directory with template files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some template files
            for name in ["alpha", "beta", "gamma"]:
                filepath = os.path.join(tmpdir, f"{name}.json")
                with open(filepath, "w") as f:
                    json.dump({"cli_version": "2.0.0"}, f)

            # Also create a non-json file that should be ignored
            with open(os.path.join(tmpdir, "readme.txt"), "w") as f:
                f.write("not a template")

            with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", tmpdir):
                names = get_template_names()

            assert names == ["alpha", "beta", "gamma"]

    def test_returns_empty_for_nonexistent_dir(self):
        """Test returns empty list for non-existent directory."""
        with patch(
            "caylent_devcontainer_cli.utils.template.TEMPLATES_DIR",
            "/nonexistent/path",
        ):
            names = get_template_names()
            assert names == []


class TestEnsureTemplatesDirEndToEnd:
    """Functional tests for ensure_templates_dir."""

    def test_creates_directory_if_missing(self):
        """Test that ensure_templates_dir creates the directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "templates")
            assert not os.path.exists(new_dir)

            with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", new_dir):
                ensure_templates_dir()

            assert os.path.isdir(new_dir)

    def test_no_error_if_directory_exists(self):
        """Test that ensure_templates_dir does not fail if dir already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("caylent_devcontainer_cli.utils.template.TEMPLATES_DIR", tmpdir):
                ensure_templates_dir()  # should not raise


class TestValidateTemplateEndToEnd:
    """Functional tests for validate_template."""

    def test_valid_template_passes_validation(self):
        """Test that a fully valid template passes all validation phases."""
        data = {
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
            "aws_profile_map": {},
        }
        result = validate_template(data)
        assert result["containerEnv"]["AWS_CONFIG_ENABLED"] == "true"
        assert result["aws_profile_map"] == {}


class TestResolveProjectRootEndToEnd:
    """Functional tests for resolve_project_root."""

    def test_resolves_valid_project_root(self):
        """Test resolving a valid project root with .devcontainer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".devcontainer"))
            result = resolve_project_root(tmpdir)
            assert result == tmpdir

    def test_defaults_to_cwd(self):
        """Test that None defaults to current working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".devcontainer"))
            with patch("os.getcwd", return_value=tmpdir):
                result = resolve_project_root()
                assert result == tmpdir

    def test_fails_without_devcontainer(self):
        """Test that it fails when .devcontainer/ doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SystemExit):
                resolve_project_root(tmpdir)


class TestCLINameIntegration:
    """Functional tests for CLI_NAME constant consolidation."""

    def test_cli_name_from_constants(self):
        """Test that CLI_NAME comes from utils/constants.py."""
        from caylent_devcontainer_cli.utils.constants import CLI_NAME

        assert CLI_NAME == "Caylent Devcontainer CLI"

    def test_cli_module_uses_same_constant(self):
        """Test that cli.py uses the same CLI_NAME from constants."""
        import caylent_devcontainer_cli.cli as cli_module
        from caylent_devcontainer_cli.utils.constants import CLI_NAME

        # After refactoring, cli.py imports CLI_NAME from constants
        # The module should not define its own CLI_NAME
        assert cli_module.CLI_NAME == CLI_NAME
