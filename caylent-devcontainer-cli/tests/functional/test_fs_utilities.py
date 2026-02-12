"""Functional tests for file system utilities (write_json_file, remove_example_files, constants)."""

import json
import os

from caylent_devcontainer_cli.utils.constants import (
    CATALOG_ENTRY_FILENAME,
    ENV_VARS_FILENAME,
    EXAMPLE_AWS_FILE,
    EXAMPLE_ENV_FILE,
    SHELL_ENV_FILENAME,
    SSH_KEY_FILENAME,
)
from caylent_devcontainer_cli.utils.fs import remove_example_files, write_json_file


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
                "DEFAULT_PYTHON_VERSION": "3.12.9",
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


class TestRemoveExampleFilesEndToEnd:
    """Functional tests for remove_example_files end-to-end behavior."""

    def test_removes_example_files_from_devcontainer_dir(self, tmp_path):
        """Test full workflow: create .devcontainer with example files, remove them."""
        devcontainer_dir = tmp_path / ".devcontainer"
        devcontainer_dir.mkdir()

        # Create the example files
        (devcontainer_dir / EXAMPLE_ENV_FILE).write_text('{"containerEnv": {}}')
        (devcontainer_dir / EXAMPLE_AWS_FILE).write_text('{"default": {}}')

        # Create other files that should NOT be removed
        devcontainer_json = devcontainer_dir / "devcontainer.json"
        devcontainer_json.write_text('{"name": "test"}')

        aws_map = devcontainer_dir / "aws-profile-map.json"
        aws_map.write_text('{"default": {}}')

        remove_example_files(str(devcontainer_dir))

        # Example files should be gone
        assert not (devcontainer_dir / EXAMPLE_ENV_FILE).exists()
        assert not (devcontainer_dir / EXAMPLE_AWS_FILE).exists()

        # Other files should remain
        assert devcontainer_json.exists()
        assert aws_map.exists()

    def test_safe_on_empty_directory(self, tmp_path):
        """Test that remove_example_files works on a directory with no example files."""
        devcontainer_dir = tmp_path / ".devcontainer"
        devcontainer_dir.mkdir()

        # Should not raise
        remove_example_files(str(devcontainer_dir))


class TestFilePathConstantsIntegration:
    """Functional tests verifying constants are used correctly across the codebase."""

    def test_constants_match_expected_filenames(self):
        """Test that all constants have the expected values."""
        assert ENV_VARS_FILENAME == "devcontainer-environment-variables.json"
        assert SHELL_ENV_FILENAME == "shell.env"
        assert EXAMPLE_ENV_FILE == "example-container-env-values.json"
        assert EXAMPLE_AWS_FILE == "example-aws-profile-map.json"
        assert CATALOG_ENTRY_FILENAME == "catalog-entry.json"
        assert SSH_KEY_FILENAME == "ssh-private-key"

    def test_constants_are_strings(self):
        """Test that all constants are string types."""
        for const in [
            ENV_VARS_FILENAME,
            SHELL_ENV_FILENAME,
            EXAMPLE_ENV_FILE,
            EXAMPLE_AWS_FILE,
            CATALOG_ENTRY_FILENAME,
            SSH_KEY_FILENAME,
        ]:
            assert isinstance(const, str)

    def test_constants_are_filenames_not_paths(self):
        """Test that constants are bare filenames, not full paths."""
        for const in [
            ENV_VARS_FILENAME,
            SHELL_ENV_FILENAME,
            EXAMPLE_ENV_FILE,
            EXAMPLE_AWS_FILE,
            CATALOG_ENTRY_FILENAME,
            SSH_KEY_FILENAME,
        ]:
            assert os.sep not in const
            assert "/" not in const
