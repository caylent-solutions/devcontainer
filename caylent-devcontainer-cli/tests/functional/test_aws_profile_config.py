#!/usr/bin/env python3
"""Functional tests for AWS profile configuration features."""

import json
from unittest.mock import patch


def test_parse_standard_profile_functional():
    """Test parsing standard AWS profile format in functional context."""
    from caylent_devcontainer_cli.commands.setup_interactive import parse_standard_profile

    profile_text = """
[default]
sso_start_url = https://example.awsapps.com/start
sso_region = us-west-2
sso_account_name = example-dev-account
sso_account_id = 123456789012
sso_role_name = DeveloperAccess
region = us-west-2
extra_field = ignored
"""

    result = parse_standard_profile(profile_text)

    # Should parse required fields
    assert result["sso_start_url"] == "https://example.awsapps.com/start"
    assert result["sso_region"] == "us-west-2"
    assert result["sso_account_name"] == "example-dev-account"
    assert result["sso_account_id"] == "123456789012"
    assert result["sso_role_name"] == "DeveloperAccess"
    assert result["region"] == "us-west-2"

    # Should include extra fields (they get ignored during validation)
    assert result["extra_field"] == "ignored"


def test_validate_standard_profile_functional():
    """Test validation of standard AWS profiles in functional context."""
    from caylent_devcontainer_cli.commands.setup_interactive import validate_standard_profile

    # Valid profile
    valid_profile = {
        "sso_start_url": "https://example.awsapps.com/start",
        "sso_region": "us-west-2",
        "sso_account_name": "example-dev-account",
        "sso_account_id": "123456789012",
        "sso_role_name": "DeveloperAccess",
        "region": "us-west-2",
    }
    assert validate_standard_profile(valid_profile) is None

    # Missing fields
    incomplete_profile = {"sso_start_url": "https://example.awsapps.com/start", "sso_region": "us-west-2"}
    error = validate_standard_profile(incomplete_profile)
    assert "Missing required fields" in error
    assert "sso_account_name" in error

    # Empty fields
    empty_profile = valid_profile.copy()
    empty_profile["region"] = ""
    error = validate_standard_profile(empty_profile)
    assert "Empty values for required fields" in error
    assert "region" in error


def test_convert_standard_to_json_functional():
    """Test conversion from standard format to JSON format."""
    from caylent_devcontainer_cli.commands.setup_interactive import convert_standard_to_json

    profiles = {
        "default": {
            "sso_start_url": "https://example.awsapps.com/start",
            "sso_region": "us-west-2",
            "sso_account_name": "example-dev-account",
            "sso_account_id": "123456789012",
            "sso_role_name": "DeveloperAccess",
            "region": "us-west-2",
        },
        "prod": {
            "sso_start_url": "https://example.awsapps.com/start",
            "sso_region": "us-east-1",
            "sso_account_name": "example-prod-account",
            "sso_account_id": "987654321098",
            "sso_role_name": "ReadOnlyAccess",
            "region": "us-east-1",
        },
    }

    result = convert_standard_to_json(profiles)

    # Check default profile
    assert "default" in result
    assert result["default"]["region"] == "us-west-2"
    assert result["default"]["sso_start_url"] == "https://example.awsapps.com/start"
    assert result["default"]["account_name"] == "example-dev-account"
    assert result["default"]["account_id"] == "123456789012"
    assert result["default"]["role_name"] == "DeveloperAccess"

    # Check prod profile
    assert "prod" in result
    assert result["prod"]["region"] == "us-east-1"
    assert result["prod"]["account_name"] == "example-prod-account"


@patch("questionary.confirm")
@patch("questionary.select")
@patch("questionary.text")
def test_aws_profile_map_json_format_functional(mock_text, mock_select, mock_confirm):
    """Test AWS profile map with JSON format option."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_aws_profile_map

    # Mock responses
    mock_confirm.return_value.ask.return_value = True
    mock_select.return_value.ask.return_value = "JSON format (paste complete configuration)"

    json_input = {
        "default": {
            "region": "us-west-2",
            "sso_start_url": "https://example.awsapps.com/start",
            "sso_region": "us-west-2",
            "account_name": "example-dev-account",
            "account_id": "123456789012",
            "role_name": "DeveloperAccess",
        }
    }
    mock_text.return_value.ask.return_value = json.dumps(json_input)

    result = prompt_aws_profile_map()

    assert result == json_input
    mock_confirm.assert_called_once()
    mock_select.assert_called_once()
    mock_text.assert_called_once()


@patch("questionary.confirm")
@patch("questionary.select")
@patch("questionary.text")
def test_aws_profile_map_standard_format_functional(mock_text, mock_select, mock_confirm):
    """Test AWS profile map with standard format option."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_aws_profile_map

    # Mock responses for standard format
    mock_confirm.return_value.ask.side_effect = [True, False]  # Enable AWS, don't add another profile
    mock_select.return_value.ask.return_value = "Standard format (enter profiles one by one)"

    # Mock profile input
    standard_profile = """sso_start_url = https://example.awsapps.com/start
sso_region = us-west-2
sso_account_name = example-dev-account
sso_account_id = 123456789012
sso_role_name = DeveloperAccess
region = us-west-2"""

    mock_text.return_value.ask.side_effect = ["default", standard_profile]

    result = prompt_aws_profile_map()

    # Should convert to JSON format
    assert "default" in result
    assert result["default"]["region"] == "us-west-2"
    assert result["default"]["account_name"] == "example-dev-account"
    assert result["default"]["account_id"] == "123456789012"


@patch("questionary.confirm")
@patch("questionary.select")
@patch("questionary.text")
def test_aws_profile_map_standard_format_validation_retry(mock_text, mock_select, mock_confirm):
    """Test AWS profile map standard format with validation retry."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_aws_profile_map

    # Mock responses
    mock_confirm.return_value.ask.side_effect = [True, False]  # Enable AWS, don't add another profile
    mock_select.return_value.ask.return_value = "Standard format (enter profiles one by one)"

    # First attempt - incomplete profile
    incomplete_profile = """sso_start_url = https://example.awsapps.com/start
sso_region = us-west-2"""

    # Second attempt - complete profile
    complete_profile = """sso_start_url = https://example.awsapps.com/start
sso_region = us-west-2
sso_account_name = example-dev-account
sso_account_id = 123456789012
sso_role_name = DeveloperAccess
region = us-west-2"""

    mock_text.return_value.ask.side_effect = [
        "default",  # profile name
        incomplete_profile,  # first attempt (will fail validation)
        complete_profile,  # second attempt (will pass)
    ]

    result = prompt_aws_profile_map()

    # Should eventually succeed with complete profile
    assert "default" in result
    assert result["default"]["region"] == "us-west-2"
    assert result["default"]["account_name"] == "example-dev-account"


@patch("questionary.confirm")
@patch("questionary.select")
@patch("questionary.text")
def test_aws_profile_map_multiple_profiles_standard_format(mock_text, mock_select, mock_confirm):
    """Test AWS profile map with multiple profiles in standard format."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_aws_profile_map

    # Mock responses - enable AWS, add another profile, then stop
    mock_confirm.return_value.ask.side_effect = [True, True, False]
    mock_select.return_value.ask.return_value = "Standard format (enter profiles one by one)"

    # Profile configurations
    default_profile = """sso_start_url = https://example.awsapps.com/start
sso_region = us-west-2
sso_account_name = example-dev-account
sso_account_id = 123456789012
sso_role_name = DeveloperAccess
region = us-west-2"""

    prod_profile = """sso_start_url = https://example.awsapps.com/start
sso_region = us-east-1
sso_account_name = example-prod-account
sso_account_id = 987654321098
sso_role_name = ReadOnlyAccess
region = us-east-1"""

    mock_text.return_value.ask.side_effect = [
        "default",
        default_profile,  # first profile
        "prod",
        prod_profile,  # second profile
    ]

    result = prompt_aws_profile_map()

    # Should have both profiles
    assert "default" in result
    assert "prod" in result
    assert result["default"]["account_name"] == "example-dev-account"
    assert result["prod"]["account_name"] == "example-prod-account"


@patch("questionary.confirm")
def test_aws_profile_map_disabled_functional(mock_confirm):
    """Test AWS profile map when disabled."""
    from caylent_devcontainer_cli.commands.setup_interactive import prompt_aws_profile_map

    mock_confirm.return_value.ask.return_value = False

    result = prompt_aws_profile_map()

    assert result == {}
    mock_confirm.assert_called_once()


def test_end_to_end_profile_processing():
    """Test end-to-end profile processing from standard format to JSON."""
    from caylent_devcontainer_cli.commands.setup_interactive import (
        convert_standard_to_json,
        parse_standard_profile,
        validate_standard_profile,
    )

    # Simulate user input
    profile_text = """
[default]
sso_start_url = https://example.awsapps.com/start
sso_region = us-west-2
sso_account_name = example-dev-account
sso_account_id = 123456789012
sso_role_name = DeveloperAccess
region = us-west-2
"""

    # Step 1: Parse
    parsed = parse_standard_profile(profile_text)

    # Step 2: Validate
    validation_error = validate_standard_profile(parsed)
    assert validation_error is None

    # Step 3: Convert to JSON format
    profiles = {"default": parsed}
    json_result = convert_standard_to_json(profiles)

    # Verify final result
    expected = {
        "default": {
            "region": "us-west-2",
            "sso_start_url": "https://example.awsapps.com/start",
            "sso_region": "us-west-2",
            "account_name": "example-dev-account",
            "account_id": "123456789012",
            "role_name": "DeveloperAccess",
        }
    }

    assert json_result == expected


def test_profile_parsing_edge_cases():
    """Test profile parsing with various edge cases."""
    from caylent_devcontainer_cli.commands.setup_interactive import parse_standard_profile

    # Test with comments and empty lines
    profile_with_comments = """
# This is a comment
[default]
# Another comment
sso_start_url = https://example.awsapps.com/start

sso_region = us-west-2
sso_account_name = example-dev-account
sso_account_id = 123456789012
sso_role_name = DeveloperAccess
region = us-west-2
# Final comment
"""

    result = parse_standard_profile(profile_with_comments)

    # Should ignore comments and empty lines
    assert len(result) == 6  # Only the actual key-value pairs
    assert result["sso_start_url"] == "https://example.awsapps.com/start"
    assert result["region"] == "us-west-2"


def test_validation_comprehensive():
    """Test comprehensive validation scenarios."""
    from caylent_devcontainer_cli.commands.setup_interactive import validate_standard_profile

    # Test with whitespace-only values
    profile_with_whitespace = {
        "sso_start_url": "https://example.awsapps.com/start",
        "sso_region": "us-west-2",
        "sso_account_name": "example-dev-account",
        "sso_account_id": "123456789012",
        "sso_role_name": "   ",  # whitespace only
        "region": "us-west-2",
    }

    error = validate_standard_profile(profile_with_whitespace)
    assert "Empty values for required fields" in error
    assert "sso_role_name" in error
