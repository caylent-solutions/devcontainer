"""Unit tests for the shared validation module (S1.3.3)."""

import json
import os
import tempfile
from unittest.mock import patch

from caylent_devcontainer_cli.utils.validation import (
    ValidationResult,
    _read_shell_env,
    _step2_locate_template,
    detect_validation_issues,
    parse_shell_env,
)

# =============================================================================
# parse_shell_env tests
# =============================================================================


class TestParseShellEnv:
    """Tests for parsing shell.env content."""

    def test_extracts_export_keys(self):
        """Test that exported variable names are extracted."""
        content = "export AWS_CONFIG_ENABLED='true'\n" "export DEVELOPER_NAME='tester'\n" "export GIT_USER='myuser'\n"
        result = parse_shell_env(content)
        assert "AWS_CONFIG_ENABLED" in result.keys
        assert "DEVELOPER_NAME" in result.keys
        assert "GIT_USER" in result.keys

    def test_extracts_metadata_template_name(self):
        """Test that template name is extracted from comment header."""
        content = "# Template: my-template\n# CLI Version: 2.0.0\nexport FOO='bar'\n"
        result = parse_shell_env(content)
        assert result.template_name == "my-template"

    def test_extracts_metadata_cli_version(self):
        """Test that CLI version is extracted from comment header."""
        content = "# Template: test\n# CLI Version: 2.0.0\nexport FOO='bar'\n"
        result = parse_shell_env(content)
        assert result.cli_version == "2.0.0"

    def test_extracts_metadata_template_path(self):
        """Test that template path is extracted from comment header."""
        content = "# Template Path: /home/user/.devcontainer-templates/test.json\nexport FOO='bar'\n"
        result = parse_shell_env(content)
        assert result.template_path == "/home/user/.devcontainer-templates/test.json"

    def test_missing_metadata_returns_none(self):
        """Test that missing metadata fields return None."""
        content = "export FOO='bar'\n"
        result = parse_shell_env(content)
        assert result.template_name is None
        assert result.template_path is None
        assert result.cli_version is None

    def test_ignores_non_export_lines(self):
        """Test that non-export lines are ignored for key extraction."""
        content = (
            "# comment\n" "unset GIT_EDITOR\n" "export REAL_KEY='value'\n" 'export PATH="$HOME/.asdf/shims:$PATH"\n'
        )
        result = parse_shell_env(content)
        assert "REAL_KEY" in result.keys
        assert "PATH" in result.keys

    def test_handles_empty_content(self):
        """Test that empty content returns empty result."""
        result = parse_shell_env("")
        assert result.keys == set()
        assert result.template_name is None


# =============================================================================
# ValidationResult tests
# =============================================================================


class TestValidationResult:
    """Tests for the ValidationResult dataclass."""

    def test_has_issues_when_base_keys_missing(self):
        """Test has_issues is True when base keys are missing."""
        result = ValidationResult(
            missing_base_keys={"FOO": "bar"},
            metadata_present=True,
            template_name="test",
            template_path="/path",
            cli_version="2.0.0",
            template_found=True,
            validated_template=None,
            missing_template_keys={},
        )
        assert result.has_issues is True

    def test_has_issues_when_metadata_missing(self):
        """Test has_issues is True when metadata is missing."""
        result = ValidationResult(
            missing_base_keys={},
            metadata_present=False,
            template_name=None,
            template_path=None,
            cli_version=None,
            template_found=False,
            validated_template=None,
            missing_template_keys={},
        )
        assert result.has_issues is True

    def test_has_issues_when_template_not_found(self):
        """Test has_issues is True when template is not found."""
        result = ValidationResult(
            missing_base_keys={},
            metadata_present=True,
            template_name="test",
            template_path="/path",
            cli_version="2.0.0",
            template_found=False,
            validated_template=None,
            missing_template_keys={},
        )
        assert result.has_issues is True

    def test_has_issues_when_template_keys_missing(self):
        """Test has_issues is True when template keys are missing."""
        result = ValidationResult(
            missing_base_keys={},
            metadata_present=True,
            template_name="test",
            template_path="/path",
            cli_version="2.0.0",
            template_found=True,
            validated_template=None,
            missing_template_keys={"EXTRA_KEY": "value"},
        )
        assert result.has_issues is True

    def test_no_issues_when_everything_valid(self):
        """Test has_issues is False when all checks pass."""
        result = ValidationResult(
            missing_base_keys={},
            metadata_present=True,
            template_name="test",
            template_path="/path",
            cli_version="2.0.0",
            template_found=True,
            validated_template=None,
            missing_template_keys={},
        )
        assert result.has_issues is False

    def test_all_missing_keys_combines_stages(self):
        """Test all_missing_keys merges base and template missing keys."""
        result = ValidationResult(
            missing_base_keys={"KEY_A": "default_a"},
            metadata_present=True,
            template_name="test",
            template_path="/path",
            cli_version="2.0.0",
            template_found=True,
            validated_template=None,
            missing_template_keys={"KEY_B": "value_b"},
        )
        combined = result.all_missing_keys
        assert combined == {"KEY_A": "default_a", "KEY_B": "value_b"}


# =============================================================================
# detect_validation_issues — Step 0 tests
# =============================================================================


class TestStep0BaseKeyCheck:
    """Tests for Step 0: base key checking."""

    @patch("caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES", {"KEY_A": "a", "KEY_B": "b"})
    def test_detects_missing_base_keys_in_json(self):
        """Test Step 0 flags base keys missing from JSON containerEnv."""
        config_data = {
            "containerEnv": {"KEY_A": "value_a"},
            "template_name": "test",
            "template_path": "/path/test.json",
            "cli_version": "2.0.0",
        }
        shell_env_content = "export KEY_A='value_a'\nexport KEY_B='value_b'\n"
        template_data = {"containerEnv": {"KEY_A": "value_a"}}

        with (
            patch("caylent_devcontainer_cli.utils.validation._read_shell_env", return_value=shell_env_content),
            patch(
                "caylent_devcontainer_cli.utils.validation._step2_locate_template",
                return_value=(True, template_data),
            ),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert "KEY_B" in result.missing_base_keys

    @patch("caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES", {"KEY_A": "a", "KEY_B": "b"})
    def test_detects_missing_base_keys_in_shell_env(self):
        """Test Step 0 flags base keys missing from shell.env."""
        config_data = {
            "containerEnv": {"KEY_A": "value_a", "KEY_B": "value_b"},
            "template_name": "test",
            "template_path": "/path/test.json",
            "cli_version": "2.0.0",
        }
        shell_env_content = "export KEY_A='value_a'\n"
        template_data = {"containerEnv": {"KEY_A": "value_a", "KEY_B": "value_b"}}

        with (
            patch("caylent_devcontainer_cli.utils.validation._read_shell_env", return_value=shell_env_content),
            patch(
                "caylent_devcontainer_cli.utils.validation._step2_locate_template",
                return_value=(True, template_data),
            ),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert "KEY_B" in result.missing_base_keys

    @patch("caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES", {"KEY_A": "a", "GIT_TOKEN": "tok"})
    def test_git_token_not_required_for_ssh(self):
        """Test Step 0 skips GIT_TOKEN when GIT_AUTH_METHOD is ssh."""
        config_data = {
            "containerEnv": {"KEY_A": "value", "GIT_AUTH_METHOD": "ssh"},
            "template_name": "test",
            "template_path": "/path/test.json",
            "cli_version": "2.0.0",
        }
        shell_env_content = "export KEY_A='value'\nexport GIT_AUTH_METHOD='ssh'\n"
        template_data = {"containerEnv": {"KEY_A": "value", "GIT_AUTH_METHOD": "ssh"}}

        with (
            patch("caylent_devcontainer_cli.utils.validation._read_shell_env", return_value=shell_env_content),
            patch(
                "caylent_devcontainer_cli.utils.validation._step2_locate_template",
                return_value=(True, template_data),
            ),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert "GIT_TOKEN" not in result.missing_base_keys

    @patch(
        "caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES",
        {"KEY_A": "a", "KEY_B": "b"},
    )
    def test_no_missing_keys_when_all_present(self):
        """Test Step 0 returns empty when all base keys present in both files."""
        config_data = {
            "containerEnv": {"KEY_A": "x", "KEY_B": "y"},
            "template_name": "test",
            "template_path": "/path/test.json",
            "cli_version": "2.0.0",
        }
        shell_env_content = "export KEY_A='x'\nexport KEY_B='y'\n"
        template_data = {"containerEnv": {"KEY_A": "x", "KEY_B": "y"}}

        with (
            patch("caylent_devcontainer_cli.utils.validation._read_shell_env", return_value=shell_env_content),
            patch(
                "caylent_devcontainer_cli.utils.validation._step2_locate_template",
                return_value=(True, template_data),
            ),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert result.missing_base_keys == {}


# =============================================================================
# detect_validation_issues — Step 1 tests
# =============================================================================


class TestStep1MetadataValidation:
    """Tests for Step 1: metadata validation."""

    def test_metadata_present_when_all_fields_exist(self):
        """Test metadata_present is True when all required fields exist."""
        config_data = {
            "containerEnv": {},
            "template_name": "test",
            "template_path": "/path/test.json",
            "cli_version": "2.0.0",
        }

        with (
            patch("caylent_devcontainer_cli.utils.validation._read_shell_env", return_value=""),
            patch(
                "caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES",
                {},
            ),
            patch(
                "caylent_devcontainer_cli.utils.validation._step2_locate_template",
                return_value=(True, {"containerEnv": {}}),
            ),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert result.metadata_present is True

    def test_metadata_missing_when_template_name_absent(self):
        """Test metadata_present is False when template_name is missing."""
        config_data = {
            "containerEnv": {},
            "template_path": "/path/test.json",
            "cli_version": "2.0.0",
        }

        with (
            patch("caylent_devcontainer_cli.utils.validation._read_shell_env", return_value=""),
            patch("caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES", {}),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert result.metadata_present is False

    def test_metadata_missing_when_cli_version_absent(self):
        """Test metadata_present is False when cli_version is missing."""
        config_data = {
            "containerEnv": {},
            "template_name": "test",
            "template_path": "/path/test.json",
        }

        with (
            patch("caylent_devcontainer_cli.utils.validation._read_shell_env", return_value=""),
            patch("caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES", {}),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert result.metadata_present is False

    def test_skips_steps_2_3_when_metadata_missing(self):
        """Test that Steps 2-3 are skipped when metadata is missing."""
        config_data = {"containerEnv": {}}

        with (
            patch("caylent_devcontainer_cli.utils.validation._read_shell_env", return_value=""),
            patch("caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES", {}),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert result.metadata_present is False
        assert result.template_found is False
        assert result.validated_template is None
        assert result.missing_template_keys == {}


# =============================================================================
# detect_validation_issues — Step 2 tests
# =============================================================================


class TestStep2LocateTemplate:
    """Tests for Step 2: template location and validation."""

    def test_template_found_when_file_exists(self):
        """Test template_found is True when template file exists."""
        config_data = {
            "containerEnv": {"KEY": "val"},
            "template_name": "my-template",
            "template_path": "/home/user/.devcontainer-templates/my-template.json",
            "cli_version": "2.0.0",
        }
        template_data = {
            "containerEnv": {"KEY": "val"},
            "template_name": "my-template",
            "template_path": "/home/user/.devcontainer-templates/my-template.json",
            "cli_version": "2.0.0",
        }

        with (
            patch("caylent_devcontainer_cli.utils.validation._read_shell_env", return_value="export KEY='val'\n"),
            patch("caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES", {}),
            patch(
                "caylent_devcontainer_cli.utils.validation._step2_locate_template",
                return_value=(True, template_data),
            ),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert result.template_found is True

    def test_template_not_found_when_file_missing(self):
        """Test template_found is False when template file does not exist."""
        config_data = {
            "containerEnv": {},
            "template_name": "nonexistent",
            "template_path": "/path/nonexistent.json",
            "cli_version": "2.0.0",
        }

        with (
            patch("caylent_devcontainer_cli.utils.validation._read_shell_env", return_value=""),
            patch("caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES", {}),
            patch(
                "caylent_devcontainer_cli.utils.validation._step2_locate_template",
                return_value=(False, None),
            ),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert result.template_found is False
        assert result.validated_template is None


# =============================================================================
# detect_validation_issues — Step 3 tests
# =============================================================================


class TestStep3TemplateComparison:
    """Tests for Step 3: template vs project comparison."""

    def test_detects_keys_in_template_not_in_project(self):
        """Test that keys in template but not in project are flagged."""
        config_data = {
            "containerEnv": {"EXISTING": "val"},
            "template_name": "test",
            "template_path": "/path/test.json",
            "cli_version": "2.0.0",
        }
        template_data = {
            "containerEnv": {"EXISTING": "val", "NEW_KEY": "new_value"},
            "template_name": "test",
            "template_path": "/path/test.json",
            "cli_version": "2.0.0",
        }

        with (
            patch(
                "caylent_devcontainer_cli.utils.validation._read_shell_env",
                return_value="export EXISTING='val'\n",
            ),
            patch("caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES", {}),
            patch(
                "caylent_devcontainer_cli.utils.validation._step2_locate_template",
                return_value=(True, template_data),
            ),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert "NEW_KEY" in result.missing_template_keys
        assert result.missing_template_keys["NEW_KEY"] == "new_value"

    def test_no_missing_when_project_matches_template(self):
        """Test no missing keys when project matches template."""
        env = {"KEY_A": "a", "KEY_B": "b"}
        config_data = {
            "containerEnv": env,
            "template_name": "test",
            "template_path": "/path/test.json",
            "cli_version": "2.0.0",
        }
        template_data = {
            "containerEnv": env.copy(),
            "template_name": "test",
            "template_path": "/path/test.json",
            "cli_version": "2.0.0",
        }

        with (
            patch(
                "caylent_devcontainer_cli.utils.validation._read_shell_env",
                return_value="export KEY_A='a'\nexport KEY_B='b'\n",
            ),
            patch("caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES", {}),
            patch(
                "caylent_devcontainer_cli.utils.validation._step2_locate_template",
                return_value=(True, template_data),
            ),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert result.missing_template_keys == {}

    def test_skips_comparison_when_template_not_found(self):
        """Test Step 3 is skipped when template was not found."""
        config_data = {
            "containerEnv": {"KEY": "val"},
            "template_name": "missing",
            "template_path": "/path/missing.json",
            "cli_version": "2.0.0",
        }

        with (
            patch("caylent_devcontainer_cli.utils.validation._read_shell_env", return_value="export KEY='val'\n"),
            patch("caylent_devcontainer_cli.utils.validation.EXAMPLE_ENV_VALUES", {}),
            patch(
                "caylent_devcontainer_cli.utils.validation._step2_locate_template",
                return_value=(False, None),
            ),
        ):
            result = detect_validation_issues("/test/path", config_data)

        assert result.missing_template_keys == {}


# =============================================================================
# _read_shell_env tests (real file I/O)
# =============================================================================


class TestReadShellEnv:
    """Tests for _read_shell_env with real file I/O."""

    def test_reads_existing_shell_env(self):
        """Test that _read_shell_env reads content from an existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            shell_env_path = os.path.join(temp_dir, "shell.env")
            with open(shell_env_path, "w") as f:
                f.write("export FOO='bar'\nexport BAZ='qux'\n")

            content = _read_shell_env(temp_dir)

        assert "export FOO='bar'" in content
        assert "export BAZ='qux'" in content

    def test_returns_empty_when_file_missing(self):
        """Test that _read_shell_env returns empty string when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            content = _read_shell_env(temp_dir)

        assert content == ""


# =============================================================================
# _step2_locate_template tests (real file I/O)
# =============================================================================


class TestStep2LocateTemplateReal:
    """Tests for _step2_locate_template with real file I/O."""

    def test_finds_existing_template(self):
        """Test that _step2_locate_template finds and validates an existing template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = os.path.join(temp_dir, ".devcontainer-templates")
            os.makedirs(templates_dir)
            template_file = os.path.join(templates_dir, "my-template.json")
            template_data = {
                "containerEnv": {"KEY_A": "val"},
                "template_name": "my-template",
                "template_path": template_file,
                "cli_version": "2.0.0",
            }
            with open(template_file, "w") as f:
                json.dump(template_data, f)

            with (
                patch(
                    "caylent_devcontainer_cli.utils.validation.get_template_path",
                    return_value=template_file,
                ),
                patch(
                    "caylent_devcontainer_cli.utils.validation.validate_template",
                    return_value=template_data,
                ),
            ):
                found, data = _step2_locate_template("my-template")

            assert found is True
            assert data is not None
            assert "containerEnv" in data

    def test_returns_false_when_template_missing(self):
        """Test that _step2_locate_template returns False for missing template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = os.path.join(temp_dir, "nonexistent.json")

            with patch(
                "caylent_devcontainer_cli.utils.validation.get_template_path",
                return_value=missing_path,
            ):
                found, data = _step2_locate_template("nonexistent")

            assert found is False
            assert data is None
