"""Unit tests for template upgrade enhancements."""

import json
import os
import tempfile
import unittest.mock as mock
from unittest.mock import MagicMock, patch

import pytest

from caylent_devcontainer_cli.commands.template import (
    get_missing_single_line_vars,
    is_single_line_env_var,
    prompt_for_missing_vars,
    upgrade_template_with_missing_vars,
)
from caylent_devcontainer_cli.commands.code import check_missing_env_vars, prompt_upgrade_or_continue


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

    @patch('caylent_devcontainer_cli.commands.template.EXAMPLE_ENV_VALUES', {
        'VAR1': 'value1',
        'VAR2': 'value2',
        'VAR3': {'complex': 'object'},
        'VAR4': 'multiline\nvalue'
    })
    def test_get_missing_single_line_vars(self):
        """Test getting missing single line variables."""
        container_env = {'VAR1': 'existing_value'}
        
        missing = get_missing_single_line_vars(container_env)
        
        # Should only include VAR2 (single line, missing)
        # VAR3 is complex object, VAR4 is multiline
        assert missing == {'VAR2': 'value2'}

    @patch('caylent_devcontainer_cli.commands.template.EXAMPLE_ENV_VALUES', {
        'VAR1': 'value1',
        'VAR2': 'value2'
    })
    def test_get_missing_single_line_vars_none_missing(self):
        """Test when no variables are missing."""
        container_env = {'VAR1': 'existing1', 'VAR2': 'existing2'}
        
        missing = get_missing_single_line_vars(container_env)
        
        assert missing == {}


class TestPromptForMissingVars:
    """Test prompting for missing variables."""

    @patch('questionary.confirm')
    @patch('questionary.text')
    def test_prompt_for_missing_vars_use_defaults(self, mock_text, mock_confirm):
        """Test using default values for missing variables."""
        mock_confirm.return_value.ask.return_value = True
        
        missing_vars = {'VAR1': 'default1', 'VAR2': 'default2'}
        
        result = prompt_for_missing_vars(missing_vars)
        
        assert result == {'VAR1': 'default1', 'VAR2': 'default2'}
        assert mock_confirm.call_count == 2

    @patch('questionary.confirm')
    @patch('questionary.text')
    def test_prompt_for_missing_vars_custom_values(self, mock_text, mock_confirm):
        """Test using custom values for missing variables."""
        mock_confirm.return_value.ask.return_value = False
        mock_text.return_value.ask.side_effect = ['custom1', 'custom2']
        
        missing_vars = {'VAR1': 'default1', 'VAR2': 'default2'}
        
        result = prompt_for_missing_vars(missing_vars)
        
        assert result == {'VAR1': 'custom1', 'VAR2': 'custom2'}
        assert mock_text.call_count == 2


class TestUpgradeTemplateWithMissingVars:
    """Test template upgrade with missing variables."""

    @patch('caylent_devcontainer_cli.commands.setup_interactive.upgrade_template')
    @patch('caylent_devcontainer_cli.commands.template.get_missing_single_line_vars')
    @patch('caylent_devcontainer_cli.commands.template.prompt_for_missing_vars')
    def test_upgrade_template_with_missing_vars(self, mock_prompt, mock_get_missing, mock_upgrade):
        """Test upgrading template with missing variables."""
        from caylent_devcontainer_cli import __version__
        
        # Setup mocks
        mock_upgrade.return_value = {
            'containerEnv': {'existing_var': 'value'},
            'cli_version': __version__,
            'aws_profile_map': {}
        }
        mock_get_missing.return_value = {'NEW_VAR': 'default_value'}
        mock_prompt.return_value = {'NEW_VAR': 'user_value'}
        
        template_data = {'containerEnv': {'existing_var': 'value'}}
        
        result = upgrade_template_with_missing_vars(template_data)
        
        # Check that NEW_VAR was added
        assert 'NEW_VAR' in result['containerEnv']
        assert result['containerEnv']['NEW_VAR'] == 'user_value'
        assert result['containerEnv']['existing_var'] == 'value'
        assert result['cli_version'] == __version__
        
        mock_upgrade.assert_called_once_with(template_data)
        mock_get_missing.assert_called_once()
        mock_prompt.assert_called_once_with({'NEW_VAR': 'default_value'})

    @patch('caylent_devcontainer_cli.commands.setup_interactive.upgrade_template')
    @patch('caylent_devcontainer_cli.commands.template.get_missing_single_line_vars')
    def test_upgrade_template_no_missing_vars(self, mock_get_missing, mock_upgrade):
        """Test upgrading template with no missing variables."""
        from caylent_devcontainer_cli import __version__
        
        mock_upgrade.return_value = {
            'containerEnv': {'existing_var': 'value'},
            'cli_version': __version__,
            'aws_profile_map': {}
        }
        mock_get_missing.return_value = {}
        
        template_data = {'containerEnv': {'existing_var': 'value'}}
        
        result = upgrade_template_with_missing_vars(template_data)
        
        # Check basic structure
        assert result['containerEnv']['existing_var'] == 'value'
        assert result['cli_version'] == __version__


class TestCodeCommandMissingVars:
    """Test code command missing variables detection."""

    def test_check_missing_env_vars(self):
        """Test checking for missing environment variables."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                'containerEnv': {
                    'EXISTING_VAR': 'value'
                }
            }
            json.dump(config_data, f)
            f.flush()
            
            with patch('caylent_devcontainer_cli.commands.code.EXAMPLE_ENV_VALUES', {
                'EXISTING_VAR': 'default1',
                'MISSING_VAR': 'default2',
                'COMPLEX_VAR': {'key': 'value'}
            }):
                missing = check_missing_env_vars(f.name)
                
            os.unlink(f.name)
            
        # Should only detect MISSING_VAR (single line, missing)
        assert missing == ['MISSING_VAR']

    @patch('questionary.select')
    @patch('sys.exit')
    def test_prompt_upgrade_or_continue_exit(self, mock_exit, mock_select):
        """Test prompting user to exit and upgrade."""
        mock_select.return_value.ask.return_value = "Exit and upgrade the profile first (recommended)"
        
        prompt_upgrade_or_continue(['VAR1', 'VAR2'], 'test-template')
        
        mock_exit.assert_called_once_with(0)

    @patch('questionary.select')
    def test_prompt_upgrade_or_continue_continue(self, mock_select):
        """Test prompting user to continue without upgrade."""
        mock_select.return_value.ask.return_value = "Continue without the upgrade (may cause issues)"
        
        # Should not raise any exception
        prompt_upgrade_or_continue(['VAR1', 'VAR2'])
        
        # Verify the select was called
        mock_select.assert_called_once()