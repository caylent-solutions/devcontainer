"""Functional tests for file system utilities (write_json_file, constants)."""

import json
import os

from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ENTRY_FILENAME,
    ENV_VARS_FILENAME,
    SHELL_ENV_FILENAME,
    SSH_KEY_FILENAME,
)
from caylent_devcontainer_cli.utils.fs import write_json_file


class TestWriteJsonFileEndToEnd:
    """Functional tests for write_json_file end-to-end behavior."""

    def test_write_and_read_back_template_data(self, tmp_path):
        """Test writing template data and reading it back produces identical results."""
        template_data = {
            "containerEnv": {
                "AWS_CONFIG_ENABLED": "true",
                "AWS_DEFAULT_OUTPUT": "json",
                "CICD": "false",
                "DEFAULT_GIT_BRANCH": "main",
                "DEVELOPER_NAME": "Test User",
                "GIT_PROVIDER_URL": "github.com",
                "GIT_TOKEN": "test-token",
                "GIT_USER": "testuser",
                "GIT_USER_EMAIL": "test@example.com",
            },
            "aws_profile_map": {
                "default": {
                    "region": "us-west-2",
                    "sso_start_url": "https://example.awsapps.com/start",
                    "sso_region": "us-west-2",
                    "account_name": "dev-account",
                    "account_id": "123456789012",
                    "role_name": "DeveloperAccess",
                }
            },
            "cli_version": "2.0.0",
        }

        file_path = str(tmp_path / "template.json")
        write_json_file(file_path, template_data)

        with open(file_path, "r") as f:
            loaded_data = json.load(f)

        assert loaded_data == template_data

    def test_written_file_has_correct_format(self, tmp_path):
        """Test that the written file has indent=2 and trailing newline."""
        data = {"key": "value"}
        file_path = str(tmp_path / "formatted.json")

        write_json_file(file_path, data)

        with open(file_path, "r") as f:
            raw_content = f.read()

        # Verify indent=2 formatting
        assert raw_content == '{\n  "key": "value"\n}\n'

    def test_write_env_vars_file(self, tmp_path):
        """Test writing a devcontainer-environment-variables.json file."""
        env_data = {
            "containerEnv": {
                "AWS_CONFIG_ENABLED": "true",
                "DEVELOPER_NAME": "Developer",
            },
            "cli_version": "2.0.0",
        }

        file_path = str(tmp_path / ENV_VARS_FILENAME)
        write_json_file(file_path, env_data)

        assert os.path.exists(file_path)
        with open(file_path, "r") as f:
            loaded = json.load(f)
        assert loaded["containerEnv"]["DEVELOPER_NAME"] == "Developer"


class TestFilePathConstantsIntegration:
    """Functional tests verifying constants are used correctly across the codebase."""

    def test_constants_match_expected_filenames(self):
        """Test that all constants have the expected values."""
        assert ENV_VARS_FILENAME == "devcontainer-environment-variables.json"
        assert SHELL_ENV_FILENAME == "shell.env"
        assert CATALOG_ENTRY_FILENAME == "catalog-entry.json"
        assert SSH_KEY_FILENAME == "ssh-private-key"

    def test_constants_are_strings(self):
        """Test that all constants are string types."""
        for const in [
            ENV_VARS_FILENAME,
            SHELL_ENV_FILENAME,
            CATALOG_ENTRY_FILENAME,
            SSH_KEY_FILENAME,
        ]:
            assert isinstance(const, str)

    def test_constants_are_filenames_not_paths(self):
        """Test that constants are bare filenames, not full paths."""
        for const in [
            ENV_VARS_FILENAME,
            SHELL_ENV_FILENAME,
            CATALOG_ENTRY_FILENAME,
            SSH_KEY_FILENAME,
        ]:
            assert os.sep not in const
            assert "/" not in const
