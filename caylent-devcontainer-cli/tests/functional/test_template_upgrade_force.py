"""Functional tests for template upgrade --force feature."""

import json
import os
import tempfile
from unittest.mock import patch

from caylent_devcontainer_cli.commands.template import handle_template_upgrade
from caylent_devcontainer_cli.utils.constants import TEMPLATES_DIR


class TestTemplateUpgradeForce:
    """Test template upgrade with --force flag."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_templates_dir = TEMPLATES_DIR

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch("caylent_devcontainer_cli.utils.constants.TEMPLATES_DIR")
    @patch(
        "caylent_devcontainer_cli.commands.template.EXAMPLE_ENV_VALUES",
        {"EXISTING_VAR": "existing_default", "NEW_VAR": "new_default", "COMPLEX_VAR": {"key": "value"}},
    )
    @patch("questionary.confirm")
    @patch("questionary.text")
    def test_force_upgrade_with_missing_vars(self, mock_text, mock_confirm, mock_templates_dir):
        """Test force upgrade adds missing variables interactively."""
        mock_templates_dir.__str__ = lambda: self.temp_dir
        mock_templates_dir.__fspath__ = lambda: self.temp_dir

        # Create template file missing NEW_VAR
        template_data = {"containerEnv": {"EXISTING_VAR": "existing_value"}, "cli_version": "1.0.0"}

        template_path = os.path.join(self.temp_dir, "test-template.json")
        with open(template_path, "w") as f:
            json.dump(template_data, f, indent=2)

        # Mock user choosing default value
        mock_confirm.return_value.ask.return_value = True

        # Create args object
        class Args:
            name = "test-template"
            force = True
            ref = None

        args = Args()

        # Run the upgrade
        with patch("caylent_devcontainer_cli.commands.template.TEMPLATES_DIR", self.temp_dir):
            handle_template_upgrade(args)

        # Verify the template was updated
        with open(template_path, "r") as f:
            updated_template = json.load(f)

        assert "NEW_VAR" in updated_template["containerEnv"]
        assert updated_template["containerEnv"]["NEW_VAR"] == "new_default"
        assert updated_template["containerEnv"]["EXISTING_VAR"] == "existing_value"
        # COMPLEX_VAR should not be added (not single line)
        assert "COMPLEX_VAR" not in updated_template["containerEnv"]

    @patch("caylent_devcontainer_cli.utils.constants.TEMPLATES_DIR")
    @patch(
        "caylent_devcontainer_cli.commands.template.EXAMPLE_ENV_VALUES",
        {"EXISTING_VAR": "existing_default", "NEW_VAR": "new_default"},
    )
    @patch("questionary.confirm")
    @patch("questionary.text")
    def test_force_upgrade_custom_values(self, mock_text, mock_confirm, mock_templates_dir):
        """Test force upgrade with custom values for missing variables."""
        mock_templates_dir.__str__ = lambda: self.temp_dir
        mock_templates_dir.__fspath__ = lambda: self.temp_dir

        # Create template file
        template_data = {"containerEnv": {"EXISTING_VAR": "existing_value"}, "cli_version": "1.0.0"}

        template_path = os.path.join(self.temp_dir, "test-template.json")
        with open(template_path, "w") as f:
            json.dump(template_data, f, indent=2)

        # Mock user choosing custom value
        mock_confirm.return_value.ask.return_value = False
        mock_text.return_value.ask.return_value = "custom_value"

        # Create args object
        class Args:
            name = "test-template"
            force = True
            ref = None

        args = Args()

        # Run the upgrade
        with patch("caylent_devcontainer_cli.commands.template.TEMPLATES_DIR", self.temp_dir):
            handle_template_upgrade(args)

        # Verify the template was updated with custom value
        with open(template_path, "r") as f:
            updated_template = json.load(f)

        assert updated_template["containerEnv"]["NEW_VAR"] == "custom_value"

    @patch("caylent_devcontainer_cli.utils.constants.TEMPLATES_DIR")
    @patch("caylent_devcontainer_cli.commands.template.EXAMPLE_ENV_VALUES", {"EXISTING_VAR": "existing_default"})
    def test_force_upgrade_no_missing_vars(self, mock_templates_dir):
        """Test force upgrade when no variables are missing."""
        mock_templates_dir.__str__ = lambda: self.temp_dir
        mock_templates_dir.__fspath__ = lambda: self.temp_dir

        # Create template file with all required vars
        template_data = {"containerEnv": {"EXISTING_VAR": "existing_value"}, "cli_version": "1.0.0"}

        template_path = os.path.join(self.temp_dir, "test-template.json")
        with open(template_path, "w") as f:
            json.dump(template_data, f, indent=2)

        # Create args object
        class Args:
            name = "test-template"
            force = True
            ref = None

        args = Args()

        # Run the upgrade
        with patch("caylent_devcontainer_cli.commands.template.TEMPLATES_DIR", self.temp_dir):
            handle_template_upgrade(args)

        # Verify the template was updated (version should be current)
        with open(template_path, "r") as f:
            updated_template = json.load(f)

        from caylent_devcontainer_cli import __version__

        assert updated_template["cli_version"] == __version__

    @patch("caylent_devcontainer_cli.utils.constants.TEMPLATES_DIR")
    def test_normal_upgrade_without_force(self, mock_templates_dir):
        """Test normal upgrade without --force flag."""
        mock_templates_dir.__str__ = lambda: self.temp_dir
        mock_templates_dir.__fspath__ = lambda: self.temp_dir

        # Create template file
        template_data = {"containerEnv": {"EXISTING_VAR": "existing_value"}, "cli_version": "1.0.0"}

        template_path = os.path.join(self.temp_dir, "test-template.json")
        with open(template_path, "w") as f:
            json.dump(template_data, f, indent=2)

        # Create args object without force
        class Args:
            name = "test-template"
            force = False
            ref = None

        args = Args()

        # Run the upgrade
        with patch("caylent_devcontainer_cli.commands.template.TEMPLATES_DIR", self.temp_dir):
            handle_template_upgrade(args)

        # Verify the template was updated but no new vars added
        with open(template_path, "r") as f:
            updated_template = json.load(f)

        # Should only have the original variable
        assert len(updated_template["containerEnv"]) == 1
        assert "EXISTING_VAR" in updated_template["containerEnv"]
