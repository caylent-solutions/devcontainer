#!/usr/bin/env python3
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path so we can import the CLI module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

from caylent_devcontainer_cli.utils.fs import (
    find_project_root,
    generate_exports,
    load_json_config,
)


def test_generate_exports_with_special_chars():
    """Test generating exports with values containing special characters."""
    env_values = {
        "NORMAL_VALUE": "simple",
        "QUOTED_VALUE": "value with spaces",
        "SPECIAL_CHARS": 'value with $pecial & "chars"',
    }

    exports = generate_exports(env_values)

    assert len(exports) == 3
    assert any("NORMAL_VALUE='simple'" in e for e in exports)
    assert any("QUOTED_VALUE='value with spaces'" in e for e in exports)
    assert any("SPECIAL_CHARS='value with $pecial & \"chars\"'" in e for e in exports)


def test_find_project_root_with_git_dir():
    """Test finding project root with .devcontainer directory."""
    with patch("os.path.isdir", return_value=True):
        result = find_project_root("/test/path/subdir")
        assert result == "/test/path/subdir"


def test_load_json_config_file_not_found():
    """Test loading JSON config when file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError()), patch("caylent_devcontainer_cli.utils.fs.log"), patch(
        "sys.exit", side_effect=SystemExit(1)
    ) as mock_exit:
        with pytest.raises(SystemExit):
            load_json_config("/test/path/nonexistent.json")
        mock_exit.assert_called_once_with(1)
